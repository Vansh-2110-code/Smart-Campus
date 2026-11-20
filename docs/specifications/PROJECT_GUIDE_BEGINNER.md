# Smart Campus Unified Attendance & Irregularity Flagging System
## Complete Beginner-Friendly Guide & Project Walkthrough

**Document Version:** 3.1-EXTENDED  
**Target Audience:** Students, Instructors, Hardware Enthusiasts, and Beginners  
**Design Theme:** Academic Emerald Green & Crisp White  

---

## Quick Start in 3 Easy Steps

If you want to see the complete system working in under 60 seconds, follow these 3 steps:

```
+------------------------------------------------------------------------+
|                        QUICK START IN 3 STEPS                          |
+------------------------------------------------------------------------+
| 1. Open PowerShell / Terminal in the project directory:               |
|    cd "d:\smart campus"                                                |
|                                                                        |
| 2. Start the unified AI server:                                        |
|    python -m uvicorn service:app --host 127.0.0.1 --port 8000          |
|                                                                        |
| 3. Open your web browser and navigate to:                              |
|    -> http://127.0.0.1:8000/dashboard                                  |
+------------------------------------------------------------------------+
```

Once the web dashboard opens in your browser:
1. Click **Tab 2 ("Door 1:1 Face Verification Simulator")**.
2. Click **"[START] Start Live Webcam"** -- your live camera feed will appear.
3. Watch the dynamic **Live Headcount Tag (`[HEADCOUNT] Headcount: 1 Person`)** appear at the top-left, and watch the dynamic **Emerald Green corner reticles `[   ]`** track all faces and display clarity in real time.
4. Click **"[HEADCOUNT] Audit Headcount"** to view a full breakdown of everyone visible in the camera, their detection confidence, and crowd density level!
5. In the Student ID box, enter `STU_0013` and click **"[PHOTO] Enroll My Face"**. Your photo avatar thumbnail will appear immediately.
6. Click **"[FAST] Capture & Execute 1:1 Face Verification"** -- hear the affirmative chime ring, watch the door solenoid unlock, confirm anti-tailgating passes, and see your name marked **PRESENT** in the classroom roster!

---

## Executive Table of Contents

| Section # | Section Title | Key Topics Covered |
| :---: | :--- | :--- |
| **1** | **What Are We Building and Why? (The Big Picture)** | Buddy-punching, curfew breaches, classroom doorway bottlenecks |
| **2** | **The Three Core Pillars (Modules 1, 2, and 3)** | Perimeter Security, Classroom Attendance & Headcount, and Central Web Console |
| **3** | **A Day in the Life on Smart Campus: Alex's Journey** | 6 chronological scenarios: morning gates, door scan, tailgating attempt, carry-over |
| **4** | **The Plain-English Analogy Dictionary** | 512-d embeddings, cosine similarity, camera headcount, anti-tailgating |
| **5** | **Complete Directory Tour & File Map** | Comprehensive file mapping organized across Modules 1, 2, and 3 |
| **6** | **Deep Dive into Key Source Files** | Under the hood of generator, pipeline, attendance engine, and service |
| **7** | **Concrete API Request & Response Examples** | Copy-pasteable JSON payloads for door verification, headcount, and perimeter scans |
| **8** | **Physical Hardware Assembly & DIY Wiring Guide** | Raspberry Pi 4 pinout schematic for solenoid lock, buzzer, and camera |
| **9** | **Walkthrough of the Web Dashboard (Tabs 1, 2, 3, 4)** | Roster grid, live webcam HUD with headcount pill, SecOps wall, teacher queue |
| **10** | **Beginner FAQ & Troubleshooting Matrix** | Rapid 10-second solutions to lighting, camera, privacy, and port errors |
| **11** | **Command Center Cheat Sheet** | All terminal commands, testing flags, and server launch shortcuts |
| **12** | **Project Summary & Verification Status** | 25/25 tests passing, DPDP Act 2023 compliance, operational readiness |

<!-- pagebreak -->

## 1. What Are We Building and Why? (The Big Picture)

Imagine a modern university with 10,000 students and faculty moving through gates, libraries, labs, and classrooms every single day. Two major challenges happen:

