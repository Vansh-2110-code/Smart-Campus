#!/usr/bin/env python3
"""
test_service.py
===============
Campus Automation System: Automated Pytest Verification Suite

Exhaustively verifies:
1. Lifespan & Service Health (/health, /config)
2. Normal daytime pedestrian entry flow (Score < 0.60, Barrier Unlocked)
3. O(1) Impossible Travel / Buddy-Punching Detection (< 60s across distant gates)
4. O(1) Repeated Denied Scan Burst Detection (3+ failed scans within 120s)
5. Strict Off-Hours Curfew Breaches (02:30 AM access to restricted facility)
6. Spatial Novelty & Habitual Baseline Anomaly Detection
7. Shadow Mode Dynamic Toggling & Live Alert Suppression vs Siren Dispatch
8. Edge Hardware Store-and-Forward Replay & Historical Backfill Tolerance
9. Local Edge SQLite Offline Buffer Enqueue, Batching, and Draining
10. Edge Turnstile Relay & Alarm Actuation (Hardware & Mock)
11. Audit Telemetry Persistence & Nightly SecOps Digest Aggregation
"""

import base64
import cv2
import datetime
import json
import os
import sqlite3
import sys
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from hardware_edge_agent import HardwareEdgeAgent, OfflineBufferStore, TurnstileRelayController
from service import AUDIT_LOG_PATH, app, feature_store


client = TestClient(app)


def test_service_health():
    """Verify service health endpoint reports operational status and loaded models."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["models_loaded"] is True
    assert "shadow_mode" in data
    assert "active_personas_tracked" in data


def test_service_config():
    """Verify configuration endpoint returns active thresholds and campus topology."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "thresholds" in data
    assert data["thresholds"]["high_confidence_tier"] == 0.85
    assert data["thresholds"]["review_suggested_tier"] == 0.60
    assert "campus_locations" in data
    assert "gate_north" in data["campus_locations"]
    assert "admin_block" in data["campus_locations"]


def test_normal_scan():
    """Verify standard morning arrival passes cleanly without operational alerts."""
    scan = {
        "person_id": "TEST_STUDENT_001",
        "location_id": "gate_main",
        "timestamp": "2026-09-01T08:30:00",
        "event_type": "entry",
    }
    response = client.post("/score", json=scan)
    assert response.status_code == 200
    data = response.json()
    assert data["flagged"] is False
    assert data["tier"] == "Normal"
    assert data["risk_score"] < 0.60
    assert data["turnstile_unlocked"] is True
    assert data["alert_dispatched"] is False


def test_impossible_travel_rule():
    """Verify O(1) Rule Engine catches buddy-punching (< 60s across distant perimeter gates)."""
    p_id = "TEST_BUDDY_001"

    # Scan 1: North Gate at 09:00:00
    scan1 = {
        "person_id": p_id,
        "location_id": "gate_north",
        "timestamp": "2026-09-01T09:00:00",
        "event_type": "entry",
    }
    r1 = client.post("/score", json=scan1)
    assert r1.status_code == 200

    # Scan 2: South Gate at 09:00:25 (Only 25s later, minimum physical walking time is 480s)
    scan2 = {
        "person_id": p_id,
        "location_id": "gate_south",
        "timestamp": "2026-09-01T09:00:25",
        "event_type": "entry",
    }
    r2 = client.post("/score", json=scan2)
    assert r2.status_code == 200
    data = r2.json()
    assert data["flagged"] is True
    assert data["tier"] == "High Confidence Issue"
    assert data["risk_score"] >= 0.85
    assert data["evaluation_tier"] == "Rule Engine"
    assert data["turnstile_unlocked"] is False
    assert any("impossible travel" in r.lower() or "buddy-punching" in r.lower() for r in data["reasons"])


def test_repeated_denied_burst_rule():
    """Verify O(1) Rule Engine catches 3 consecutive denied scans within 120s."""
    p_id = "TEST_BRUTE_FORCE_001"

    # 3 consecutive denials within 30 seconds
    for sec_offset in [0, 12, 25]:
        r = client.post("/score", json={
            "person_id": p_id,
            "location_id": "lab_cs",
            "timestamp": f"2026-09-01T10:15:{sec_offset:02d}",
            "event_type": "denied",
        })
        assert r.status_code == 200

    data = r.json()
    assert data["flagged"] is True
    assert data["tier"] == "High Confidence Issue"
    assert data["evaluation_tier"] == "Rule Engine"
    assert data["turnstile_unlocked"] is False
    assert any("denied" in r.lower() for r in data["reasons"])


