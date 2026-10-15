#!/usr/bin/env python3
"""
synthetic_generator.py
======================
Campus Automation System: Phase 1 Irregularity Flagging Engine
Synthetic Event Log Generator

Generates realistic RFID/biometric campus access event streams conforming to the
standardized shared event contract:
    {
      "person_id": str,
      "location_id": str,
      "timestamp": "ISO 8601 string",
      "event_type": "entry" | "exit" | "denied"
    }

Key Features:
- 100 individuals (70 students, 30 faculty/staff) with persona-based routines.
- 12 campus locations across Perimeter Gates, Academic Halls, and Facilities.
- Graph-based physical minimum travel distance/time matrix.
- Ground-truth anomaly injection:
    1. Impossible Travel / Buddy-Punching (< 60s across distant locations).
    2. Temporal Curfew Breaches (unauthorized access between 23:00 - 05:00).
    3. Repeated Denied Scans (3-5 consecutive denied scans within 120s).
    4. Spatial Novelty (unauthorized / first-time access to restricted facilities).
- Dual output: Labeled CSV for ML training & contract-only JSONL for streaming ingestion.
"""

import argparse
import datetime
import json
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Campus Topology & Minimum Physical Transit Matrix (Seconds)
# ---------------------------------------------------------------------------
CAMPUS_LOCATIONS: Dict[str, Dict[str, Any]] = {
    # Perimeter Gates (Entry/Exit to campus)
    "gate_north": {"zone": "perimeter", "restricted": False, "name": "North Gate Turnstiles"},
    "gate_south": {"zone": "perimeter", "restricted": False, "name": "South Gate Turnstiles"},
    "gate_main": {"zone": "perimeter", "restricted": False, "name": "Main Entrance Plaza"},

    # Academic Buildings & Research Laboratories
    "hall_a": {"zone": "academic", "restricted": False, "name": "Lecture Hall Complex A"},
    "hall_b": {"zone": "academic", "restricted": False, "name": "Science Block Hall B"},
    "lecture_c": {"zone": "academic", "restricted": False, "name": "Auditorium Lecture C"},
    "lab_cs": {"zone": "academic", "restricted": False, "name": "Computer Science Lab Complex"},
    "eng_block": {"zone": "academic", "restricted": False, "name": "Engineering Design Center"},

    # Campus Amenities & Common Facilities
    "library_main": {"zone": "facility", "restricted": False, "name": "Central Campus Library"},
    "cafeteria": {"zone": "facility", "restricted": False, "name": "Student Center Dining Hall"},
    "sports_complex": {"zone": "facility", "restricted": False, "name": "Indoor Athletic Arena"},

    # Secure Administrative & Executive Facility
    "admin_block": {"zone": "secure_facility", "restricted": True, "name": "Executive Administration Vault"},
}

# Pairwise minimum physical transit time (in seconds).
# Based on average walking speed ~1.3 m/s and campus layout geometry.
MIN_TRANSIT_SECONDS: Dict[Tuple[str, str], int] = {
    ("gate_north", "gate_south"): 480,
    ("gate_north", "gate_main"): 300,
    ("gate_south", "gate_main"): 360,
    ("gate_north", "sports_complex"): 420,
    ("gate_south", "lab_cs"): 450,
    ("gate_main", "admin_block"): 180,
    ("hall_a", "sports_complex"): 360,
    ("lab_cs", "sports_complex"): 400,
    ("admin_block", "gate_south"): 380,
    ("library_main", "gate_north"): 320,
}


def get_min_transit_time(loc_a: str, loc_b: str) -> int:
    """
    Calculates the minimum physically possible transit time in seconds between two points.
    Transitions occurring faster than this indicate credential sharing (buddy-punching).
    """
    if loc_a == loc_b:
        return 5  # Minimum turnstile cycle interval

    pair = (loc_a, loc_b)
    rev_pair = (loc_b, loc_a)
    if pair in MIN_TRANSIT_SECONDS:
        return MIN_TRANSIT_SECONDS[pair]
    if rev_pair in MIN_TRANSIT_SECONDS:
        return MIN_TRANSIT_SECONDS[rev_pair]

    # Topological fallback based on campus zoning
    zone_a = CAMPUS_LOCATIONS.get(loc_a, {}).get("zone", "perimeter")
    zone_b = CAMPUS_LOCATIONS.get(loc_b, {}).get("zone", "perimeter")
    if zone_a == zone_b:
        return 75  # Intra-zone transit
    return 180     # Inter-zone transit