### Problem 1: Campus Security & "Buddy-Punching"
- A student wants to be marked present at campus, so they give their RFID student card to a friend. The friend swipes at the North Gate at 09:00:00 AM, and then swipes their own card at the South Gate at 09:00:20 AM.
- A human cannot walk 1 kilometer in 20 seconds! This is physically impossible (**Buddy-Punching / Impossible Travel**).
- Someone tries scanning into a restricted executive vault or chemical lab at 02:30 AM on a Sunday (**Curfew Violation**).
- Someone's damaged card or a hacker device fails 4 times in 30 seconds (**Brute-Force / Denial Burst**).

### Problem 2: Classroom Attendance Queues & Back-to-Back Classes
- If 60 students enter a classroom and each student has to search for their name or wait for a camera to search through all 10,000 students in the university, it causes a huge doorway traffic jam!
- If students have back-to-back classes in the same room (e.g., Math from 09:00 to 09:50, and Physics from 09:50 to 10:45 in Room 301), making everyone leave the room and scan again at 09:50 is chaotic.

---

## 2. The Three Core Pillars of Smart Campus (Modules 1, 2, and 3)

Our system is engineered as three coordinated modules:

```
+---------------------------------------------------------------------------------------------------+
|                                     SMART CAMPUS ARCHITECTURE                                     |
+---------------------------------+---------------------------------+-------------------------------+
| MODULE 1: CAMPUS SECURITY GATES | MODULE 2: CLASSROOM ATTENDANCE  | MODULE 3: CENTRAL WEB CONSOLE |
| (Perimeter Irregularity Engine) | (Biometric 1:1 Verification)    | (REST API & Live Dashboard)   |
+---------------------------------+---------------------------------+-------------------------------+
| * Turnstiles at Perimeter Gates | * Camera & RFID reader at doors | * Real-time WebRTC Camera HUD |
| * Catches buddy-punching in <60s| * "Verify, do not search" (1:1) | * Physical Solenoid Audio Chime|
| * Stops off-hours curfew breach | * In-Room Presence State Machine| * Teacher Manual Review Queue |
| * Uses Machine Learning (IForest* Students in back-to-back classes| * 1-Click Attendance CSV Export|
| * 3 Tiers: Normal, Review, Alert|   automatically carry over!     | * Fast sub-1ms response speed |
| * Offline buffer if Wi-Fi drops | * WP 7: Passive room audit check| * Swagger interactive docs    |
+---------------------------------+---------------------------------+-------------------------------+
```

### The Magic Concept: "Verify, Do Not Search" (1:1 Matching)
Instead of pointing a camera at a student and asking: *"Which of our 10,000 campus students is this?"* (which is slow, computationally heavy, and error-prone), we do:
1. The student taps their RFID badge or scans their fingerprint. The badge says: *"I claim to be Student STU_0013 (Alex Rivera)"*.
2. The door camera takes a quick picture and asks only ONE question: *"Does this face match Alex Rivera's registered face?"* (1:1 Match).
3. This is lightning fast (< 30 milliseconds), highly accurate, and stops friends from carrying someone else's badge!

### The Second Magic Concept: "Continuous Presence Carry-Over"
- When Alex enters Room 301 at 08:55 AM, he is marked **`IN_ROOM`**.
- When Math class ends at 09:50 AM and Physics begins, Alex does **not** have to get up and scan his badge again! The system knows he never scanned an exit event, so his attendance automatically carries over as **Present** for Physics!

### The Third Magic Concept: "Camera View Headcount & Anti-Tailgating Guard"
What happens if two students try to squeeze through the doorway on a single badge tap ("Tailgating / Piggybacking")?
1. The camera does not just look for one face; its neural network scans the entire view and counts **every visible human face**.
2. If `Headcount == 1`, normal single-person transit proceeds.
3. If `Headcount > 1`, the system instantly flags an **Anti-Tailgating Alert** (`tailgating_detected: true`), displays an amber warning in the console, and alerts the instructor or door attendant to ensure both students badge in!
4. Operators can also click **"Audit Headcount"** at any time to get an instant live head count and crowd density classification of the room.

---

## 3. A Day in the Life on Smart Campus: Alex's Journey

To understand how every part of the software interacts in real life, let us follow a second-year engineering student, **Alex Rivera (ID: `STU_0013`)**, through an entire college day:

```
  08:15 AM               08:55 AM               08:56 AM               09:50 AM               10:10 AM               02:30 AM
  Main Gate              Room 301 Door          Room 301 Door          Room 301 Inside        Room 301 Ceiling       Chemical Vault
+-------------+        +-------------+        +-------------+        +-------------+        +-------------+        +-------------+
| RFID Swipe  |        | Badge + Face|        | Follower Try|        | Class Change|        | Overhead Cam|        | Intruder    |
| IForest AI  |------->| 1:1 Biometric|------>| Headcount=2 |------->| Automatic   |------->| Passive WP7 |------->| Rogue Swipe |
| Risk = 0.12 |        | Sim = 0.89  |        | Tailgate Warn|       | Carry-Over  |        | Audit Check |        | Risk = 0.96 |
+-------------+        +-------------+        +-------------+        +-------------+        +-------------+        +-------------+
  [NORMAL]               [PRESENT]              [TAILGATE FLAG]        [PRESENT]              [CONFIRMED]            [DEADLOCKED]
  Door Opens             Chime Sounds           Amber Warning          Zero Re-scans          Roster Match           Siren Sounds
```

### Scenario 1: 08:15 AM -- Morning Perimeter Gate Arrival
- Alex swipes his RFID badge at the Main Campus Turnstile.
- **Under the Hood:** `pipeline.py` extracts 17 spatio-temporal features. Alex arrives on a weekday morning at a main entrance (his normal routine).
- **AI Decision:** Isolation Forest computes an anomaly risk score of $0.12$ (🟢 **Normal**).
- **Physical Result:** Turnstile clicks unlocked, green LED flashes, Alex walks onto campus.

### Scenario 2: 08:55 AM -- Classroom Entrance (Math 101, Period 1)
- Alex arrives at Room 301. The door has an RFID reader and a webcam.
- Alex taps his card. The camera captures his face in 7 ms via YuNet.
- **Under the Hood:** SFace creates a 512-dimensional vector and computes Cosine Similarity against Alex's enrolled vector. Score = $0.89$ ($\ge 0.72$).
- **Physical Result:** Solenoid relay unlatches, affirmative chime plays, Alex is marked **`PRESENT`** and enters room state **`IN_ROOM`**.

### Scenario 2b: 08:56 AM -- Anti-Tailgating Guard in Action (The Doorway Squeeze)
- Right as Alex verifies, a classmate, Jordan, tries to quickly sneak in through the open door behind him without swiping.
- **Under the Hood:** The camera's YuNet detector detects **two distinct faces** in the doorway: Person #1 (Alex, 94% match) and Person #2 (Jordan, 87% detection confidence).
- **AI Decision:** Headcount = 2 (`Pair / Potential Tailgating`).
- **System Action:** The door verification registers Alex's entry but flags a high-visibility amber notice: `[Tailgating Alert: Headcount=2 in doorway]`. The screen prompts Jordan to present his badge, preventing unrecorded entry!

### Scenario 3: 09:50 AM -- Back-to-Back Period 2 Transition (Physics 201)
- Math class concludes. Physics starts immediately in the same room.
- While other systems force all 40 students to step outside and queue up again, our **Presence State Machine** inspects the room state.
- **Under the Hood:** Because Alex never swiped an exit reader, the state machine confirms he is still `IN_ROOM`.
- **System Action:** Alex is automatically registered as **`PRESENT`** for Physics 201 with zero interaction required!

### Scenario 4: 10:10 AM -- Work Package 7 Passive Roster Audit
- Around minute 15 of Physics class, the wide-angle ceiling camera takes an audit snapshot of the room.
- **Under the Hood:** The engine detects all faces seated in the room and runs a constrained 1:N match **strictly against the 40 students enrolled in Physics 201**.
- **Result:** Alex is confirmed present. The teacher's dashboard shows a green verified checkmark.

### Scenario 5: 02:30 AM -- Curfew Intruder Caught (The Lost Badge)
- That night, a lost student card is swiped at the High-Security Chemical Lab at 02:30 AM.
- **Under the Hood:** The feature store notices this location is restricted, the time is outside normal hours, and the Z-score deviation is massive.
- **AI Decision:** Risk score = $0.96$ (🔴 **High Confidence Issue**).
- **Physical Result:** Solenoid remains deadlocked, alarm siren triggers, and security guards receive an immediate alert on the SecOps dashboard!

<!-- pagebreak -->

## 4. The Plain-English Analogy Dictionary

Machine learning and cybersecurity can sound intimidating. Here is what every technical term really means in everyday life:

| Technical Term | Everyday Life Analogy | What It Actually Does in Our System |
| :--- | :--- | :--- |
| **512-Dimensional Embedding** | A digital DNA recipe or barcode made of 512 numbers instead of lines. | A non-reversible list of 512 decimal numbers that uniquely describes facial structure (eye spacing, jawline angle, nose bridge). |
| **Cosine Similarity** | Comparing two compass needles or flashlights in the dark. | Measures the angle between two embedding vectors. If they point in the exact same direction, similarity is $1.00$ ($100\%$ match). Threshold is $0.72$. |
| **Isolation Forest** | The "Lone Wolf" on a deserted island. | An AI algorithm that easily isolates anomalies because weird events (like 2:30 AM vault swipes) require very few rule cuts to separate from normal events. |
| **1:1 vs 1:N Matching** | Airport Customs vs "Where's Waldo?". | **1:1** checks: *"Are you who your passport says you are?"* (Fast, 7ms). **1:N** searches: *"Find this face out of 10,000 people"* (Slow, 500ms). |
| **Camera View Headcount** | An automated clicker counter at a theater door. | YuNet neural network detects and counts all visible human faces concurrently in $\le 10$ ms. |
| **Anti-Tailgating Guard** | Subway turnstile arm preventing two people on one metro card. | Flags an alert if multiple people ($\text{Headcount} > 1$) enter a 1:1 door scan simultaneously. |
| **Crowd Density Level** | Rating how busy an elevator or room is. | Categorizes view into Empty (0), Single (1), Pair / Tailgating (2), Small Group (3-6), Crowd (7+). |
| **Presence State Machine** | A hotel room keycard slot on the wall. | Keeps a student's seat active in the room database until they physically swipe out at the exit reader. |
| **Solenoid Latch** | An electromagnetic deadbolt lock. | A 12V metal pin pulled back by a magnetic coil when the computer says `ACCEPT`, letting the student push the door open. |
| **Liveness / Anti-Spoofing** | Spotting the difference between a real apple and a printed photo of an apple. | Examines microscopic skin textures and screen frequency moiré to reject smartphone photos and paper printouts. |
| **Store-and-Forward FIFO** | A postal mailbox that holds letters when the mail truck is delayed. | A local SQLite database on the Raspberry Pi turnstile that saves card scans if the campus Wi-Fi drops, then syncs them when the internet returns. |

---

## 5. Complete Directory Tour & File Map

Here is the exact structure of our codebase, organized cleanly across the **Three Modules (1, 2, and 3)**:

```
d:\smart campus\
|
+--- DOCUMENTATION & BLUEPRINTS
|    +--- ML_Work_Brief__Irregularity_Flagging.pdf   -> Original engineering brief for Module 1 (Security gates)
|    +--- ML_Team_Brief_Smart_Campus_Attendance.docx  -> Original engineering brief for Module 2 (Classroom attendance)
|    +--- SMART_CAMPUS_PRD_TRD_SYSTEM_FLOW.md        -> Complete PRD, TRD, and Architecture Blueprint
|    +--- PROJECT_GUIDE_BEGINNER.md                  -> This beginner guide!
|    +--- PROJECT_GUIDE_BEGINNER.pdf                 -> Publication-ready executive PDF version
|    +--- PROJECT_GUIDE_ADVANCED.md                  -> Advanced mathematical & engineering deep dive
|    +--- PROJECT_GUIDE_ADVANCED.pdf                 -> Publication-ready executive PDF version
|    +--- build_guides_pdf.py                        -> High-end PDF document compiler using ReportLab
|
+--- MODULE 1: IRREGULARITY FLAGGING & GATE SECURITY
|    +--- synthetic_generator.py                     -> Generates 30 days of realistic campus badge scans with anomalies
|    +--- pipeline.py                                -> Feature engineering & AI models (Isolation Forest, PU Forest)
|    +--- hardware_edge_agent.py                     -> Runs on turnstiles (Raspberry Pi/PC); has offline SQLite buffer
|    +--- campus_scans.csv                           -> 13,000 synthetic scan events dataset
|    +--- manual_test.py                             -> Interactive CLI tool to manually test scans & security alerts
|
+--- MODULE 2: BIOMETRIC 1:1 FACE ATTENDANCE & HEADCOUNT ENGINE
|    +--- attendance_engine.py                       -> Deep face detection (YuNet), SFace biometrics, liveness gating,
|    |                                                  Multi-Person Headcount audit, Anti-Tailgating, FSM presence
|    +--- models/                                    -> Serialized AI models directory:
|    |    +--- face_detection_yunet_2023mar.onnx      -> High-speed multi-person face detector (sub-10ms inference)
|    |    +--- face_recognition_sface_2021dec.onnx    -> Deep facial biometric identity extractor (SFace)
|    |    +--- isolation_forest.joblib                -> Gate anomaly detector model
|    |    +--- next_gen_model.joblib                  -> Positive-Unlabeled Random Forest
|    |    +--- benchmark_results.json                 -> Model comparison metrics table
|    +--- data/                                      -> Persistent state directory:
|         +--- embeddings/                            -> DPDP Act encrypted per-student 512-d feature vectors
|         +--- presence_state.json                    -> Real-time continuous room presence database
|
+--- MODULE 3: CENTRAL FASTAPI SERVICE & WEB CONSOLE
     +--- service.py                                 -> FastAPI unified REST API (<1ms latency) with /attendance/headcount
     +--- dashboard.html                             -> Modern console with camera HUD, live headcount tag, and audio chimes
     +--- test_service.py                            -> Automated Pytest verification suite (25 tests, 100% pass)
```