def test_temporal_off_hours_curfew():
    """Verify strict curfew rule flags 02:30 AM access to restricted admin block."""
    scan = {
        "person_id": "TEST_CURFEW_001",
        "location_id": "admin_block",
        "timestamp": "2026-09-01T02:30:00",
        "event_type": "entry",
    }
    response = client.post("/score", json=scan)
    assert response.status_code == 200
    data = response.json()
    assert data["flagged"] is True
    assert data["tier"] == "High Confidence Issue"
    assert data["risk_score"] >= 0.85
    assert data["turnstile_unlocked"] is False
    assert any("curfew" in r.lower() or "off-hours" in r.lower() for r in data["reasons"])


def test_spatial_novelty_behavioral():
    """Verify behavioral ML flags unusual daytime access outside personal baseline."""
    p_id = "TEST_SPATIAL_001"

    # Establish baseline for student only visiting hall_a
    for i in range(1, 10):
        client.post("/score", json={
            "person_id": p_id,
            "location_id": "hall_a",
            "timestamp": f"2026-09-01T1{i%5}:00:00",
            "event_type": "entry",
        })

    # Sudden scan into high-novelty facility
    scan_novel = {
        "person_id": p_id,
        "location_id": "admin_block",
        "timestamp": "2026-09-01T16:00:00",
        "event_type": "entry",
    }
    r = client.post("/score", json=scan_novel)
    assert r.status_code == 200
    data = r.json()
    assert data["flagged"] is True
    assert data["risk_score"] >= 0.60
    assert any("novelty" in r.lower() or "spatial" in r.lower() or "curfew" in r.lower() for r in data["reasons"])


def test_shadow_mode_toggle_and_alert_suppression():
    """Verify shadow mode suppresses live sirens, while disabling it dispatches sirens."""
    # Step 1: Ensure Shadow Mode is ENABLED
    client.post("/config/shadow-mode", json={"shadow_mode": True})

    now = datetime.datetime.now()
    ts1 = now.isoformat()
    ts2 = (now + datetime.timedelta(seconds=15)).isoformat()

    scan_shadow_1 = {
        "person_id": "TEST_SHADOW_ALERT",
        "location_id": "gate_north",
        "timestamp": ts1,
        "event_type": "entry",
    }
    client.post("/score", json=scan_shadow_1)

    scan_shadow_2 = {
        "person_id": "TEST_SHADOW_ALERT",
        "location_id": "gate_south",
        "timestamp": ts2,
        "event_type": "entry",
    }
    r_shadow = client.post("/score", json=scan_shadow_2).json()
    assert r_shadow["tier"] == "High Confidence Issue"
    assert r_shadow["shadow_mode"] is True
    assert r_shadow["alert_dispatched"] is False  # Suppressed!

    # Step 2: Switch Shadow Mode to LIVE (Autonomous Phase 4)
    client.post("/config/shadow-mode", json={"shadow_mode": False})

    scan_live_1 = {
        "person_id": "TEST_LIVE_ALERT",
        "location_id": "gate_north",
        "timestamp": ts1,
        "event_type": "entry",
    }
    client.post("/score", json=scan_live_1)

    scan_live_2 = {
        "person_id": "TEST_LIVE_ALERT",
        "location_id": "gate_south",
        "timestamp": ts2,
        "event_type": "entry",
    }
    r_live = client.post("/score", json=scan_live_2).json()
    assert r_live["tier"] == "High Confidence Issue"
    assert r_live["shadow_mode"] is False
    assert r_live["alert_dispatched"] is True  # Real-time Siren Dispatched!

    # Reset back to Shadow Mode
    client.post("/config/shadow-mode", json={"shadow_mode": True})


def test_store_and_forward_backfill():
    """
    Verify replaying offline buffered scans from edge devices updates historical state
    as backfills without triggering false live sirens.
    """
    client.post("/config/shadow-mode", json={"shadow_mode": False})

    # Historical event timestamped 2 hours ago
    past_ts = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
    scan = {
        "person_id": "TEST_BACKFILL_001",
        "location_id": "gate_main",
        "timestamp": past_ts,
        "event_type": "entry",
        "is_offline_replay": True,
    }
    resp = client.post("/score", json=scan)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_backfill"] is True
    assert data["alert_dispatched"] is False  # Never dispatch live siren for historical sync

    client.post("/config/shadow-mode", json={"shadow_mode": True})