# ---------------------------------------------------------------------------
# Person Profiles & Habitual Baseline Generators
# ---------------------------------------------------------------------------
def build_person_profiles(num_students: int = 70, num_faculty: int = 30) -> List[Dict[str, Any]]:
    """
    Constructs behavioral personas with distinct baseline arrival schedules,
    primary facilities, and movement habits.
    """
    profiles: List[Dict[str, Any]] = []

    # 1. Student Personas
    for i in range(1, num_students + 1):
        pid = f"STU_{i:03d}"
        arr_mean = random.choice([8.25, 8.75, 9.25, 10.0])  # Typical morning arrival hour
        arr_std = random.uniform(0.18, 0.40)                # Personal schedule consistency
        preferred_gate = random.choice(["gate_main", "gate_north", "gate_south"])
        major = random.choice(["cs", "engineering", "arts", "science"])

        if major == "cs":
            acad_locs = ["lab_cs", "hall_a", "library_main"]
        elif major == "engineering":
            acad_locs = ["eng_block", "hall_b", "library_main"]
        elif major == "science":
            acad_locs = ["hall_b", "lecture_c", "library_main"]
        else:
            acad_locs = ["hall_a", "lecture_c", "cafeteria"]

        profiles.append({
            "person_id": pid,
            "role": "student",
            "arr_mean": arr_mean,
            "arr_std": arr_std,
            "preferred_gate": preferred_gate,
            "acad_locs": acad_locs,
            "dwell_hours": random.uniform(5.5, 8.5),
        })

    # 2. Faculty & Staff Personas
    for i in range(1, num_faculty + 1):
        pid = f"FAC_{i:03d}"
        arr_mean = random.choice([7.75, 8.25, 8.5])
        arr_std = random.uniform(0.10, 0.25)                # Faculty adhere to strict schedules
        preferred_gate = random.choice(["gate_main", "gate_north"])
        dept = random.choice(["eng", "cs", "admin", "science"])

        if dept == "admin":
            acad_locs = ["admin_block", "cafeteria", "hall_a"]
        elif dept == "cs":
            acad_locs = ["lab_cs", "hall_a", "library_main"]
        elif dept == "eng":
            acad_locs = ["eng_block", "hall_b", "library_main"]
        else:
            acad_locs = ["hall_b", "lecture_c", "library_main"]

        profiles.append({
            "person_id": pid,
            "role": "faculty",
            "arr_mean": arr_mean,
            "arr_std": arr_std,
            "preferred_gate": preferred_gate,
            "acad_locs": acad_locs,
            "dwell_hours": random.uniform(7.0, 9.5),
        })

    return profiles