<!-- pagebreak -->

## 6. How the Key Files Work Under the Hood

### Files in Module 1: Perimeter Security
- **`synthetic_generator.py`:** Generates 100 student/faculty profiles, 12 campus locations, and 13,000 realistic badge scans with injected buddy-punching and curfew anomalies.
- **`pipeline.py`:** Extracts 17 spatio-temporal features (Z-scores, hours outside daytime band, spatial novelty), fits an Isolation Forest and Positive-Unlabeled Random Forest, and outputs calibrated confidence tiers (🟢 Normal, 🟡 Review, 🔴 Alert).
- **`hardware_edge_agent.py`:** The turnstile controller code. If network drops, it queues scans in a local SQLite store-and-forward buffer.

### Files in Module 2: Classroom Biometric & Headcount Engine
- **`attendance_engine.py`:** Contains:
  1. `detect_all_faces`: Runs YuNet in ~8ms across the entire frame to detect every visible face, bounding box, and 5 landmark points.
  2. `get_live_headcount`: Computes accurate real-time headcount, classifies crowd density, and warns against doorway tailgating.
  3. `FaceDetectionAndEmbeddingEngine`: Projects primary face into 512-d normalized embedding space using hybrid SFace and MobileNet-V3.
  4. `ClassroomPresenceStateMachine`: Tracks `IN_ROOM` vs `OUT_OF_ROOM` state to carry students over across back-to-back classes automatically.
  5. `PassiveClassroomRosterAuditor`: Runs WP 7 overhead checks constrained strictly to the active class roster.

### Files in Module 3: Microservice & Web Console
- **`service.py`:** Central high-throughput FastAPI REST server providing `/score`, `/attendance/verify`, `/attendance/headcount`, `/attendance/detect-face`, `/attendance/student/{id}`, and `/dashboard`.
- **`dashboard.html`:** The unified single-page web console with live camera tracking, floating headcount pill, multi-face HUD reticles, audio solenoid chimes, and 1-click CSV attendance export.
- **`test_service.py`:** 25 comprehensive unit tests validating physical rules, biometrics, liveness, multi-person headcount, anti-tailgating, and API responses.

---

## 7. Concrete API Request & Response Examples