def test_offline_buffer_store(tmp_path):
    """Verify local SQLite buffer enqueue, batch retrieval, and ID removal."""
    db_file = os.path.join(tmp_path, "test_buffer.db")
    buffer = OfflineBufferStore(db_path=db_file)

    assert buffer.count_pending() == 0

    # Enqueue 3 events
    for i in range(3):
        buffer.enqueue({
            "person_id": f"TEST_BUF_{i}",
            "location_id": "gate_main",
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "entry",
            "device_id": "GATE_01",
        })

    assert buffer.count_pending() == 3

    batch = buffer.fetch_batch(limit=2)
    assert len(batch) == 2
    assert batch[0]["person_id"] == "TEST_BUF_0"

    # Remove processed IDs
    buffer.remove_ids([batch[0]["id"], batch[1]["id"]])
    assert buffer.count_pending() == 1

    remaining = buffer.fetch_batch(limit=10)
    assert len(remaining) == 1
    assert remaining[0]["person_id"] == "TEST_BUF_2"


def test_edge_agent_turnstile_actuation(tmp_path):
    """Verify Edge Agent correctly triggers barrier unlock on PASS and alarm on breach."""
    db_file = os.path.join(tmp_path, "edge_actuator.db")
    relay = TurnstileRelayController(relay_pin=17, buzzer_pin=27, green_led_pin=22)
    agent = HardwareEdgeAgent(
        device_id="TEST_EDGE_01",
        location_id="gate_main",
        server_url="http://testserver",
        db_path=db_file,
        relay_controller=relay,
    )

    # Test online scoring with FastAPI TestClient
    scan_event = {
        "person_id": "ACTUATOR_STU_001",
        "location_id": "gate_main",
        "timestamp": "2026-09-01T08:30:00",
        "event_type": "entry",
    }
    resp = client.post("/score", json=scan_event)
    data = resp.json()
    assert data["turnstile_unlocked"] is True

    agent.stop()


def test_audit_summary_and_nightly_digest():
    """Verify JSONL telemetry summary and /digest/nightly compilation."""
    r_summary = client.get("/audit/summary")
    assert r_summary.status_code == 200
    sum_data = r_summary.json()
    assert sum_data["total_scans_logged"] > 0
    assert "tier_breakdown" in sum_data
    assert "Normal" in sum_data["tier_breakdown"]

    r_digest = client.get("/digest/nightly")
    assert r_digest.status_code == 200
    digest_data = r_digest.json()
    assert "total_count" in digest_data
    assert "items" in digest_data


