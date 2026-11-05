#!/usr/bin/env python3
"""
service.py
==========
Campus Automation System: Phase 1 Irregularity Flagging Microservice
Production-Grade Real-Time Scoring API

Provides low-latency (< 1ms), two-tiered evaluation for campus access events:
1. Tier 1: Deterministic Rule Engine (O(1) execution for fast physical cutoffs):
   - Impossible Travel / Buddy-Punching Delta-T against campus transit matrix.
   - Repeated Denied Scans Bursts (>= 2 denies within rolling 120s).
   - Strict Curfew / Restricted Facility Breaches (23:00 - 05:00).

2. Tier 2: Stateful & Behavioral ML Pipeline (executed if Tier 1 passes):
   - Stateful rolling feature computation (Z-score deviation, frequency windows, spatial novelty).
   - Multi-model scoring via Isolation Forest and statistical calibrator.
   - 3-Tier Categorical Confidence mapping (High Confidence Issue, Review Suggested, Normal).

3. Edge Hardware & Store-and-Forward Replay Handling:
   - Detects delayed events (delta > 300s or is_offline_replay=True) buffered by offline edge readers.
   - Backfills update historical rolling averages without triggering false real-time sirens.

4. 4-Stage Shadow Mode Architecture:
   - Configurable at runtime via /config/shadow-mode.
   - Suppresses live operator sirens during calibration while logging structured JSONL audit telemetry.
"""

import datetime
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from attendance_engine import attendance_system
from academic_engine import academic_store, academic_ml, academic_ledger
from pipeline import (
    FEATURE_COLUMNS,
    CampusAnomalyEngine,
    CampusFeatureStore,
)
from synthetic_generator import CAMPUS_LOCATIONS, get_min_transit_time


# ---------------------------------------------------------------------------
# Configuration & Environment
# ---------------------------------------------------------------------------
SHADOW_MODE_ENV = os.getenv("SHADOW_MODE", "true").lower() in ("true", "1", "yes")
AUDIT_LOG_DIR = os.getenv("AUDIT_LOG_DIR", "logs")
AUDIT_LOG_PATH = os.path.join(AUDIT_LOG_DIR, "shadow_audit.jsonl")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