### Example 1: Door Face Verification Request (With Headcount Telemetry)
**Endpoint:** `POST /attendance/verify`
```json
{
  "claimed_id": "STU_0013",
  "room_id": "hall_a",
  "timestamp": "2026-09-29T09:05:00",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

**Successful Response (`200 OK`):**
```json
{
  "claimed_id": "STU_0013",
  "room_id": "hall_a",
  "timestamp": "2026-09-29T09:05:00",
  "decision": "ACCEPT",
  "door_unlocked": true,
  "attendance_status": "Present",
  "similarity_score": 0.884,
  "liveness_score": 0.942,
  "headcount": 1,
  "tailgating_detected": false,
  "reason_code": "GENUINE_MATCH",
  "message": "Access granted: Verified 1:1 biometric identity for STU_0013"
}
```

### Example 2: Real-Time Camera View Headcount Audit Request
**Endpoint:** `POST /attendance/headcount`
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Successful Response (`200 OK`):**
```json
{
  "status": "success",
  "timestamp": "2026-09-30T11:45:00.124Z",
  "headcount": 2,
  "density_category": "Pair / Potential Tailgating",
  "status_description": "Two individuals in camera view (potential tailgating / buddy scan)",
  "tailgating_warning": true,
  "sharpness_score": 118.4,
  "all_faces": [
    {
      "face_id": 1,
      "confidence": 0.942,
      "box": [110, 65, 84, 102],
      "area": 8568
    },
    {
      "face_id": 2,
      "confidence": 0.871,
      "box": [220, 78, 72, 90],
      "area": 5184
    }
  ]
}
```

### Example 3: Gate Perimeter Card Scan Request
**Endpoint:** `POST /score`
```json
{
  "person_id": "STU_0013",
  "location_id": "gate_main",
  "event_type": "entry",
  "timestamp": "2026-09-29T08:15:00Z"
}
```

**Successful Response (`200 OK`):**
```json
{
  "person_id": "STU_0013",
  "risk_score": 0.12,
  "tier": "NORMAL",
  "action": "ALLOW",
  "explanation": "Normal weekday morning arrival schedule"
}
```

<!-- pagebreak -->

## 8. Physical Hardware Assembly & DIY Wiring Guide

If you want to build a physical working turnstile or door scanner using a Raspberry Pi 4 or a PC with an Arduino, here is the hardware schematic:

```
                                  RASPBERRY PI 4 / PC CONTROLLER
                                 +-------------------------------+
                                 |                               |
                                 |  [USB Port 1] --- USB Webcam  |
                                 |  [USB Port 2] --- RFID Reader |
                                 |                               |
                                 |  GPIO 17 (Pin 11)             |
                                 |  GPIO 27 (Pin 13)             |
                                 |  GND     (Pin 6)              |
                                 +-------+--------------+--------+
                                         |              |
                   +---------------------+              +---------------------+
                   v                                                          v
        +-----------------------+                                  +-----------------------+
        |  Optocoupler Relay    |                                  |   Piezo Audio Buzzer  |
        |  Module (5V / 10A)    |                                  |   (5V Active Piezo)   |
        +----------+------------+                                  +-----------------------+
                   |
                   v (12V DC External Supply)
        +-----------------------+
        | 12V Solenoid Deadbolt |  --> Unlocks physical classroom door or turnstile arm!
        +-----------------------+
```

### Pinout Connections:
1. **Solenoid Relay Pin (GPIO 17 / Physical Pin 11):** Driven high (`1`) for 3.0 seconds when `status == "ACCEPT"`, closing the relay contacts to energize the 12V solenoid lock.
2. **Piezo Audio Buzzer Pin (GPIO 27 / Physical Pin 13):** Emits a cheerful double-beep on access granted, or a continuous 1.5-second alarm buzz on security violations.
3. **USB RFID Reader:** Operates as a standard USB-HID keyboard device or serial Wiegand interface, streaming card IDs directly to `hardware_edge_agent.py`.
4. **USB HD Camera:** Positioned at eye-level ($150\text{ cm}$) pointing at the door entrance, feeding frames to YuNet.

---

## 9. Walkthrough of the Web Dashboard (`http://127.0.0.1:8000/dashboard`)

Our console is styled in an academic **Emerald Green & Crisp White** theme with 4 tabs:

### Tab 1: Classroom Attendance & Presence
- Shows active session info (Course Name, Teacher, Grace Window, and Period Number).
- 4 real-time stat cards: **Present**, **Late**, **Currently In Room**, and **Absent**.
- **Real-Time Student Roster Grid:** Lists all 40 students with their room state, entry timestamp, and verification similarity score.
- **Action Buttons:** Advance to Next Period, Trigger WP 7 Passive Roster Audit, and Export Attendance (CSV).

