#!/usr/bin/env python3
"""
manual_test.py
==============
Interactive Manual Testing Utility for Campus Automation Models

Allows you to manually test and inspect:
1. The Hybrid Calibrated Ensemble (Production Engine)
2. Scikit-Learn Isolation Forest (models/isolation_forest.joblib)
3. Next-Gen PU Random Forest (models/next_gen_model.joblib)
4. Deterministic Physics & Curfew Rules (Tier 1 Engine)

Usage:
  - Interactive Menu:
      python manual_test.py
  - Direct Scan Evaluation from CLI:
      python manual_test.py --person STU_001 --location gate_main --time "2026-09-29T08:30:00" --event entry
  - Quick Security Scenarios Suite:
      python manual_test.py --suite
"""

import argparse
import datetime
import json
import os
import sys
from typing import Dict, Any, List

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

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline import CampusAnomalyEngine, CampusFeatureStore, FEATURE_COLUMNS
from synthetic_generator import CAMPUS_LOCATIONS
from attendance_engine import attendance_system




def print_banner():
    print("=" * 72)
    print(" 🏫 CAMPUS AUTOMATION IRREGULARITY FLAGGING - MANUAL MODEL TESTER")
    print("=" * 72)


def format_result(res: Dict[str, Any], features: Dict[str, float]) -> None:
    tier = res["tier"]
    flagged = res["flagged"]
    score = res["risk_score"]
    
    # Color/Symbol coding
    if tier == "High Confidence Issue":
        status_badge = "🔴 [HIGH CONFIDENCE ISSUE - ACCESS DENIED]"
        gate_status = "🔒 TURNSTILE LOCKED | 🚨 LIVE SIREN ACTIVATED"
    elif tier == "Review Suggested":
        status_badge = "🟡 [REVIEW SUGGESTED - BATCH DIGEST]"
        gate_status = "🔓 TURNSTILE UNLOCKED | 📋 ADDED TO NIGHTLY DIGEST"
    else:
        status_badge = "🟢 [NORMAL - PASS]"
        gate_status = "🔓 TURNSTILE UNLOCKED | ✅ SILENT PASS"

    print("\n" + "-" * 72)
    print(f"STATUS:        {status_badge}")
    print(f"GATE ACTION:   {gate_status}")
    print(f"OVERALL RISK:  {score * 100:.1f}% (Tier: {tier})")
    print("-" * 72)
    print("SUB-MODEL SCORES:")
    print(f"  • Isolation Forest Risk:       {res.get('if_risk', 0.0) * 100:.1f}%")
    print(f"  • Next-Gen Random Forest Risk: {res.get('ng_risk', 0.0) * 100:.1f}%")
    print(f"  • Statistical & Physics Risk:  {res.get('stat_risk', 0.0) * 100:.1f}%")
    print("\nREASONS / ROOT-CAUSE SIGNALS:")
    for r in res.get("reasons", []):
        print(f"  ⚠ {r}")
    
    print("\nKEY EXTRACTED FEATURES:")
    key_feats = [
        "arrival_z_score", "hours_from_band", "elapsed_seconds", 
        "is_impossible_transit", "transit_violation_ratio", "spatial_novelty",
        "is_restricted_loc", "denied_count_5m", "is_off_hours", "curfew_violation"
    ]
    for k in key_feats:
        if k in features:
            v = features[k]
            if isinstance(v, float):
                print(f"  - {k:<25}: {v:.2f}")
            else:
                print(f"  - {k:<25}: {v}")
    print("-" * 72)


def evaluate_single_scan(engine: CampusAnomalyEngine, store: CampusFeatureStore,
                         person_id: str, location_id: str, timestamp_str: str,
                         event_type: str = "entry", update_state: bool = True):
    loc_meta = CAMPUS_LOCATIONS.get(location_id, {})
    loc_name = loc_meta.get("name", location_id)
    loc_zone = loc_meta.get("zone", "general")
    print(f"\nEvaluating Scan:")
    print(f"  Person ID:   {person_id}")
    print(f"  Location:    {location_id} ('{loc_name}', Zone: {loc_zone})")
    print(f"  Timestamp:   {timestamp_str}")
    print(f"  Event Type:  {event_type}")

    feats = store.extract_features(
        person_id=person_id,
        location_id=location_id,
        timestamp_str=timestamp_str,
        event_type=event_type,
        update_state=update_state
    )
    result = engine.predict_single(feats)
    format_result(result, feats)
    return result