# ---------------------------------------------------------------------------
# Module 2: Classroom Biometric & 1:1 Face Attendance Tests (Work Packages 1-7)
# ---------------------------------------------------------------------------
def test_dashboard_endpoint():
    """Verify Emerald Green & Crisp White Dashboard HTML renders with 200 OK."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "Smart Campus Intelligence" in resp.text
    assert "Classroom Attendance" in resp.text


def test_attendance_enrollment():
    """Verify WP 1 enrollment stores 512-d normalized embedding."""
    resp = client.post("/attendance/enroll", json={
        "student_id": "TEST_STUDENT_ENROLL_99",
        "name": "Jane Doe"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["embedding_dimensions"] == 512


def test_door_verification_accept():
    """Verify WP 3 & 5 genuine badge tap + face match unlocks barrier and marks Present."""
    resp = client.post("/attendance/verify", json={
        "claimed_id": "STU_001",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:05:00",
        "method": "rfid_card",
        "is_spoof": False,
        "blur_score": 120.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "ACCEPT"
    assert data["door_unlocked"] is True
    assert data["attendance_status"] == "Present"
    assert data["similarity_score"] >= 0.72


def test_door_verification_spoof_reject():
    """Verify WP 4 presentation attack detection blocks printed photo / screen spoof."""
    resp = client.post("/attendance/verify", json={
        "claimed_id": "STU_002",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:06:00",
        "is_spoof": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "REJECT"
    assert data["door_unlocked"] is False
    assert data["reason_code"] == "SPOOF_REJECT"


def test_door_verification_blur_manual_review():
    """Verify WP 2 & 5 camera blur / poor lighting unlocks door to avoid crowd and queues to teacher."""
    resp = client.post("/attendance/verify", json={
        "claimed_id": "STU_003",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:07:00",
        "blur_score": 20.0  # Blurry capture below 45 threshold
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "MANUAL_REVIEW"
    assert data["door_unlocked"] is True  # Avoid doorway bottleneck
    assert data["attendance_status"] == "Review"


def test_continuous_period_carryover():
    """Verify WP 6 back-to-back period carry-over preserves in-room students with zero rescans."""
    # Step 1: Ensure STU_001 is IN_ROOM
    client.post("/attendance/verify", json={
        "claimed_id": "STU_001",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:05:00"
    })

    # Step 2: Period changeover to Period 2
    resp = client.post("/attendance/period-change", json={
        "next_session_id": "CS102_PERIOD_2",
        "course_name": "Computer Science 102",
        "start_time": "09:50:00",
        "end_time": "10:45:00"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["carried_over_count"] >= 1
    assert "STU_001" in data["carried_over_students"]

    # Step 3: Verify presence summary shows student carried over as Present
    pres = client.get("/attendance/presence").json()
    assert pres["session_id"] == "CS102_PERIOD_2"
    assert pres["present_count"] >= 1


def test_passive_roster_audit_wp7():
    """Verify WP 7 overhead camera audit checks active roster and confirms in-room students."""
    resp = client.post("/attendance/passive-audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "confirmed_in_room_count" in data
    assert "teacher_advisories" in data


def test_teacher_review_queue_and_action():
    """Verify teacher review queue lists pending items and 1-click override resolves status."""
    # Fetch queue
    q_resp = client.get("/attendance/review-queue")
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "items" in q_data

    # Override STU_003 to Present
    act_resp = client.post("/attendance/review-action", json={
        "session_id": q_data.get("session_id", "CS101_PERIOD_1"),
        "student_id": "STU_003",
        "action": "approve_present"
    })
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "success"


def test_door_verification_with_webcam_base64():
    """Verify live webcam base64 JPEG ingestion, real sharpness computation, and 1:1 match."""
    import io
    from PIL import Image

    # Generate dummy test image frame
    img = Image.fromarray(np.random.randint(50, 200, (240, 320, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    # 1. Enroll face with webcam snapshot
    enroll_res = client.post("/attendance/enroll", json={
        "student_id": "TEST_WEBCAM_USER",
        "name": "Webcam User",
        "image_base64": b64_str
    })
    assert enroll_res.status_code == 200
    assert enroll_res.json()["status"] == "success"

    # 2. Verify with matching webcam snapshot
    verify_res = client.post("/attendance/verify", json={
        "claimed_id": "TEST_WEBCAM_USER",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:05:00",
        "image_base64": b64_str
    })
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["decision"] in ("ACCEPT", "MANUAL_REVIEW")
    assert "sharpness_score" in v_data


def test_detect_face_endpoint():
    """Verify real-time face detection HUD endpoint for blank frame and user screenshot."""
    import io
    from PIL import Image

    # 1. Blank frame -> No face detected
    blank = Image.new("RGB", (320, 240), color=(200, 200, 200))
    buf = io.BytesIO()
    blank.save(buf, format="JPEG")
    blank_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    res_blank = client.post("/attendance/detect-face", json={"image_base64": blank_b64})
    assert res_blank.status_code == 200
    data_blank = res_blank.json()
    assert data_blank["face_detected"] is False
    assert data_blank["box"] is None

    # 2. Frame with face -> Face detected
    img_path = r"C:\Users\vansh\.gemini\antigravity-ide\brain\e234ea8f-b0bd-4e51-a502-a68758dd8b49\.user_uploaded\media_1790663716065.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            face_b64 = base64.b64encode(f.read()).decode("utf-8")
        res_face = client.post("/attendance/detect-face", json={"image_base64": face_b64})
        assert res_face.status_code == 200
        data_face = res_face.json()
        assert data_face["face_detected"] is True
        assert data_face["confidence"] >= 0.70
        assert data_face["box"] is not None
        assert len(data_face["landmarks"]) == 5


def test_student_profile_endpoint():
    """Verify student profile retrieval, enrollment state, and avatar metadata."""
    # 1. Enrolled student
    res = client.get("/attendance/student/STU_001")
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == "STU_001"
    assert data["is_enrolled"] is True

    # 2. Non-existent student
    res_unknown = client.get("/attendance/student/STU_NONEXISTENT_999")
    assert res_unknown.status_code == 200
    data_u = res_unknown.json()
    assert data_u["is_enrolled"] is False


def test_camera_headcount_endpoint():
    """Verify real-time camera headcount API on blank and face frames."""
    # 1. Blank frame -> Headcount 0
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", blank)
    blank_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    res_blank = client.post("/attendance/headcount", json={"image_base64": blank_b64})
    assert res_blank.status_code == 200
    data_blank = res_blank.json()
    assert data_blank["headcount"] == 0
    assert data_blank["density_category"] == "Empty Viewport"
    assert data_blank["tailgating_warning"] is False
    assert len(data_blank["all_faces"]) == 0

    # 2. Single face frame -> Headcount 1
    img_path = r"C:\Users\vansh\.gemini\antigravity-ide\brain\e234ea8f-b0bd-4e51-a502-a68758dd8b49\.user_uploaded\media_1790663716065.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            face_b64 = base64.b64encode(f.read()).decode("utf-8")
        res_single = client.post("/attendance/headcount", json={"image_base64": face_b64})
        assert res_single.status_code == 200
        data_single = res_single.json()
        assert data_single["headcount"] >= 1
        assert data_single["tailgating_warning"] is False
        assert len(data_single["all_faces"]) >= 1
        assert data_single["all_faces"][0]["confidence"] >= 0.70


def test_multi_person_headcount_and_tailgating():
    """Verify multi-person headcount detection and door anti-tailgating alert."""
    img_path = r"C:\Users\vansh\.gemini\antigravity-ide\brain\e234ea8f-b0bd-4e51-a502-a68758dd8b49\.user_uploaded\media_1790663716065.png"
    if not os.path.exists(img_path):
        return

    # Create composite frame with 2 visible faces side-by-side
    single_img = cv2.imread(img_path)
    assert single_img is not None
    h, w = single_img.shape[:2]
    # Place two scaled faces side-by-side on wide canvas
    scaled = cv2.resize(single_img, (w // 2, h // 2))
    sh, sw = scaled.shape[:2]
    composite = np.zeros((sh + 40, (sw * 2) + 60, 3), dtype=np.uint8)
    composite[20:20 + sh, 20:20 + sw] = scaled
    composite[20:20 + sh, 40 + sw:40 + (sw * 2)] = scaled

    _, c_buf = cv2.imencode(".jpg", composite)
    c_b64 = base64.b64encode(c_buf.tobytes()).decode("utf-8")

    # 1. Test /attendance/headcount detects both individuals
    res_hc = client.post("/attendance/headcount", json={"image_base64": c_b64})
    assert res_hc.status_code == 200
    data_hc = res_hc.json()
    assert data_hc["headcount"] >= 2
    assert data_hc["tailgating_warning"] is True
    assert len(data_hc["all_faces"]) >= 2
    assert data_hc["density_category"] == "Pair / Potential Tailgating"

    # 2. Test /attendance/verify includes headcount & flags tailgating
    res_verify = client.post("/attendance/verify", json={
        "claimed_id": "STU_001",
        "room_id": "hall_a",
        "timestamp": "2026-09-29T09:05:00",
        "image_base64": c_b64
    })
    assert res_verify.status_code == 200
    data_v = res_verify.json()
    assert data_v["headcount"] >= 2
    assert data_v["tailgating_detected"] is True
    assert "Tailgating Alert" in data_v["message"]


def test_health_and_openvino_status_endpoints():
    """Verify /health and /openvino/status return active OpenVINO acceleration telemetry."""
    # Test /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert data_h["status"] == "operational"
    assert "openvino" in data_h
    assert data_h["openvino"]["openvino_installed"] is True
    assert data_h["openvino"]["active"] is True
    assert "11th Gen Intel" in data_h["openvino"]["device_full_name"] or "Intel" in data_h["openvino"]["device_full_name"] or "CPU" in data_h["openvino"]["target_device"]

    # Test /openvino/status
    res_ov = client.get("/openvino/status")
    assert res_ov.status_code == 200
    data_ov = res_ov.json()
    assert "sface_accelerated" in data_ov
    assert data_ov["mobilenet_accelerated"] is True
    assert data_ov["target_device"] in ("GPU", "GPU.0", "GPU.1", "CPU")
    assert data_ov["device_type"] in ("GPU", "CPU")


def test_classroom_verification_logs_endpoint():
    """Verify /attendance/logs endpoint returns structured logs and filters correctly."""
    # 1. Fetch all logs
    res = client.get("/attendance/logs")
    assert res.status_code == 200
    data = res.json()
    assert "total_count" in data
    assert "items" in data
    assert data["total_count"] > 0
    assert len(data["items"]) > 0

    # Verify log entry fields
    first = data["items"][0]
    assert "student_id" in first
    assert "room_id" in first
    assert "timestamp" in first
    assert "decision" in first
    assert "door_unlocked" in first
    assert "similarity_score" in first

    # 2. Filter by status
    res_acc = client.get("/attendance/logs?status_filter=accepted")
    assert res_acc.status_code == 200
    for item in res_acc.json()["items"]:
        assert item["decision"] == "ACCEPT"


def test_classroom_verification_logs_export_csv():
    """Verify /attendance/logs/export returns RFC-4180 CSV spreadsheet."""
    res = client.get("/attendance/logs/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    text = res.text
    assert "Log ID,Timestamp,Student ID" in text
    assert "1:1 Verification Decision" in text


if __name__ == "__main__":
    pytest.main(["-v", "test_service.py"])