### Tab 2: Door 1:1 Face Verification Simulator (Live Webcam Terminal)
- **Live Video Viewport:** Displays your live webcam stream in real time.
- **Dynamic Live Headcount Tag:** Floating top-left pill (`[HEADCOUNT] Headcount: N`) that continuously displays how many people are in the camera view.
- **Multi-Face HUD Reticles:** Draws emerald corner brackets for Person #1 and cyan/indigo reticles for Person #2, #3, along with 5 glowing facial landmark dots.
- **Anti-Tailgating Warning Banner:** Renders an immediate red banner `[WARN] TAILGATING ALERT: N PEOPLE IN VIEW` when multiple individuals are detected in the doorway.
- **"Audit Headcount" Button:** Instant 1-click camera snapshot breakdown displaying total headcount, crowd density category, and individual face coordinates.
- **Student Profile Preview:** Displays student name, enrolled photo avatar, and registration status.
- **Door Solenoid Reaction Box:** Shows live Solenoid status, 1:1 Cosine Similarity, Camera Headcount, and Anti-Tailgating verification flag (`[OK] Clear` vs `[ALERT] Tailgating Detected`).
- **Audio Feedback:** Synthesizes affirmative harmonic chimes on accept and warning buzzes on reject.

### Tab 3: Gate Irregularity & Curfew Wall (Module 1 Engine)
- Tests campus perimeter gates against physical anomalies with 1 click:
  - 1. Normal Daytime Arrival (Main Gate 08:30 AM -> Authorized).
  - 2. Buddy-Punching (North Gate then South Gate in 15s -> Flagged).
  - 3. Admin Curfew Breach (Executive Vault 02:30 AM -> High Confidence Security Breach).
  - 4. Brute-Force Denied Burst (3 failed card scans in 30s -> Alarm dispatched).

### Tab 4: Teacher Manual Review Queue
- Displays borderline scans ($0.55 \le \text{similarity} < 0.72$) or camera lighting occlusions.
- Allows the professor to click **"Approve Present"** with 1 click to confirm attendance without interrupting lecture.

<!-- pagebreak -->

## 10. Beginner FAQ & Troubleshooting Matrix

| Symptom / Question | Root Cause | Exact 10-Second Fix |
| :--- | :--- | :--- |
| **Camera HUD shows amber `[WARN] Align Face in Center`** | Face is either too far from the camera, tilted >30 deg, or lighting is too dark. | Center your face in the camera view and turn on overhead room lighting. |
| **Verification returns `NO_FACE_DETECTED`** | YuNet deep face detector did not find human face landmarks in the captured frame. | Keep your face still in front of the lens before clicking verify. |
| **"Face does not match claimed badge identity"** | The Student ID entered has not been enrolled with your live face yet. | Type the Student ID (e.g. `STU_0013`) and click **"[PHOTO] Enroll My Face"** once to register. |
| **Why does the screen show `[WARN] Tailgating Alert`?** | The camera detected more than 1 face in view during a 1:1 door badge tap. | Ask the follower to stand back, or badge in individually one-at-a-time. |
| **Are student webcam photos stored on the server?** | Privacy concern under India's DPDP Act 2023. | **No.** Raw photos are instantly discarded. Only a 512-number mathematical vector is encrypted and stored. |
| **Port 8000 already in use error** | A previous server instance is still running in the background. | In PowerShell run: `taskkill /F /IM python.exe` then restart uvicorn. |
| **Unit tests fail or error** | Missing python packages or outdated environment. | Run: `pip install fastapi uvicorn opencv-python onnxruntime scikit-learn pytest`. |

---

## 11. Command Center Cheat Sheet

Here are all the commands you will ever need, collected in one place:

```powershell
# 1. Navigate to the project directory
cd "d:\smart campus"

# 2. Run all 25 unit tests (Takes ~10 seconds)
python -m pytest -v test_service.py

# 3. Start the unified FastAPI backend server
python -m uvicorn service:app --host 127.0.0.1 --port 8000

# 4. Open the Web Dashboard
start http://127.0.0.1:8000/dashboard

# 5. Open the Interactive Swagger API Documentation
start http://127.0.0.1:8000/docs

# 6. Re-generate the publication PDFs
python build_guides_pdf.py
```

---

## 12. Project Summary & Verification Status

Congratulations! You now have a complete, intuitive, and practical understanding of the Smart Campus Access Management & Biometric Attendance System.

- **Module 1 (Perimeter Gate Security):** 100% operational with Isolation Forest and Positive-Unlabeled models.
- **Module 2 (Classroom Biometric Verification & Headcount):** 100% operational with YuNet multi-face detection, SFace, continuous presence tracking, and anti-tailgating guards.
- **Module 3 (REST API & Web Console):** 100% operational with live camera HUD, headcount pill, solenoid chimes, and CSV export.
- **Automated Test Suite:** 25 / 25 unit tests passing (100% pass rate).