def run_test_suite(engine: CampusAnomalyEngine):
    """Runs standard security benchmark scenarios."""
    print("\n" + "=" * 72)
    print(" RUNNING PRE-PACKAGED SECURITY BENCHMARK SUITE")
    print("=" * 72)

    scenarios = [
        {
            "name": "Scenario 1: Standard Morning Student Arrival",
            "desc": "Expected daytime arrival at main perimeter gate",
            "steps": [
                ("STU_101", "gate_main", "2026-09-29T08:30:00", "entry")
            ]
        },
        {
            "name": "Scenario 2: Buddy-Punching / Impossible Travel (<20s across distant gates)",
            "desc": "Card scanned at North Gate, then at South Gate 15 seconds later (min walk: 8 mins)",
            "steps": [
                ("STU_BUDDY", "gate_north", "2026-09-29T09:00:00", "entry"),
                ("STU_BUDDY", "gate_south", "2026-09-29T09:00:15", "entry")
            ]
        },
        {
            "name": "Scenario 3: Curfew Security Violation (Restricted Facility Off-Hours)",
            "desc": "Scan into restricted Admin Block at 02:30 AM (Curfew: 23:00 - 05:00)",
            "steps": [
                ("STU_CURFEW", "admin_block", "2026-09-29T02:30:00", "entry")
            ]
        },
        {
            "name": "Scenario 4: Repeated Denied Scans Burst (Brute-force / Skimming)",
            "desc": "3 consecutive denied scans within 30 seconds at Computer Science Lab",
            "steps": [
                ("STU_SKIM", "lab_cs", "2026-09-29T10:15:00", "denied"),
                ("STU_SKIM", "lab_cs", "2026-09-29T10:15:12", "denied"),
                ("STU_SKIM", "lab_cs", "2026-09-29T10:15:25", "denied")
            ]
        },
        {
            "name": "Scenario 5: High Spatial Novelty (Unusual Facility Exploration)",
            "desc": "Student establishes baseline at hall_a, then suddenly accesses restricted admin facility",
            "steps": [
                ("STU_NOVEL", "hall_a", "2026-09-29T10:00:00", "entry"),
                ("STU_NOVEL", "hall_a", "2026-09-29T12:00:00", "entry"),
                ("STU_NOVEL", "hall_a", "2026-09-29T14:00:00", "entry"),
                ("STU_NOVEL", "admin_block", "2026-09-29T16:00:00", "entry")
            ]
        }
    ]

    for sc in scenarios:
        print("\n" + "#" * 72)
        print(f"👉 {sc['name']}")
        print(f"   Description: {sc['desc']}")
        print("#" * 72)
        local_store = CampusFeatureStore()
        for idx, (p, loc, ts, evt) in enumerate(sc["steps"], 1):
            if len(sc["steps"]) > 1:
                print(f"\n[Step {idx}/{len(sc['steps'])}]")
            evaluate_single_scan(engine, local_store, p, loc, ts, evt)