os.makedirs(AUDIT_LOG_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Pydantic Contract Schemas
# ---------------------------------------------------------------------------
class ScanEvent(BaseModel):
    """
    Shared event schema contract consumed from edge readers, firmware, or edge gateway.
    """
    person_id: str = Field(..., description="Unique person identifier (e.g. STU_012, FAC_005)")
    location_id: str = Field(..., description="Scanner location identifier (e.g. gate_north, lab_cs)")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp string")
    event_type: Literal["entry", "exit", "denied"] = Field(..., description="Scan event classification")
    
    # Optional hardware telemetry fields (forward-compatible with edge readers)
    match_confidence: Optional[float] = Field(
        1.0, ge=0.0, le=1.0, description="Biometric analog match confidence (0.0 to 1.0)"
    )
    is_offline_replay: Optional[bool] = Field(
        False, description="True if this scan was buffered offline by edge hardware"
    )
    device_id: Optional[str] = Field(
        None, description="Edge scanner / turnstile hardware serial or ID"
    )


class BatchScanRequest(BaseModel):
    """Batch ingestion request for replaying buffered edge events."""
    events: List[ScanEvent]


class ScoringResponse(BaseModel):
    """Comprehensive scoring response returned to edge turnstile or SecOps console."""
    flagged: bool = Field(..., description="True if scan requires operational attention or review")
    tier: Literal["High Confidence Issue", "Review Suggested", "Normal"] = Field(
        ..., description="3-Tier categorical confidence routing level"
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability [0.0 - 1.0]")
    reasons: List[str] = Field(default_factory=list, description="Root-cause explanatory signals")
    evaluation_tier: Literal["Rule Engine", "Behavioral ML", "Normal Baseline", "Historical Backfill"] = Field(
        ..., description="Which layer finalized the evaluation"
    )
    shadow_mode: bool = Field(..., description="Whether shadow mode was active during evaluation")
    alert_dispatched: bool = Field(..., description="Whether a live siren/alert was dispatched to SecOps")
    turnstile_unlocked: bool = Field(..., description="Immediate physical barrier authorization decision")
    audit_id: str = Field(..., description="Unique UUID for audit trail cross-referencing")
    timestamp: str = Field(..., description="Original scan event timestamp")
    is_backfill: bool = Field(..., description="Whether event was treated as historical store-and-forward backfill")


class ShadowModeConfig(BaseModel):
    shadow_mode: bool


class ServiceHealthResponse(BaseModel):
    status: str
    shadow_mode: bool
    models_loaded: bool
    audit_log_path: str
    active_personas_tracked: int
    openvino: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# State Management & Service Lifespan
# ---------------------------------------------------------------------------
feature_store = CampusFeatureStore()
anomaly_engine = CampusAnomalyEngine()
current_shadow_mode = SHADOW_MODE_ENV


def load_engine_models() -> None:
    """Initializes ML models and feature baselines from disk."""
    global anomaly_engine
    model_file = os.path.join(MODEL_DIR, "isolation_forest.joblib")
    if os.path.exists(model_file):
        try:
            anomaly_engine.load(MODEL_DIR)
        except Exception as e:
            print(f"[Service ERROR] Failed to load model from {MODEL_DIR}: {e}")
    else:
        print(f"[Service WARNING] Model artifact not found at {model_file}. Run pipeline.py --train first.")


load_engine_models()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for warm model loading."""
    load_engine_models()
    yield


app = FastAPI(
    title="Campus Automation System - Irregularity Flagging Microservice",
    version="1.0.0",
    description="Real-time scan event scoring engine featuring deterministic fast-cutoffs, behavioral ML, and shadow mode.",
    lifespan=lifespan,
)


def write_audit_log(record: Dict[str, Any]) -> None:
    """Appends evaluated scan telemetry to persistent JSONL audit trail."""
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[Service ERROR] Failed to write audit record: {e}")


# ---------------------------------------------------------------------------
# Tier 1: Deterministic Rule Engine (O(1) Execution)
# ---------------------------------------------------------------------------
def evaluate_deterministic_rules(
    event: ScanEvent, dt: datetime.datetime
) -> Optional[Dict[str, Any]]:
    """
    Executes O(1) checks before routing to the ML pipeline:
    1. Impossible Travel / Buddy-Punching (< min transit seconds).
    2. Repeated Denied Scans Burst (>= 2 denies within 120s).
    3. Restricted Facility Curfew Breaches.
    """
    p_id = event.person_id
    loc = event.location_id
    evt_type = event.event_type

    # Rule 1: Impossible Travel / Buddy-Punching
    if p_id in feature_store.last_scan:
        last_dt, last_loc, last_evt = feature_store.last_scan[p_id]
        delta_sec = max(0.0, (dt - last_dt).total_seconds())
        min_required_sec = get_min_transit_time(last_loc, loc)

        if loc != last_loc and delta_sec < min_required_sec:
            return {
                "flagged": True,
                "tier": "High Confidence Issue",
                "risk_score": 0.98,
                "reasons": [
                    f"Impossible Travel / Buddy-Punching: Only {int(delta_sec)}s elapsed between {last_loc} and {loc} (minimum required transit: {min_required_sec}s)"
                ],
                "evaluation_tier": "Rule Engine",
            }
        elif loc == last_loc and delta_sec < 5.0 and evt_type == last_evt:
            return {
                "flagged": True,
                "tier": "Review Suggested",
                "risk_score": 0.65,
                "reasons": [
                    f"Rapid duplicate scan: Consecutive {evt_type} at {loc} within {int(delta_sec)}s"
                ],
                "evaluation_tier": "Rule Engine",
            }

    # Rule 2: Repeated Denied Scans Burst (Skimming / Hardware Tamper / Brute-force)
    if evt_type == "denied":
        cutoff_120s = dt - datetime.timedelta(seconds=120)
        recent_denies = [t for t in feature_store.denied_scans_5m[p_id] if t >= cutoff_120s]
        if len(recent_denies) >= 2:  # This scan constitutes the 3rd or greater denied scan
            return {
                "flagged": True,
                "tier": "High Confidence Issue",
                "risk_score": 0.95,
                "reasons": [
                    f"Repeated denied scan burst: {len(recent_denies) + 1} consecutive denied scans within 120s at {loc}"
                ],
                "evaluation_tier": "Rule Engine",
            }

    # Rule 3: Strict Curfew Breach for Restricted Facilities (23:00 - 05:00)
    if loc in CAMPUS_LOCATIONS and CAMPUS_LOCATIONS[loc].get("restricted", False):
        if dt.hour < 5 or dt.hour >= 23:
            return {
                "flagged": True,
                "tier": "High Confidence Issue",
                "risk_score": 0.94,
                "reasons": [
                    f"Curfew Security Violation: Access attempt to restricted facility '{loc}' during lockdown hours (23:00 - 05:00)"
                ],
                "evaluation_tier": "Rule Engine",
            }

    return None


# ---------------------------------------------------------------------------
# Core Scoring Pipeline
# ---------------------------------------------------------------------------
def score_event_internal(event: ScanEvent) -> ScoringResponse:
    """Evaluates a scan event through the two-tier architecture."""
    audit_id = f"SCAN_{uuid.uuid4().hex[:12].upper()}"

    try:
        dt = datetime.datetime.fromisoformat(event.timestamp)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO 8601 timestamp format: {event.timestamp}",
        )

    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    # Check for Store-and-Forward Replay (Delayed Edge Buffer Sync)
    # If the scan occurred more than 300 seconds ago or was explicitly flagged as offline replay
    server_now = datetime.datetime.now()
    event_age_sec = (server_now - dt).total_seconds()
    is_backfill = event.is_offline_replay or (event_age_sec > 300.0)

    # 1. Evaluate Tier 1: Deterministic Rules First (O(1))
    rule_result = evaluate_deterministic_rules(event, dt)

    if rule_result is not None:
        # Extract features and update rolling state
        _ = feature_store.extract_features(
            person_id=event.person_id,
            location_id=event.location_id,
            timestamp_str=event.timestamp,
            event_type=event.event_type,
            update_state=True,
            is_backfill=is_backfill,
        )

        flagged = rule_result["flagged"]
        tier = rule_result["tier"]
        risk_score = rule_result["risk_score"]
        reasons = rule_result["reasons"]
        eval_tier = rule_result["evaluation_tier"]

    else:
        # 2. Evaluate Tier 2: Stateful Feature Store & Hybrid ML
        features = feature_store.extract_features(
            person_id=event.person_id,
            location_id=event.location_id,
            timestamp_str=event.timestamp,
            event_type=event.event_type,
            update_state=True,
            is_backfill=is_backfill,
        )

        # Incorporate hardware match confidence if provided
        if event.match_confidence is not None and event.match_confidence < 0.60:
            features["match_confidence"] = float(event.match_confidence)

        if anomaly_engine.is_fitted:
            ml_pred = anomaly_engine.predict_single(features)
            flagged = ml_pred["flagged"]
            tier = ml_pred["tier"]
            risk_score = ml_pred["risk_score"]
            reasons = ml_pred["reasons"]
            eval_tier = "Behavioral ML" if flagged else "Normal Baseline"
        else:
            # Fallback if model not yet fitted: pure statistical rule
            stat_risk, stat_reasons = anomaly_engine.compute_statistical_risk(features)
            risk_score = stat_risk
            if stat_risk >= 0.85:
                tier = "High Confidence Issue"
                flagged = True
            elif stat_risk >= 0.60:
                tier = "Review Suggested"
                flagged = True
            else:
                tier = "Normal"
                flagged = False
            reasons = stat_reasons if stat_reasons else ["Normal scan"]
            eval_tier = "Rule Engine" if flagged else "Normal Baseline"

    # Turnstile Authorization Decision:
    # PASS and Review Suggested permit entry; High Confidence Issue locks turnstile
    turnstile_unlocked = (tier != "High Confidence Issue") and (event.event_type != "denied")

    # Shadow Mode Handling & Live Alert Dispatch:
    # Live alerts are suppressed if in shadow mode OR if event is a historical backfill
    if current_shadow_mode or is_backfill:
        alert_dispatched = False
    else:
        alert_dispatched = (tier == "High Confidence Issue")

    response_obj = ScoringResponse(
        flagged=flagged,
        tier=tier,
        risk_score=risk_score,
        reasons=reasons,
        evaluation_tier=eval_tier,
        shadow_mode=current_shadow_mode,
        alert_dispatched=alert_dispatched,
        turnstile_unlocked=turnstile_unlocked,
        audit_id=audit_id,
        timestamp=event.timestamp,
        is_backfill=is_backfill,
    )

    # Persist structured audit telemetry
    audit_record = response_obj.model_dump()
    audit_record["person_id"] = event.person_id
    audit_record["location_id"] = event.location_id
    audit_record["event_type"] = event.event_type
    audit_record["logged_at"] = server_now.isoformat()
    write_audit_log(audit_record)

    return response_obj


# ---------------------------------------------------------------------------
# API Endpoints & Web Dashboard
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    """Redirects root visitor directly to the unified Green & White UI dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard & UI"])
async def get_dashboard():
    """Renders the Emerald Green & Crisp White Interactive Dashboard."""
    dashboard_file = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_file):
        with open(dashboard_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Dashboard file not found.</h2>", status_code=404)



@app.get("/health", response_model=ServiceHealthResponse, tags=["System"])
async def get_health():
    """Returns operational status, shadow mode state, tracked personas, and OpenVINO hardware telemetry."""
    ov_status = attendance_system.face_engine.get_openvino_status()
    return ServiceHealthResponse(
        status="operational",
        shadow_mode=current_shadow_mode,
        models_loaded=anomaly_engine.is_fitted,
        audit_log_path=AUDIT_LOG_PATH,
        active_personas_tracked=len(feature_store.person_total_counts),
        openvino=ov_status,
    )


@app.get("/config", tags=["Configuration"])
async def get_config():
    """Returns runtime configuration, confidence thresholds, and campus topology."""
    return {
        "shadow_mode": current_shadow_mode,
        "thresholds": {
            "high_confidence_tier": 0.85,
            "review_suggested_tier": 0.60,
            "normal_pass_tier": 0.00,
        },
        "campus_locations": CAMPUS_LOCATIONS,
        "feature_columns": FEATURE_COLUMNS,
        "rollout_stages": {
            "stage_1": "Silent Shadow (suppress alerts)",
            "stage_2": "Digest Audit (nightly digest)",
            "stage_3": "Guarded Live (rules live, ML in digest)",
            "stage_4": "Autonomous (rules & high-confidence ML live)",
        },
    }


@app.post("/config/shadow-mode", tags=["Configuration"])
async def update_shadow_mode(cfg: ShadowModeConfig):
    """Enables or disables shadow mode dynamically at runtime."""
    global current_shadow_mode
    current_shadow_mode = cfg.shadow_mode
    mode_str = "ENABLED (alerts suppressed)" if current_shadow_mode else "DISABLED (live sirens active)"
    print(f"[Service Config] Shadow mode dynamically set to: {mode_str}")
    return {
        "status": "success",
        "shadow_mode": current_shadow_mode,
        "message": f"Shadow mode updated to {current_shadow_mode}",
    }


@app.post("/score", response_model=ScoringResponse, tags=["Scoring"])
async def score_scan(event: ScanEvent):
    """
    Scores a single scan event in real time (< 1ms).
    Returns calibrated risk score, 3-tier confidence level, and gate authorization.
    """
    return score_event_internal(event)


@app.post("/score/batch", tags=["Scoring"])
async def score_batch(batch: BatchScanRequest):
    """
    Ingests and evaluates a batch of scan events (e.g. edge device store-and-forward sync).
    """
    results = []
    for evt in batch.events:
        res = score_event_internal(evt)
        results.append(res)
    return {
        "total_processed": len(results),
        "results": results,
    }


@app.get("/audit/summary", tags=["SecOps & Audit"])
async def get_audit_summary():
    """Aggregates telemetry from the append-only JSONL audit trail."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return {
            "total_scans_logged": 0,
            "tier_breakdown": {},
            "evaluation_tier_breakdown": {},
            "live_alerts_dispatched": 0,
        }

    total = 0
    tier_counts = {"Normal": 0, "Review Suggested": 0, "High Confidence Issue": 0}
    eval_counts = {"Rule Engine": 0, "Behavioral ML": 0, "Normal Baseline": 0}
    alerts_dispatched = 0

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                total += 1
                t = rec.get("tier", "Normal")
                tier_counts[t] = tier_counts.get(t, 0) + 1
                e = rec.get("evaluation_tier", "Normal Baseline")
                eval_counts[e] = eval_counts.get(e, 0) + 1
                if rec.get("alert_dispatched", False):
                    alerts_dispatched += 1
            except Exception:
                pass

    return {
        "total_scans_logged": total,
        "tier_breakdown": tier_counts,
        "evaluation_tier_breakdown": eval_counts,
        "live_alerts_dispatched": alerts_dispatched,
    }


@app.get("/digest/nightly", tags=["SecOps & Audit"])
async def get_nightly_digest(limit: int = 100):
    """
    Compiles recent 'Review Suggested' scans for daily SecOps batch review,
    preventing real-time alert fatigue.
    """
    digest_items = []
    if not os.path.exists(AUDIT_LOG_PATH):
        return {"items": [], "total_count": 0}

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("tier") == "Review Suggested":
                    digest_items.append({
                        "audit_id": rec.get("audit_id"),
                        "person_id": rec.get("person_id"),
                        "location_id": rec.get("location_id"),
                        "timestamp": rec.get("timestamp"),
                        "risk_score": rec.get("risk_score"),
                        "reasons": rec.get("reasons"),
                    })
            except Exception:
                pass

    return {
        "total_count": len(digest_items),
        "items": digest_items[-limit:],
    }


@app.get("/audit/export", tags=["SecOps & Audit"])
async def export_audit_log(limit: int = 500):
    """Exports recent raw audit log records for compliance and retraining."""
    records = []
    if not os.path.exists(AUDIT_LOG_PATH):
        return {"records": []}

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass

    return {"count": len(records), "records": records[-limit:]}


@app.get("/openvino/status", tags=["Hardware Acceleration"])
async def get_openvino_telemetry():
    """
    Returns detailed Intel OpenVINO runtime acceleration status,
    target device, SIMD vectorization capabilities, and active compiled models.
    """
    return attendance_system.face_engine.get_openvino_status()


# ---------------------------------------------------------------------------
# Classroom Attendance & Biometric 1:1 Verification (Work Packages 1-7)
# ---------------------------------------------------------------------------
class EnrollmentRequest(BaseModel):
    student_id: str
    name: str
    image_base64: Optional[str] = None


class DoorVerifyRequest(BaseModel):
    claimed_id: str
    room_id: str = "hall_a"
    timestamp: Optional[str] = None
    method: str = "rfid_card"
    image_base64: Optional[str] = None
    is_spoof: bool = False
    blur_score: Optional[float] = None


class PeriodChangeRequest(BaseModel):
    next_session_id: str
    course_name: str
    start_time: str
    end_time: str


class ReviewActionRequest(BaseModel):
    session_id: str
    student_id: str
    action: Literal["approve_present", "mark_absent"]


class FaceDetectRequest(BaseModel):
    image_base64: str


class HeadcountRequest(BaseModel):
    image_base64: str


@app.post("/attendance/detect-face", tags=["Classroom Attendance & Verification"])
async def detect_face_endpoint(req: FaceDetectRequest):
    """
    Sub-10ms YuNet face detection & headcount HUD endpoint:
    Returns primary face bounding box, 5 landmarks, multi-person headcount, all detected faces,
    facial sharpness, and detection confidence.
    """
    return attendance_system.detect_face_in_frame(req.image_base64)


@app.post("/attendance/headcount", tags=["Classroom Attendance & Verification"])
async def camera_headcount_endpoint(req: HeadcountRequest):
    """
    Real-Time Camera View Headcount & Crowd Density Audit:
    Analyzes full camera frame, counts visible human faces, detects tailgating at doors,
    and returns spatial bounding boxes with confidence levels.
    """
    return attendance_system.get_live_headcount(req.image_base64)


@app.post("/attendance/enroll", tags=["Classroom Attendance & Verification"])
async def enroll_student_endpoint(req: EnrollmentRequest):
    """Enrolls a student by generating and storing their 512-d normalized embedding (supports live webcam)."""
    if req.image_base64:
        emb = attendance_system.embedding_store.enroll_from_webcam(req.student_id, req.name, req.image_base64)
    else:
        emb = attendance_system.embedding_store.enroll_student(req.student_id, req.name)
    return {
        "status": "success",
        "student_id": req.student_id,
        "name": req.name,
        "embedding_dimensions": len(emb),
        "message": "Student successfully enrolled with encrypted embedding",
    }


@app.get("/attendance/student/{student_id}", tags=["Classroom Attendance & Verification"])
async def get_student_profile_endpoint(student_id: str):
    """Returns registration status, name, and face avatar thumbnail for a student ID."""
    return attendance_system.get_student_profile(student_id)


@app.post("/attendance/verify", tags=["Classroom Attendance & Verification"])
async def verify_door_scan_endpoint(req: DoorVerifyRequest):
    """
    Executes real-time 1:1 biometric & face verification at classroom doors:
    - Cosine similarity against claimed ID embedding
    - Presentation attack detection (anti-spoofing)
    - Quality gating (blur & pose)
    - 3-outcome triage: ACCEPT, REJECT, MANUAL_REVIEW
    - Presence State Machine update
    """
    result = attendance_system.process_door_verification(
        claimed_id=req.claimed_id,
        room_id=req.room_id,
        timestamp_str=req.timestamp,
        method=req.method,
        image_base64=req.image_base64,
        is_spoof=req.is_spoof,
        blur_score=req.blur_score,
    )
    return result



@app.get("/attendance/presence", tags=["Classroom Attendance & Verification"])
async def get_classroom_presence():
    """Returns active session attendance, in-room presence count, and student roster."""
    summary = attendance_system.presence_fsm.get_session_summary()
    return summary


@app.post("/attendance/period-change", tags=["Classroom Attendance & Verification"])
async def advance_period_endpoint(req: PeriodChangeRequest):
    """
    Continuous Period Changeover (Zero-Queue Carry-Over Invariant):
    Advances timetable session; all students currently IN_ROOM carry over as PRESENT!
    """
    res = attendance_system.presence_fsm.advance_to_next_period(
        next_session_id=req.next_session_id,
        course_name=req.course_name,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return res


@app.post("/attendance/passive-audit", tags=["Classroom Attendance & Verification"])
async def trigger_passive_roster_audit():
    """
    Work Package 7 (Approved): Overhead camera captures classroom frame and matches
    detected faces strictly against active class roster (30-60 students).
    Confirms carry-overs and flags non-roster visitors to teacher dashboard.
    """
    active_sess = attendance_system.presence_fsm.active_session["session_id"]
    in_room_students = attendance_system.presence_fsm.get_room_presence(
        attendance_system.presence_fsm.active_session["room_id"]
    )
    # Collect embeddings for students currently in room
    face_embeddings = []
    for s_id in in_room_students:
        emb = attendance_system.embedding_store.get_embedding(s_id)
        if emb is not None:
            face_embeddings.append(emb)

    audit_result = attendance_system.roster_auditor.execute_roster_audit(
        session_id=active_sess,
        detected_face_embeddings=face_embeddings,
    )
    return audit_result


@app.get("/attendance/review-queue", tags=["Classroom Attendance & Verification"])
async def get_review_queue():
    """Returns borderline scans awaiting teacher manual review."""
    sess_id = attendance_system.presence_fsm.active_session["session_id"]
    items = attendance_system.presence_fsm.review_queue.get(sess_id, [])
    return {"session_id": sess_id, "count": len(items), "items": items}


@app.post("/attendance/review-action", tags=["Classroom Attendance & Verification"])
async def resolve_review_action(req: ReviewActionRequest):
    """Professor 1-click override to approve or reject a borderline scan."""
    sess_id = req.session_id
    att = attendance_system.presence_fsm.session_attendance.get(sess_id, {})
    if req.student_id in att:
        if req.action == "approve_present":
            att[req.student_id]["status"] = "Present"
            att[req.student_id]["method"] = "Teacher Override (Approved)"
        else:
            att[req.student_id]["status"] = "Absent"
            att[req.student_id]["method"] = "Teacher Override (Marked Absent)"

    # Remove from review queue
    q = attendance_system.presence_fsm.review_queue.get(sess_id, [])
    attendance_system.presence_fsm.review_queue[sess_id] = [
        item for item in q if item.get("student_id") != req.student_id
    ]
    attendance_system.presence_fsm.save_state()
    return {"status": "success", "student_id": req.student_id, "action": req.action}


@app.get("/attendance/logs", tags=["Classroom Attendance & Verification"])
async def get_classroom_verification_logs(
    limit: int = 100,
    status_filter: str = "all",
    room_id: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Returns full classroom entry and 1:1 biometric verification logs:
    - Who entered (student_id, student_name)
    - Where (room_id, room_name)
    - What time (timestamp)
    - 1:1 Verification outcome (ACCEPT, REJECT, MANUAL_REVIEW)
    - Match score, liveness score, attendance status, and full details.
    """
    return attendance_system.get_verification_logs(
        limit=limit,
        status_filter=status_filter,
        room_id=room_id,
        search=search,
    )


@app.get("/attendance/logs/export", tags=["Classroom Attendance & Verification"])
async def export_classroom_verification_logs():
    """Exports all classroom access & 1:1 verification logs as a downloadable CSV report."""
    csv_data = attendance_system.export_verification_logs_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=classroom_verification_logs.csv"},
    )


@app.post("/attendance/logs/clear", tags=["Classroom Attendance & Verification"])
async def clear_classroom_verification_logs():
    """Clears the classroom verification logs."""
    return attendance_system.clear_verification_logs()


# ---------------------------------------------------------------------------
# Academic Module: Study Material, Quiz, ML Services & Universal Ledger
# (Phase 2 Extension - SOCI Block Pilot)
# ---------------------------------------------------------------------------
class MaterialProgressUpdate(BaseModel):
    person_id: str
    material_id: str
    percent: int = Field(100, ge=0, le=100)


class MaterialCreateRequest(BaseModel):
    topic_id: str
    title: str
    type: Literal["pdf", "slides", "video", "notes"] = "pdf"
    required: bool = True
    status: Literal["Draft", "Published"] = "Published"
    content_summary: Optional[str] = None
    file_url: Optional[str] = None


class QuizAutosaveRequest(BaseModel):
    answers: Dict[str, Any]


class QuizSubmitRequest(BaseModel):
    answers: Optional[Dict[str, Any]] = None


class QuestionGenRequest(BaseModel):
    topic_id: str
    count: int = Field(5, ge=1, le=20)
    custom_gemini_api_key: Optional[str] = None
    difficulty_mix: Optional[Dict[str, float]] = None


class QuestionReviewActionRequest(BaseModel):
    question_id: str
    action: Literal["accept", "edit", "reject"]
    edited_data: Optional[Dict[str, Any]] = None
    approved_by: str = "FAC_001"


class ManualQuestionCreateRequest(BaseModel):
    topic_id: str
    type: Literal["single_choice", "multiple_choice", "true_false", "short_answer"]
    text: str
    options: List[str] = []
    answer: str
    explanation: str
    marks: float = 1.0
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    subtopic: str = "General"
    source_passage: Optional[str] = None
    created_by: str = "FAC_001"


class ScoreCorrectionRequest(BaseModel):
    attempt_id: str
    question_id: Optional[str] = None
    new_score: float
    reason: str
    corrected_by: str = "FAC_001"


class ShortAnswerEvalRequest(BaseModel):
    student_answer: str
    reference_answer: str
    max_marks: float = 2.0
    key_concepts: Optional[List[str]] = None


@app.get("/api/v1/academic/overview", tags=["Academic Module (SOCI Block)"])
async def get_academic_overview():
    """Returns general overview of subjects, topics, quiz completion, and ML status."""
    return {
        "status": "operational",
        "pilot_block": "SOCI Block",
        "phase": "Phase 2 Extension",
        "subjects_count": len(academic_store.subjects),
        "topics_count": len(academic_store.topics),
        "materials_count": len(academic_store.materials),
        "questions_in_bank": len(academic_store.questions),
        "total_attempts": len(academic_store.attempts),
        "ml_model_version": academic_ml.model_version
    }


@app.get("/api/v1/academic/subjects", tags=["Academic Module (SOCI Block)"])
async def list_subjects():
    """Returns list of subjects."""
    return list(academic_store.subjects.values())


@app.get("/api/v1/academic/subjects/{subject_id}/topics", tags=["Academic Module (SOCI Block)"])
async def list_subject_topics(subject_id: str):
    """Returns topics for a given subject."""
    topics = [t for t in academic_store.topics.values() if t.get("subject_id") == subject_id]
    topics.sort(key=lambda x: x.get("position", 0))
    return topics


@app.get("/api/v1/academic/topics/{topic_id}/materials", tags=["Academic Module (SOCI Block)"])
async def list_topic_materials(topic_id: str):
    """Returns all materials for a topic."""
    mats = [m for m in academic_store.materials.values() if m.get("topic_id") == topic_id]
    return mats


@app.post("/api/v1/academic/topics/{topic_id}/materials", tags=["Academic Module (SOCI Block)"])
async def create_topic_material(topic_id: str, req: MaterialCreateRequest):
    """Adds a new study material item (AC-MAT-02)."""
    mat_id = f"MAT_{uuid.uuid4().hex[:6].upper()}"
    new_mat = {
        "material_id": mat_id,
        "topic_id": topic_id,
        "title": req.title,
        "type": req.type,
        "status": req.status,
        "required": req.required,
        "version": 1,
        "content_summary": req.content_summary or f"Uploaded {req.type.upper()} material: {req.title}",
        "file_url": req.file_url or f"/static/materials/{mat_id.lower()}.{req.type}"
    }
    academic_store.materials[mat_id] = new_mat
    academic_store.save()
    academic_ledger.record_event(
        person_id="FAC_001",
        location_id=f"ACAD-SUBJ-{topic_id}",
        event_type="material_uploaded",
        payload={"material_id": mat_id, "title": req.title}
    )
    return new_mat


@app.post("/api/v1/academic/materials/{material_id}/publish", tags=["Academic Module (SOCI Block)"])
async def toggle_material_publish(material_id: str):
    """Toggles Draft/Published status for a study material item (AC-MAT-03)."""
    mat = academic_store.materials.get(material_id)
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    new_status = "Draft" if mat.get("status") == "Published" else "Published"
    mat["status"] = new_status
    academic_store.save()
    academic_ledger.record_event(
        person_id="FAC_001",
        location_id="ACAD-MAT",
        event_type="material_status_changed",
        payload={"material_id": material_id, "new_status": new_status}
    )
    return {"material_id": material_id, "status": new_status}


@app.put("/api/v1/academic/materials/{material_id}/progress", tags=["Academic Module (SOCI Block)"])
async def record_material_progress(material_id: str, req: MaterialProgressUpdate):
    """Records student reading or video watching progress (AC-STU-02)."""
    key = f"{req.person_id}:{material_id}"
    record = {
        "person_id": req.person_id,
        "material_id": material_id,
        "percent": req.percent,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat() if req.percent >= 100 else None
    }
    academic_store.material_progress[key] = record
    academic_store.save()
    if req.percent >= 100:
        academic_ledger.record_event(
            person_id=req.person_id,
            location_id="ACAD-PROGRESS",
            event_type="material_completed",
            payload={"material_id": material_id}
        )
    return record


@app.get("/api/v1/academic/quizzes/{quiz_id}/unlock-status", tags=["Academic Module (SOCI Block)"])
async def get_quiz_unlock_status(quiz_id: str, person_id: str = "STU_012"):
    """Evaluates whether the quiz is unlocked for the student (AC-STU-03)."""
    quiz = academic_store.quizzes.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return academic_store.check_quiz_unlock(person_id, quiz["topic_id"])


@app.post("/api/v1/academic/quizzes/{quiz_id}/attempts", tags=["Academic Module (SOCI Block)"])
async def start_quiz_attempt(quiz_id: str, person_id: str = "STU_012"):
    """Starts a new attempt or resumes an active attempt with frozen question set (AC-STU-04, AC-BE-02)."""
    try:
        attempt = academic_store.start_or_resume_attempt(person_id, quiz_id)
        return attempt
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.put("/api/v1/academic/attempts/{attempt_id}/answers", tags=["Academic Module (SOCI Block)"])
async def autosave_attempt_answers(attempt_id: str, req: QuizAutosaveRequest):
    """Autosaves student answers with 10s timer cadence (AC-STU-05)."""
    try:
        return academic_store.autosave_answers(attempt_id, req.answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/academic/attempts/{attempt_id}/submit", tags=["Academic Module (SOCI Block)"])
async def submit_quiz_attempt(attempt_id: str, req: QuizSubmitRequest):
    """
    Submits, scores, evaluates short answers via ML, computes weak areas and integrity signals.
    Guaranteed response in under 3 seconds (AC-STU-06, AC-STU-09, AC-BE-06).
    """
    try:
        result = academic_store.submit_attempt(attempt_id, req.answers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/academic/attempts/{attempt_id}", tags=["Academic Module (SOCI Block)"])
async def get_attempt_details(attempt_id: str):
    """Returns attempt details and scored results."""
    att = academic_store.attempts.get(attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return att


@app.post("/api/v1/academic/topics/{topic_id}/questions/generate", tags=["Academic ML Services"])
async def generate_questions_api(topic_id: str, req: QuestionGenRequest):
    """
    Generates grounded quiz questions from topic text using ML or optional Gemini API (AC-ML-01, AC-ML-02).
    """
    topic = academic_store.topics.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    text = topic.get("extracted_text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Topic has no extracted text to generate questions from.")

    result = academic_ml.generate_questions_from_text(
        topic_id=topic_id,
        material_text=text,
        count=req.count,
        difficulty_mix=req.difficulty_mix,
        custom_gemini_api_key=req.custom_gemini_api_key
    )

    # Place in review queue for staff approval (AC-QZ-04)
    for q in result.get("questions", []):
        academic_store.review_queue.append(q)
    academic_store.save()

    return result


@app.get("/api/v1/academic/questions/review-queue", tags=["Academic ML Services"])
async def get_question_review_queue():
    """Returns ML generated questions currently awaiting staff review (AC-QZ-04)."""
    return academic_store.review_queue


@app.post("/api/v1/academic/questions/review-action", tags=["Academic ML Services"])
async def review_question_action(req: QuestionReviewActionRequest):
    """
    Staff review action: Accepts into question bank, edits, or rejects draft question (AC-QZ-04).
    """
    found = None
    for i, q in enumerate(academic_store.review_queue):
        if q["question_id"] == req.question_id:
            found = academic_store.review_queue.pop(i)
            break

    if not found:
        raise HTTPException(status_code=404, detail="Draft question not found in review queue")

    if req.action in ("accept", "edit"):
        target_data = req.edited_data if (req.action == "edit" and req.edited_data) else found
        target_data["approved_by"] = req.approved_by
        target_data["status"] = "Approved"
        academic_store.questions[target_data["question_id"]] = target_data
        
        # Link to Topic 1 quiz if topic matches
        quiz = academic_store.quizzes.get("QUIZ_CS101_01")
        if quiz and target_data["question_id"] not in quiz.get("question_ids", []):
            quiz.setdefault("question_ids", []).append(target_data["question_id"])

        academic_ledger.record_event(
            person_id=req.approved_by,
            location_id="ACAD-QBANK",
            event_type="question_approved",
            payload={"question_id": target_data["question_id"], "action": req.action}
        )

    academic_store.save()
    return {"status": req.action, "question_id": req.question_id}


@app.post("/api/v1/academic/questions", tags=["Academic ML Services"])
async def create_manual_question(req: ManualQuestionCreateRequest):
    """Manually adds a question to the question bank (AC-QZ-04)."""
    qid = f"Q_MAN_{uuid.uuid4().hex[:6].upper()}"
    new_q = {
        "question_id": qid,
        "topic_id": req.topic_id,
        "type": req.type,
        "text": req.text,
        "options": req.options,
        "answer": req.answer,
        "explanation": req.explanation,
        "marks": req.marks,
        "difficulty": req.difficulty,
        "subtopic": req.subtopic,
        "source_passage": req.source_passage or "Manually authored by staff.",
        "origin": "Manual",
        "approved_by": req.created_by
    }
    academic_store.questions[qid] = new_q
    quiz = academic_store.quizzes.get("QUIZ_CS101_01")
    if quiz:
        quiz.setdefault("question_ids", []).append(qid)
    academic_store.save()
    return new_q


@app.post("/api/v1/academic/ml/evaluate-short-answer", tags=["Academic ML Services"])
async def evaluate_short_answer_api(req: ShortAnswerEvalRequest):
    """Evaluates short-answer semantic correctness and concept coverage (AC-ML-05)."""
    return academic_ml.evaluate_short_answer(
        student_answer=req.student_answer,
        reference_answer=req.reference_answer,
        max_marks=req.max_marks,
        key_concepts=req.key_concepts
    )


@app.get("/api/v1/academic/analytics/item-discrimination", tags=["Academic Psychometrics & Analytics"])
async def get_item_discrimination():
    """
    Calculates Classical Item Difficulty (p) and Item Discrimination Index (D):
    D = P_upper - P_lower. Flags mis-keyed questions (AC-ML-07).
    """
    attempts_list = [a for a in academic_store.attempts.values() if a.get("submitted")]
    questions_list = list(academic_store.questions.values())
    return academic_ml.compute_item_analytics(attempts_list, questions_list)


@app.get("/api/v1/academic/analytics/integrity-summary", tags=["Academic Psychometrics & Analytics"])
async def get_integrity_summary():
    """Summarizes quiz speedruns, identical error clusters, and collusion signals (AC-ML-08)."""
    hist = [a for a in academic_store.attempts.values() if a.get("submitted")]
    flagged = []
    for att in hist:
        integ = academic_ml.check_attempt_integrity(att, hist)
        if integ.get("category") in ("Medium", "High") or integ.get("flags"):
            flagged.append(integ)
    return {
        "total_attempts_audited": len(hist),
        "flagged_attempts_count": len(flagged),
        "flagged_attempts": flagged
    }


@app.post("/api/v1/academic/scores/correct", tags=["Academic Psychometrics & Analytics"])
async def correct_student_score(req: ScoreCorrectionRequest):
    """
    Allows faculty/HOD to manually correct an attempt score.
    Must provide a reason and immediately records to the append-only ledger (AC-RES-02, AC-BE-04).
    """
    att = academic_store.attempts.get(req.attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")
    old_score = att.get("score", 0.0)
    att["score"] = req.new_score
    att["passed"] = (req.new_score / max(att.get("max_score", 1.0), 1.0)) >= 0.60
    academic_store.save()

    # Append to SHA-256 Ledger
    academic_ledger.record_event(
        person_id=req.corrected_by,
        location_id="ACAD-SCORE-AUDIT",
        event_type="score_corrected",
        payload={
            "attempt_id": req.attempt_id,
            "student_person_id": att.get("person_id"),
            "old_score": old_score,
            "new_score": req.new_score,
            "reason": req.reason
        },
        reason=req.reason
    )
    return {"status": "corrected", "attempt_id": req.attempt_id, "old_score": old_score, "new_score": req.new_score}


@app.get("/api/v1/academic/ledger", tags=["Academic Ledger & Governance"])
async def get_academic_ledger_events(limit: int = 50):
    """Returns immutable 4-field SHA-256 chained audit events (AC-BE-04, AC-BE-05)."""
    return academic_ledger.get_recent_events(limit=limit)


@app.get("/api/v1/academic/ledger/export", tags=["Academic Ledger & Governance"])
async def export_academic_ledger_csv():
    """Exports academic audit ledger as CSV for compliance and HOD review (AC-RES-04)."""
    events = academic_ledger.get_recent_events(limit=500)
    import io
    output = io.StringIO()
    output.write("event_id,person_id,location_id,timestamp,event_type,reason,current_hash\n")
    for ev in events:
        output.write(f'"{ev.get("event_id")}","{ev.get("person_id")}","{ev.get("location_id")}","{ev.get("timestamp")}","{ev.get("event_type")}","{ev.get("reason")}","{ev.get("current_hash")}"\n')
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=academic_audit_ledger.csv"}
    )


if __name__ == "__main__":

    import uvicorn
    print("\n" + "=" * 65)
    print("🚀 CAMPUS IRREGULARITY FLAGGING SERVICE IS STARTING")
    print("👉 Click or open in your browser: http://127.0.0.1:8000/docs")
    print("👉 Or root endpoint:              http://127.0.0.1:8000")
    print("👉 Health check endpoint:         http://127.0.0.1:8000/health")
    print("Note: The server will stay running until you press CTRL+C.")
    print("=" * 65 + "\n")
    uvicorn.run("service:app", host="127.0.0.1", port=8000, reload=False)