# ---------------------------------------------------------------------------
# Synthetic Log Stream Simulation
# ---------------------------------------------------------------------------
def generate_campus_dataset(
    num_days: int = 30,
    num_students: int = 70,
    num_faculty: int = 30,
    start_date: datetime.date = datetime.date(2026, 9, 1),
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simulates a multi-day stream of scan events conforming to real human routines,
    with calibrated physical anomaly injection.
    """
    random.seed(seed)
    np.random.seed(seed)

    profiles = build_person_profiles(num_students=num_students, num_faculty=num_faculty)
    events: List[Dict[str, Any]] = []

    for day_idx in range(num_days):
        current_date = start_date + datetime.timedelta(days=day_idx)
        is_weekend = current_date.weekday() >= 5

        # Weekend presence is lower (~15% students, ~10% faculty)
        daily_profiles = [
            p for p in profiles
            if (not is_weekend) or (random.random() < (0.15 if p["role"] == "student" else 0.10))
        ]

        for p in daily_profiles:
            pid = p["person_id"]

            # 1. Morning Arrival Scan
            arr_hour = float(np.random.normal(p["arr_mean"], p["arr_std"]))
            arr_hour = max(6.5, min(arr_hour, 12.0))
            arr_minutes = int((arr_hour % 1) * 60)
            arr_seconds = random.randint(0, 59)
            arr_dt = datetime.datetime.combine(
                current_date,
                datetime.time(int(arr_hour), arr_minutes, arr_seconds)
            )

            # Natural scanner misread rate (~0.8%)
            first_event = "denied" if random.random() < 0.008 else "entry"
            gate = p["preferred_gate"] if random.random() < 0.85 else random.choice(["gate_north", "gate_south", "gate_main"])

            events.append({
                "person_id": pid,
                "location_id": gate,
                "timestamp": arr_dt.isoformat(),
                "event_type": first_event,
                "anomaly_label": "normal",
                "anomaly_type": "none",
            })

            # If initial scan was denied by natural misread, immediately retry successfully
            if first_event == "denied":
                retry_dt = arr_dt + datetime.timedelta(seconds=random.randint(6, 15))
                events.append({
                    "person_id": pid,
                    "location_id": gate,
                    "timestamp": retry_dt.isoformat(),
                    "event_type": "entry",
                    "anomaly_label": "normal",
                    "anomaly_type": "none",
                })
                current_dt = retry_dt
            else:
                current_dt = arr_dt

            # 2. Midday Intra-Campus Movements (Academic Sessions, Cafeteria, Library)
            num_transitions = random.randint(2, 5)
            for _ in range(num_transitions):
                step_mins = random.randint(45, 140)
                current_dt += datetime.timedelta(minutes=step_mins)
                if current_dt.hour >= 20:
                    break

                target_loc = random.choice(p["acad_locs"])
                # 90% entry, 10% exit
                trans_type = "entry" if random.random() < 0.90 else "exit"

                events.append({
                    "person_id": pid,
                    "location_id": target_loc,
                    "timestamp": current_dt.isoformat(),
                    "event_type": trans_type,
                    "anomaly_label": "normal",
                    "anomaly_type": "none",
                })

            # 3. Evening Departure Scan
            dwell_td = datetime.timedelta(hours=p["dwell_hours"])
            exit_dt = arr_dt + dwell_td + datetime.timedelta(minutes=random.randint(-20, 30))
            if exit_dt <= current_dt:
                exit_dt = current_dt + datetime.timedelta(minutes=random.randint(15, 45))

            exit_gate = random.choice(["gate_north", "gate_south", "gate_main"])
            events.append({
                "person_id": pid,
                "location_id": exit_gate,
                "timestamp": exit_dt.isoformat(),
                "event_type": "exit",
                "anomaly_label": "normal",
                "anomaly_type": "none",
            })

    # -----------------------------------------------------------------------
    # Ground-Truth Anomaly Injection (Calibrated to realistic ~2.5% rate)
    # -----------------------------------------------------------------------
    injected_events: List[Dict[str, Any]] = []

    # Category 1: Impossible Travel / Buddy-Punching (Delta-T < 60s across distant gates)
    for day_idx in range(num_days):
        # 1-2 incidents per day
        for _ in range(random.randint(1, 2)):
            target_p = random.choice(profiles)["person_id"]
            inject_dt = datetime.datetime.combine(
                start_date + datetime.timedelta(days=day_idx),
                datetime.time(random.randint(8, 17), random.randint(0, 59), random.randint(0, 30))
            )
            # Scan 1: North Gate
            injected_events.append({
                "person_id": target_p,
                "location_id": "gate_north",
                "timestamp": inject_dt.isoformat(),
                "event_type": "entry",
                "anomaly_label": "anomaly",
                "anomaly_type": "impossible_travel",
            })
            # Scan 2: South Gate within 15-35 seconds (minimum required is 480s)
            impos_dt = inject_dt + datetime.timedelta(seconds=random.randint(15, 35))
            injected_events.append({
                "person_id": target_p,
                "location_id": "gate_south",
                "timestamp": impos_dt.isoformat(),
                "event_type": "entry",
                "anomaly_label": "anomaly",
                "anomaly_type": "impossible_travel",
            })

    # Category 2: Temporal Off-Hours / Curfew Breach (01:00 - 04:30 AM)
    for day_idx in range(num_days):
        if random.random() < 0.65:
            target_p = random.choice(profiles)["person_id"]
            curfew_hour = random.choice([1, 2, 3, 4])
            curfew_dt = datetime.datetime.combine(
                start_date + datetime.timedelta(days=day_idx),
                datetime.time(curfew_hour, random.randint(5, 50), random.randint(0, 59))
            )
            target_loc = random.choice(["admin_block", "eng_block", "lab_cs"])
            injected_events.append({
                "person_id": target_p,
                "location_id": target_loc,
                "timestamp": curfew_dt.isoformat(),
                "event_type": "entry",
                "anomaly_label": "anomaly",
                "anomaly_type": "off_hours",
            })

    # Category 3: Repeated Denied Scans Burst (Brute-force / Skimming)
    for day_idx in range(num_days):
        # 1-3 incidents per day
        for _ in range(random.randint(1, 3)):
            target_p = random.choice(profiles)["person_id"]
            burst_loc = random.choice(["admin_block", "lab_cs", "gate_main"])
            base_dt = datetime.datetime.combine(
                start_date + datetime.timedelta(days=day_idx),
                datetime.time(random.randint(9, 21), random.randint(0, 59), random.randint(0, 30))
            )
            # 3-4 consecutive denied attempts within 45s
            for burst_idx in range(random.randint(3, 4)):
                burst_dt = base_dt + datetime.timedelta(seconds=burst_idx * random.randint(8, 14))
                injected_events.append({
                    "person_id": target_p,
                    "location_id": burst_loc,
                    "timestamp": burst_dt.isoformat(),
                    "event_type": "denied",
                    "anomaly_label": "anomaly",
                    "anomaly_type": "denied_burst",
                })

    # Category 4: Spatial Novelty / Unauthorized Vault Exploration
    student_profiles = [p for p in profiles if p["role"] == "student"]
    for day_idx in range(num_days):
        if random.random() < 0.50:
            target_p = random.choice(student_profiles)["person_id"]
            novel_dt = datetime.datetime.combine(
                start_date + datetime.timedelta(days=day_idx),
                datetime.time(random.randint(10, 16), random.randint(0, 59), random.randint(0, 59))
            )
            injected_events.append({
                "person_id": target_p,
                "location_id": "admin_block",
                "timestamp": novel_dt.isoformat(),
                "event_type": "entry",
                "anomaly_label": "anomaly",
                "anomaly_type": "spatial_novelty",
            })

    # Combine, sort strictly chronologically, and format
    all_events = events + injected_events
    df = pd.DataFrame(all_events)
    df["dt"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    df = df.sort_values("dt").reset_index(drop=True).drop(columns=["dt"])

    return df


def save_contract_jsonl(df: pd.DataFrame, filepath: str) -> None:
    """
    Exports events formatted strictly against the shared 4-field contract schema:
    { "person_id": str, "location_id": str, "timestamp": str, "event_type": str }
    """
    contract_cols = ["person_id", "location_id", "timestamp", "event_type"]
    records = df[contract_cols].to_dict(orient="records")
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic RFID/biometric campus access event streams."
    )
    parser.add_argument("--num-days", type=int, default=30, help="Number of simulated days (default: 30)")
    parser.add_argument("--num-students", type=int, default=70, help="Number of student personas (default: 70)")
    parser.add_argument("--num-faculty", type=int, default=30, help="Number of faculty personas (default: 30)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-csv", type=str, default="campus_scans.csv", help="Labeled CSV output path")
    parser.add_argument("--output-jsonl", type=str, default="campus_scans.jsonl", help="Contract-only JSONL path")

    args = parser.parse_args()

    print(f"[Synthetic Generator] Generating {args.num_days} days of campus scans...")
    df = generate_campus_dataset(
        num_days=args.num_days,
        num_students=args.num_students,
        num_faculty=args.num_faculty,
        seed=args.seed,
    )

    total_events = len(df)
    anomalies = len(df[df["anomaly_label"] == "anomaly"])
    print(f"[Synthetic Generator] Total events: {total_events:,}")
    print(f"[Synthetic Generator] Anomalies injected: {anomalies:,} ({anomalies / total_events * 100:.2f}%)")
    print(f"[Synthetic Generator] Breakdown by type:\n{df['anomaly_type'].value_counts()}")

    df.to_csv(args.output_csv, index=False)
    print(f"[Synthetic Generator] Labeled dataset saved to: {args.output_csv}")

    save_contract_jsonl(df, args.output_jsonl)
    print(f"[Synthetic Generator] Contract JSONL stream saved to: {args.output_jsonl}")


if __name__ == "__main__":
    main()