def interactive_menu(engine: CampusAnomalyEngine, store: CampusFeatureStore):
    while True:
        print_banner()
        print("Select a testing option:")
        print("  1. Run Pre-packaged Security Test Suite (All 5 Scenarios)")
        print("  2. Test a Custom Gate Scan (Enter Person, Location, Time)")
        print("  3. Test Buddy-Punching Simulator (Multi-gate instant swipe)")
        print("  4. View Registered Campus Locations")
        print("  5. Test Classroom Door 1:1 Face Verification (Genuine / Spoof / Blur)")
        print("  6. Test Classroom Back-to-Back Period Carry-Over & Passive Audit (WP 7)")
        print("  7. Test Camera View Headcount & Anti-Tailgating Audit")
        print("  8. Exit")
        print("=" * 72)

        choice = input("Enter choice (1-8): ").strip()
        if choice == "1":
            run_test_suite(engine)
        elif choice == "2":
            p_id = input("Enter Person ID [e.g. STU_001]: ").strip() or "STU_001"
            print("Available locations: " + ", ".join(list(CAMPUS_LOCATIONS.keys())))
            loc_id = input("Enter Location ID [default: gate_main]: ").strip() or "gate_main"
            now_iso = datetime.datetime.now().replace(microsecond=0).isoformat()
            ts = input(f"Enter Timestamp ISO [default: {now_iso}]: ").strip() or now_iso
            evt = input("Enter Event Type (entry / exit / denied) [default: entry]: ").strip() or "entry"
            evaluate_single_scan(engine, store, p_id, loc_id, ts, evt)
        elif choice == "3":
            p_id = input("Enter Person ID [e.g. STU_TEST]: ").strip() or "STU_TEST"
            ts1 = datetime.datetime.now().replace(microsecond=0)
            ts2 = ts1 + datetime.timedelta(seconds=15)
            print(f"\nSimulating Scan 1 at North Gate ({ts1.isoformat()})...")
            evaluate_single_scan(engine, store, p_id, "gate_north", ts1.isoformat(), "entry")
            print(f"\nSimulating Scan 2 at South Gate 15s later ({ts2.isoformat()})...")
            evaluate_single_scan(engine, store, p_id, "gate_south", ts2.isoformat(), "entry")
        elif choice == "4":
            print("\nCampus Locations Topology:")
            for loc_id, meta in CAMPUS_LOCATIONS.items():
                res = "[RESTRICTED]" if meta.get("restricted") else "[OPEN]"
                print(f"  • {loc_id:<15} ({meta.get('name', loc_id):<30} | Zone: {meta.get('zone', ''):<10}) -> {res}")
            print()
        elif choice == "5":
            p_id = input("Enter Student ID [default: STU_001]: ").strip() or "STU_001"
            is_spoof_str = input("Simulate Presentation Attack (Printed Photo / Screen)? (y/N): ").strip().lower()
            is_spoof = is_spoof_str == 'y'
            is_blur_str = input("Simulate Camera Blur / Poor Lighting? (y/N): ").strip().lower()
            blur_score = 20.0 if is_blur_str == 'y' else 120.0
            
            print(f"\n[Door Reader] Tapping badge for '{p_id}'...")
            res = attendance_system.process_door_verification(
                claimed_id=p_id,
                room_id="hall_a",
                timestamp_str="2026-09-29T09:05:00",
                method="rfid_card",
                is_spoof=is_spoof,
                blur_score=blur_score
            )
            print("\n" + "-" * 72)
            print(f"DECISION:          {res['decision']}")
            print(f"DOOR SOLENOID:     {'UNLOCKED (3.0s)' if res['door_unlocked'] else 'LOCKED (ALARM DISPATCHED)'}")
            print(f"PERIOD STATUS:     {res['attendance_status']}")
            print(f"HEADCOUNT IN VIEW: {res.get('headcount', 1)}")
            print(f"ANTI-TAILGATING:   {'⚠️ TAILGATING ALERT' if res.get('tailgating_detected') else '✅ Clear (Single Person)'}")
            print(f"SIMILARITY MATCH:  {res['similarity_score'] * 100:.1f}%")
            print(f"LIVENESS SCORE:    {res['liveness_score'] * 100:.1f}%")
            print(f"MESSAGE:           {res['message']}")
            print("-" * 72)
        elif choice == "6":
            print("\n[Continuous Presence] Current Room State:")
            summary = attendance_system.presence_fsm.get_session_summary()
            print(f"  Active Session:  {summary['session_id']} ({summary['course_name']})")
            print(f"  Students In Room: {summary['in_room_now']}")
            print(f"  Present: {summary['present_count']} | Late: {summary['late_count']} | Review: {summary['review_count']}")
            
            adv = input("\nAdvance to Period 2 (Carry-Over in-room students)? (Y/n): ").strip().lower()
            if adv != 'n':
                carry = attendance_system.presence_fsm.advance_to_next_period(
                    next_session_id="CS102_PERIOD_2",
                    course_name="Computer Science 102",
                    start_time="09:50:00",
                    end_time="10:45:00"
                )
                print(f"\nAdvanced to Period 2! {carry['carried_over_count']} students carried over automatically as Present!")
            
            audit = input("\nTrigger WP 7 Passive Overhead Camera Roster Audit? (Y/n): ").strip().lower()
            if audit != 'n':
                in_room = attendance_system.presence_fsm.get_room_presence("hall_a")
                embs = [attendance_system.embedding_store.get_embedding(s) for s in in_room if attendance_system.embedding_store.get_embedding(s) is not None]
                audit_res = attendance_system.roster_auditor.execute_roster_audit("CS102_PERIOD_2", embs)
                print(f"  Overhead Faces Detected: {audit_res['faces_detected_in_camera']}")
                print(f"  Confirmed In-Room:      {audit_res['confirmed_in_room_count']}")
                print(f"  Teacher Advisories:     {audit_res['teacher_advisories']}")
        elif choice == "7":
            print("\n[Camera View Headcount & Anti-Tailgating Tester]")
            default_img = r"C:\Users\vansh\.gemini\antigravity-ide\brain\e234ea8f-b0bd-4e51-a502-a68758dd8b49\.user_uploaded\media_1790663716065.png"
            img_input = input(f"Enter image path [default: test face photo]: ").strip() or default_img
            if not os.path.exists(img_input):
                print(f"File not found: {img_input}. Testing synthetic blank frame instead.")
                import base64, cv2
                blank = np.zeros((240, 320, 3), dtype=np.uint8)
                _, b_buf = cv2.imencode(".jpg", blank)
                b64 = base64.b64encode(b_buf.tobytes()).decode("utf-8")
            else:
                import base64
                with open(img_input, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")

            res = attendance_system.get_live_headcount(b64)
            print("\n" + "-" * 72)
            print(f"HEADCOUNT DETECTED: {res['headcount']} person(s)")
            print(f"CROWD DENSITY:      {res['density_category']}")
            print(f"TAILGATING STATUS:  {'⚠️ TAILGATING DETECTED' if res['tailgating_warning'] else '✅ Single Person / Clear'}")
            print(f"CLARITY SCORE:      {res['sharpness_score']} Laplacian var")
            print(f"DETECTED FACES:     {len(res['all_faces'])}")
            for f in res['all_faces']:
                print(f"  • Face #{f['face_id']}: Confidence {f['confidence']*100:.1f}%, Box {f['box']}")
            print("-" * 72)
        elif choice == "8":
            print("Exiting test utility.")
            break
        else:
            print("Invalid selection. Please choose 1-8.")


        input("\nPress Enter to continue...")


def main():
    parser = argparse.ArgumentParser(description="Manual Tester for Campus Anomaly Models")
    parser.add_argument("--person", type=str, help="Person ID")
    parser.add_argument("--location", type=str, help="Location ID")
    parser.add_argument("--time", type=str, help="ISO Timestamp (e.g. 2026-09-29T08:30:00)")
    parser.add_argument("--event", type=str, default="entry", choices=["entry", "exit", "denied"], help="Event type")
    parser.add_argument("--suite", action="store_true", help="Run full pre-packaged security test suite")
    parser.add_argument("--model-dir", type=str, default="models", help="Directory containing model artifacts")
    args = parser.parse_args()

    engine = CampusAnomalyEngine()
    try:
        engine.load(args.model_dir)
        print(f"[Init] Loaded models from '{args.model_dir}'.")
    except Exception as e:
        print(f"[Error] Failed to load models: {e}")
        print("Please ensure models exist by running: python pipeline.py --train")
        sys.exit(1)

    store = CampusFeatureStore()

    if args.suite:
        run_test_suite(engine)
    elif args.person and args.location:
        ts = args.time or datetime.datetime.now().isoformat()
        evaluate_single_scan(engine, store, args.person, args.location, ts, args.event)
    else:
        interactive_menu(engine, store)


if __name__ == "__main__":
    main()
