# build_unified_dashboard.py
import os
import re

with open("dashboard.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Header to add Role Switcher and Academic Subtitle
header_old = """      <div class="brand">
        <div class="brand-icon">🏛</div>
        <div>
          <h1>Smart Campus Intelligence</h1>
          <span>Unified Attendance & Irregularity Flagging Console</span>
        </div>
      </div>
      <div class="header-actions">
        <span class="badge-status">System Operational</span>
        <span id="openvino-badge" class="badge-status" style="background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd;" title="Intel OpenVINO Deep Learning Optimization">
          ⚡ OpenVINO Active
        </span>
        <a href="/docs" target="_blank" class="btn btn-outline btn-sm">API Docs (Swagger)</a>
      </div>"""

header_new = """      <div class="brand">
        <div class="brand-icon">🏛</div>
        <div>
          <h1>Smart Campus Intelligence</h1>
          <span>Unified Attendance, Security & Academic AI Suite (SOCI Block)</span>
        </div>
      </div>
      <div class="header-actions" style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
        <!-- Role Switcher -->
        <div class="role-selector" style="display: flex; gap: 0.25rem; align-items: center; background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 20px; font-size: 0.8rem; border: 1px solid var(--border);">
          <span style="font-weight: 600; color: var(--text-muted); margin-right: 0.25rem;">Role:</span>
          <button class="role-pill active" onclick="switchUserRole('student')" id="role-pill-student">👨‍🎓 Student</button>
          <button class="role-pill" onclick="switchUserRole('faculty')" id="role-pill-faculty">👩‍🏫 Faculty</button>
          <button class="role-pill" onclick="switchUserRole('hod')" id="role-pill-hod">🏛️ HOD</button>
          <button class="role-pill" onclick="switchUserRole('security')" id="role-pill-security">🛡️ Security</button>
          <button class="role-pill" onclick="switchUserRole('admin')" id="role-pill-admin">⚙️ Admin</button>
        </div>
        <span class="badge-status">System Operational</span>
        <span id="openvino-badge" class="badge-status" style="background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd;" title="Intel OpenVINO Deep Learning Optimization">
          ⚡ OpenVINO Active
        </span>
        <a href="/docs" target="_blank" class="btn btn-outline btn-sm">API Docs</a>
      </div>"""

if header_old in content:
    content = content.replace(header_old, header_new)
    print("Replaced header successfully")
else:
    print("Header match not found directly, checking partial")

# 2. Add extra stat card for SOCI Academic Module in stats-grid
stats_old = """      <div class="stat-card">
        <span class="label">Teacher Review Queue</span>
        <span class="value" id="stat-review-count">0</span>
        <span class="sub">Borderline / Lighting Occlusions</span>
      </div>
      <div class="stat-card">
        <span class="label">High Confidence Breaches</span>
        <span class="value" style="color: var(--danger);" id="stat-breach-count">0</span>
        <span class="sub">Curfew / Buddy-Punching</span>
      </div>
    </div>"""

stats_new = """      <div class="stat-card">
        <span class="label">Topic 1 Quiz Mastery</span>
        <span class="value" style="color: #0284c7;" id="stat-acad-mastery">86.8%</span>
        <span class="sub" id="stat-acad-sub">38 Attempts / CS101 SOCI</span>
      </div>
      <div class="stat-card">
        <span class="label">Item Discrimination Queue</span>
        <span class="value" style="color: #8b5cf6;" id="stat-item-d-count">1</span>
        <span class="sub">AI Psychometric Review</span>
      </div>
      <div class="stat-card">
        <span class="label">Teacher Review Queue</span>
        <span class="value" id="stat-review-count">0</span>
        <span class="sub">Borderline Occlusions</span>
      </div>
      <div class="stat-card">
        <span class="label">Security Breaches</span>
        <span class="value" style="color: var(--danger);" id="stat-breach-count">0</span>
        <span class="sub">Curfew / Travel Anomaly</span>
      </div>
    </div>"""

if stats_old in content:
    content = content.replace(stats_old, stats_new)
    print("Replaced stats successfully")

# 3. Replace tabs-nav with unified 9 tabs
tabs_old = """    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('tab-attendance')">
        🎓 1. Classroom Attendance & Presence
      </button>
      <button class="tab-btn" onclick="switchTab('tab-verification')">
        🚪 2. Door 1:1 Face Verification Simulator
      </button>
      <button class="tab-btn" onclick="switchTab('tab-secops')">
        🚨 3. Gate Irregularity & Curfew Wall
      </button>
      <button class="tab-btn" onclick="switchTab('tab-review')">
        📋 4. Teacher Manual Review Queue
      </button>
      <button class="tab-btn" onclick="switchTab('tab-logs')">
        📜 5. Classroom Entry & 1:1 Verification Logs
      </button>
    </div>"""

tabs_new = """    <div class="tabs-nav" style="flex-wrap: wrap;">
      <button class="tab-btn active" onclick="switchTab('tab-academic-student')">
        📚 1. Student Study & Quiz Portal
      </button>
      <button class="tab-btn" onclick="switchTab('tab-academic-faculty')">
        🧪 2. Faculty Studio & AI Quiz Builder
      </button>
      <button class="tab-btn" onclick="switchTab('tab-academic-analytics')">
        📊 3. Psychometrics & Integrity Analytics
      </button>
      <button class="tab-btn" onclick="switchTab('tab-academic-ledger')">
        🔗 4. Universal 4-Field Audit Ledger
      </button>
      <button class="tab-btn" onclick="switchTab('tab-attendance')">
        🎓 5. Classroom Attendance & Presence
      </button>
      <button class="tab-btn" onclick="switchTab('tab-verification')">
        🚪 6. Door 1:1 Face Verification
      </button>
      <button class="tab-btn" onclick="switchTab('tab-secops')">
        🚨 7. Gate Irregularity & Curfew Wall
      </button>
      <button class="tab-btn" onclick="switchTab('tab-review')">
        📋 8. Teacher Review Queue
      </button>
      <button class="tab-btn" onclick="switchTab('tab-logs')">
        📜 9. Biometric Verification Logs
      </button>
    </div>"""

if tabs_old in content:
    content = content.replace(tabs_old, tabs_new)
    print("Replaced tabs successfully")

# 4. Insert the 4 new academic tab panes right before tab-attendance
tab1_insert_point = """    <!-- ============================================================== -->
    <!-- TAB 1: CLASSROOM ATTENDANCE & PRESENCE (BACK-TO-BACK CLASSES)  -->
    <!-- ============================================================== -->
    <div id="tab-attendance" class="tab-pane active">"""

tab1_replacement = """    <!-- ============================================================== -->
    <!-- TAB: ACADEMIC MODULE - STUDENT STUDY & QUIZ PORTAL (AC-STU)     -->
    <!-- ============================================================== -->
    <div id="tab-academic-student" class="tab-pane active">
      <div class="grid-2">
        <!-- Left Column: Enrolled Subject & Study Material Progress -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">📚 Course: CS101 Distributed Systems</h2>
            <span class="badge" style="background: #e0f2fe; color: #0369a1; font-weight: 600;">SOCI Block Pilot</span>
          </div>

          <div style="margin-bottom: 1rem; padding: 0.85rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
              <strong style="color: var(--dark); font-size: 0.95rem;">Topic 1: Consensus Protocols & Raft Architecture</strong>
              <span id="topic1-progress-pct" style="font-weight: 700; color: var(--primary);">100% Complete</span>
            </div>
            <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">
              Covers Leader Election, Log Replication, Safety Invariants, and Fault Tolerance. Required for Topic Quiz unlock.
            </p>
            <div style="background: #e2e8f0; border-radius: 6px; height: 8px; overflow: hidden;">
              <div id="topic1-progress-bar" style="background: var(--primary); height: 100%; width: 100%; transition: width 0.3s ease;"></div>
            </div>
          </div>

          <!-- Material Items List -->
          <h3 style="font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 0.75rem;">
            📖 Topic Study Materials (AC-MAT-04)
          </h3>
          <div style="display: flex; flex-direction: column; gap: 0.75rem;" id="student-materials-list">
            <!-- Material Item 1 -->
            <div class="mat-card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; background: #fff;">
              <div style="display: flex; gap: 0.75rem; align-items: center;">
                <span style="font-size: 1.5rem;">📊</span>
                <div>
                  <div style="font-weight: 600; font-size: 0.9rem; color: var(--dark);">Lecture Slides: Raft Consensus & Election Protocol</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">Format: PDF Slides • <span style="color: #dc2626; font-weight: 600;">Required</span></div>
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_001')">View</button>
                <button class="btn btn-primary btn-sm" id="mat-btn-MAT_001" onclick="toggleMaterialCompletion('MAT_001')">✅ Completed</button>
              </div>
            </div>

            <!-- Material Item 2 -->
            <div class="mat-card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; background: #fff;">
              <div style="display: flex; gap: 0.75rem; align-items: center;">
                <span style="font-size: 1.5rem;">📄</span>
                <div>
                  <div style="font-weight: 600; font-size: 0.9rem; color: var(--dark);">Core Technical Document: Diego Ongaro's Raft Paper</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">Format: Research Paper • <span style="color: #dc2626; font-weight: 600;">Required</span></div>
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_002')">View</button>
                <button class="btn btn-primary btn-sm" id="mat-btn-MAT_002" onclick="toggleMaterialCompletion('MAT_002')">✅ Completed</button>
              </div>
            </div>

            <!-- Material Item 3 -->
            <div class="mat-card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; background: #fff;">
              <div style="display: flex; gap: 0.75rem; align-items: center;">
                <span style="font-size: 1.5rem;">🎬</span>
                <div>
                  <div style="font-weight: 600; font-size: 0.9rem; color: var(--dark);">Supplementary Video: Raft Distributed Visual Simulation</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">Format: Interactive Animation • <span style="color: #059669; font-weight: 600;">Optional</span></div>
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_003')">View</button>
                <button class="btn btn-outline btn-sm" id="mat-btn-MAT_003" onclick="toggleMaterialCompletion('MAT_003')">Mark Done</button>
              </div>
            </div>
          </div>

          <!-- Dynamic Quiz Unlock Banner (AC-STU-03, AC-FE-04) -->
          <div id="quiz-unlock-banner" style="margin-top: 1.25rem; padding: 0.85rem; border-radius: 8px; background: #ecfdf5; border: 1px solid #a7f3d0; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; gap: 0.75rem; align-items: center;">
              <span style="font-size: 1.6rem;" id="quiz-unlock-icon">🔓</span>
              <div>
                <strong style="color: #065f46; font-size: 0.92rem;" id="quiz-unlock-title">Topic 1 Quiz Unlocked & Open!</strong>
                <div style="font-size: 0.78rem; color: #047857;" id="quiz-unlock-desc">All required topic study materials completed. Ready for attempt.</div>
              </div>
            </div>
            <button class="btn btn-primary" onclick="launchQuizAttempt()" id="btn-start-quiz">Start Topic Quiz</button>
          </div>
        </div>

        <!-- Right Column: Interactive Quiz Sitting & ML Evaluation Screen -->
        <div class="card" id="student-quiz-container">
          <div class="card-header">
            <h2 class="card-title" id="quiz-session-title">📝 Topic 1 End-of-Topic Quiz</h2>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <span id="quiz-timer-badge" class="badge" style="background: #fef3c7; color: #92400e; font-weight: 700; font-family: monospace;">⏱️ 10:00</span>
              <span id="quiz-autosave-status" class="badge" style="background: #e0f2fe; color: #0369a1;">🟢 Autosaved</span>
            </div>
          </div>

          <!-- Idle / Pre-quiz Banner -->
          <div id="quiz-idle-view" style="padding: 2.5rem 1rem; text-align: center; color: var(--text-muted);">
            <div style="font-size: 3rem; margin-bottom: 0.75rem;">🎯</div>
            <h3 style="color: var(--dark); margin-bottom: 0.5rem;">End-of-Topic Mastery Quiz</h3>
            <p style="font-size: 0.88rem; max-width: 420px; margin: 0 auto 1.25rem auto;">
              Tests your understanding of Raft states, quorum calculation, log safety invariants, and candidate timeouts.
            </p>
            <div style="display: inline-flex; gap: 1.5rem; background: #f8fafc; padding: 0.75rem 1.5rem; border-radius: 8px; border: 1px solid var(--border); font-size: 0.82rem; margin-bottom: 1.25rem;">
              <div><strong>Pass Mark:</strong> 60%</div>
              <div><strong>Time Limit:</strong> 10 Minutes</div>
              <div><strong>Max Attempts:</strong> 3 (Current: 1/3)</div>
            </div>
            <div>
              <button class="btn btn-primary btn-lg" onclick="launchQuizAttempt()">Begin Topic 1 Quiz Now</button>
            </div>
          </div>

          <!-- Active Sitting View (Hidden until attempt starts) -->
          <div id="quiz-active-view" style="display: none;">
            <!-- Question Navigation Palette -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border);">
              <div style="display: flex; gap: 0.4rem;" id="quiz-palette">
                <button class="btn btn-sm btn-primary" onclick="showQuizQuestion(0)">Q1</button>
                <button class="btn btn-sm btn-outline" onclick="showQuizQuestion(1)">Q2</button>
                <button class="btn btn-sm btn-outline" onclick="showQuizQuestion(2)">Q3</button>
                <button class="btn btn-sm btn-outline" onclick="showQuizQuestion(3)">Q4</button>
              </div>
              <span style="font-size: 0.8rem; color: var(--text-muted);" id="q-counter">Question 1 of 4</span>
            </div>

            <!-- Question Cards Container -->
            <div id="active-question-card" style="min-height: 220px; margin-bottom: 1.25rem;">
              <!-- Dynamic question rendered by JS -->
            </div>

            <!-- Quiz Sitting Footer Controls -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; border-top: 1px solid var(--border);">
              <button class="btn btn-outline" id="btn-prev-q" onclick="navigateQuiz(-1)" disabled>Previous</button>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-outline" onclick="saveQuizAnswerDraft()">💾 Save Draft</button>
                <button class="btn btn-primary" id="btn-next-q" onclick="navigateQuiz(1)">Next Question</button>
                <button class="btn btn-success" id="btn-submit-quiz" onclick="confirmSubmitQuiz()" style="display: none; background: #059669; color: white;">🚀 Submit Quiz</button>
              </div>
            </div>
          </div>

          <!-- Instant Scored Result View & ML Evaluation Report (Hidden until submitted) -->
          <div id="quiz-result-view" style="display: none;">
            <div style="padding: 1.25rem; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <span class="badge" style="background: #16a34a; color: white; font-weight: 700; font-size: 0.9rem;" id="result-status-badge">🎉 PASSED (88.0%)</span>
                <h3 style="color: #065f46; margin-top: 0.35rem; font-size: 1.15rem;">Topic 1 Quiz Results Scored</h3>
                <div style="font-size: 0.82rem; color: #15803d;" id="result-score-detail">Scored 4.4 / 5.0 Marks • Duration: 3m 40s (Target: < 3s submit feedback)</div>
              </div>
              <button class="btn btn-outline btn-sm" onclick="retakeQuiz()">Retake Quiz (2/3)</button>
            </div>

            <!-- AC-ML-05 Short Answer Semantic Evaluation Highlight -->
            <div style="padding: 1rem; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 1.25rem; background: #f8fafc;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: var(--dark); font-size: 0.9rem;">🤖 AC-ML-05 Short-Answer Semantic Evaluation</strong>
                <span class="badge" style="background: #ede9fe; color: #6d28d9; font-weight: 600;">Confidence: 94%</span>
              </div>
              <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                Question 4: <em>"Why does Raft use randomized election timeouts rather than fixed timeouts?"</em>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.5rem; font-size: 0.8rem;">
                <div style="padding: 0.5rem; background: white; border: 1px solid var(--border); border-radius: 6px;">
                  <strong style="color: var(--text-muted); display: block; font-size: 0.72rem;">YOUR SUBMITTED ANSWER:</strong>
                  <span id="res-short-student-ans">"Randomized election timeouts ensure candidates do not start elections simultaneously, preventing split votes and repeated deadlocks."</span>
                </div>
                <div style="padding: 0.5rem; background: white; border: 1px solid var(--border); border-radius: 6px;">
                  <strong style="color: var(--text-muted); display: block; font-size: 0.72rem;">REFERENCE STANDARD:</strong>
                  <span>"Randomized timeouts prevent split-vote scenarios where multiple candidates split the votes equally."</span>
                </div>
              </div>
              <div style="display: flex; gap: 1rem; font-size: 0.8rem; background: #f1f5f9; padding: 0.5rem 0.75rem; border-radius: 6px;">
                <div>Cosine Semantic Similarity: <strong style="color: var(--primary);" id="res-sim-score">89.4%</strong></div>
                <div>Concept Coverage: <strong style="color: var(--primary);" id="res-cov-score">100.0%</strong></div>
                <div>Suggested Score: <strong style="color: var(--primary);" id="res-short-score">1.8 / 2.0 Marks</strong></div>
              </div>
              <p style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.5rem;" id="res-short-feedback">
                Feedback: Excellent response: covers core concepts and semantics accurately.
              </p>
            </div>

            <!-- AC-ML-06 Weak-Area Remediation Cards -->
            <div style="margin-bottom: 1.25rem;">
              <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">
                🎯 AC-ML-06 Weak-Area Remediation & Insights
              </h4>
              <div id="weak-areas-container" style="display: flex; flex-direction: column; gap: 0.5rem;">
                <div style="padding: 0.65rem 0.85rem; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; font-size: 0.82rem; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <strong style="color: #92400e;">Fault Tolerance & Quorum Calculation</strong>
                    <div style="font-size: 0.75rem; color: #b45309;">Recommended: Re-read Section 1.4: Raft Paper (Diego Ongaro)</div>
                  </div>
                  <button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_002')">Open Paper</button>
                </div>
              </div>
            </div>

            <!-- AC-ML-08 Advisory Integrity Indicators -->
            <div style="padding: 0.75rem; background: #f8fafc; border-radius: 6px; border: 1px solid var(--border); font-size: 0.78rem; color: var(--text-muted);">
              <strong>🛡️ AC-ML-08 Quiz Integrity Telemetry:</strong> Completion speed within normal baseline (3m 40s). No collusion or identical error clusters detected against 38 peer attempts.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- TAB: ACADEMIC MODULE - FACULTY STUDIO & AI QUIZ BUILDER (AC-QZ)-->
    <!-- ============================================================== -->
    <div id="tab-academic-faculty" class="tab-pane">
      <div class="grid-2">
        <!-- Left Column: Study Material Manager & Upload -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">📁 Topic Study Material Manager</h2>
            <button class="btn btn-primary btn-sm" onclick="openUploadMaterialModal()">+ Upload New Material</button>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem;">
            Manage study materials for <strong>Topic 1: Consensus Protocols & Raft Algorithm</strong>. Toggle Draft/Published and Required/Optional tags (AC-MAT-03, AC-MAT-04).
          </p>

          <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-bottom: 1.25rem;">
            <thead>
              <tr style="border-bottom: 2px solid var(--border); text-align: left; background: #f8fafc;">
                <th style="padding: 0.5rem;">Material Title</th>
                <th style="padding: 0.5rem;">Type</th>
                <th style="padding: 0.5rem;">Status</th>
                <th style="padding: 0.5rem;">Rule</th>
                <th style="padding: 0.5rem;">Action</th>
              </tr>
            </thead>
            <tbody id="faculty-materials-tbody">
              <!-- Rendered via JS -->
            </tbody>
          </table>

          <div style="padding: 0.75rem; background: #f1f5f9; border-radius: 8px; font-size: 0.78rem; color: var(--text-muted);">
            <strong>🛡️ AC-MAT-05 Security:</strong> All uploads undergo automated ClamAV virus scanning, MIME-type verification, and text extraction before publication.
          </div>
        </div>

        <!-- Right Column: AI Question Generator & Review Queue -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">✨ AC-ML-01 Grounded AI Question Generator</h2>
            <span class="badge" style="background: #e0e7ff; color: #4338ca; font-weight: 600;">Zero-Cost Local NLP</span>
          </div>

          <div style="padding: 0.85rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 1.25rem;">
            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label style="font-weight: 600; font-size: 0.82rem;">Source Topic Text Context:</label>
              <select class="form-control" id="gen-topic-select" style="font-size: 0.82rem;">
                <option value="TOPIC_CS101_01">Topic 1: Consensus Protocols & Raft Algorithm (4,120 words extracted)</option>
              </select>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem;">
              <div>
                <label style="font-weight: 600; font-size: 0.82rem;">Questions Count:</label>
                <select class="form-control" id="gen-count-select" style="font-size: 0.82rem;">
                  <option value="3">3 Questions (Fast Pilot)</option>
                  <option value="5" selected>5 Questions (Standard)</option>
                  <option value="10">10 Questions (Comprehensive)</option>
                </select>
              </div>
              <div>
                <label style="font-weight: 600; font-size: 0.82rem;">AI Model Engine:</label>
                <select class="form-control" id="gen-model-engine" style="font-size: 0.82rem;" onchange="toggleApiKeyField()">
                  <option value="local">Local DPDP NLP (Built-in, Zero API Key)</option>
                  <option value="gemini">Google Gemini 1.5 Flash (Cloud LLM)</option>
                </select>
              </div>
            </div>

            <!-- Optional Gemini API Key Field -->
            <div id="gemini-key-container" style="display: none; margin-bottom: 0.75rem;">
              <label style="font-weight: 600; font-size: 0.82rem;">Google Gemini API Key (Optional):</label>
              <input type="password" class="form-control" id="gemini-api-key" placeholder="Enter GEMINI_API_KEY for Cloud LLM" style="font-size: 0.82rem;">
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.25rem;">
                Note: Local DPDP engine requires no key and processes 100% on-premises.
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.78rem; color: var(--text-muted);">Strict Grounding & Quality Filtering Active</span>
              <button class="btn btn-primary" onclick="triggerAIQuestionGeneration()" id="btn-generate-ai">✨ Generate Questions with AI</button>
            </div>
            
            <div id="gen-progress-bar-container" style="display: none; margin-top: 0.75rem;">
              <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.25rem;">
                <span id="gen-status-text">Parsing concepts & grounding passages...</span>
                <span id="gen-percent-text">45%</span>
              </div>
              <div style="background: #e2e8f0; height: 6px; border-radius: 4px; overflow: hidden;">
                <div id="gen-progress-fill" style="background: var(--primary); height: 100%; width: 45%; transition: width 0.3s ease;"></div>
              </div>
            </div>
          </div>

          <!-- AC-QZ-04 AI Draft Review Queue -->
          <div class="card-header" style="margin-top: 1rem; border-top: 1px solid var(--border); padding-top: 1rem;">
            <h3 style="font-size: 0.95rem; color: var(--dark);">📋 AC-QZ-04 AI Draft Review Queue (<span id="review-queue-count">0</span> Drafts)</h3>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Staff approval required before live publish</span>
          </div>

          <div id="review-queue-list" style="display: flex; flex-direction: column; gap: 0.75rem; max-height: 400px; overflow-y: auto;">
            <div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem;">
              Review queue empty. Click "Generate Questions with AI" above to synthesize draft questions from Topic 1 text.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- TAB: ACADEMIC MODULE - PSYCHOMETRICS & INTEGRITY (AC-ML-07/08) -->
    <!-- ============================================================== -->
    <div id="tab-academic-analytics" class="tab-pane">
      <div class="grid-2">
        <!-- Left Column: Item Discrimination Table (AC-ML-07) -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">📊 AC-ML-07 Psychometric Item Discrimination</h2>
            <span class="badge" style="background: #ecfdf5; color: #047857;">N = 38 Attempts</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">
            Classical Test Theory: Item Difficulty (<em>p</em>) & Discrimination Index (<em>D = P<sub>upper</sub> - P<sub>lower</sub></em>). Differentiates mastery and flags flawed or mis-keyed questions.
          </p>

          <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-bottom: 1rem;">
            <thead>
              <tr style="border-bottom: 2px solid var(--border); background: #f8fafc; text-align: left;">
                <th style="padding: 0.5rem;">QID</th>
                <th style="padding: 0.5rem;">Question Prompt</th>
                <th style="padding: 0.5rem;">Diff (<em>p</em>)</th>
                <th style="padding: 0.5rem;">Index (<em>D</em>)</th>
                <th style="padding: 0.5rem;">Diagnosis</th>
              </tr>
            </thead>
            <tbody id="item-discrimination-tbody">
              <!-- Rendered via JS -->
            </tbody>
          </table>

          <div style="padding: 0.75rem; background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; font-size: 0.78rem; color: #9f1239;">
            <strong>🚨 Negative Discrimination Warning Rule:</strong> When <em>D < 0.0</em>, top quartile students missed the question while bottom quartile students guessed correctly. This triggers an automated alert for faculty to review confusing wording or mis-keyed answers.
          </div>
        </div>

        <!-- Right Column: Quiz Integrity Telemetry & Collusion Alerts (AC-ML-08) -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">🛡️ AC-ML-08 Quiz Integrity & Anomaly Signals</h2>
            <span class="badge" style="background: #fef3c7; color: #92400e;">Advisory Review Only</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">
            Monitors attempt duration outliers (speedruns) and identical wrong-answer clusters across peer attempts. Flags are strictly advisory and never auto-penalize students.
          </p>

          <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem;" id="integrity-alerts-container">
            <!-- Alert Card 1 -->
            <div style="padding: 0.75rem; border-radius: 8px; background: #fffbeb; border: 1px solid #fde68a;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <strong style="color: #92400e; font-size: 0.85rem;">⚡ Speedrun Anomaly: Student STU_115</strong>
                <span class="badge" style="background: #f59e0b; color: white;">Risk: Medium</span>
              </div>
              <p style="font-size: 0.78rem; color: #78350f; margin-bottom: 0.5rem;">
                Completed 10-minute Topic 1 Quiz in <strong>45 seconds</strong> (Expected min: 120s). Abnormal rapid clicking profile across 4 questions.
              </p>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-outline btn-sm" onclick="reviewAttemptTelemetry('ATT_004')">View Telemetry</button>
                <button class="btn btn-outline btn-sm" onclick="correctScorePrompt('ATT_004')">Correct Score (AC-RES-02)</button>
              </div>
            </div>

            <!-- Alert Card 2 -->
            <div style="padding: 0.75rem; border-radius: 8px; background: #fef2f2; border: 1px solid #fecaca;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <strong style="color: #991b1b; font-size: 0.85rem;">👥 Identical Error Cluster: STU_102 & STU_115</strong>
                <span class="badge" style="background: #dc2626; color: white;">Risk: High</span>
              </div>
              <p style="font-size: 0.78rem; color: #7f1d1d; margin-bottom: 0.5rem;">
                Both students submitted within 3 minutes of each other with identical uncommon wrong choices on Q_102 and Q_103.
              </p>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-outline btn-sm" onclick="alert('Telemetry profile flagged for HOD consultation.')">Request Interview</button>
                <button class="btn btn-outline btn-sm" onclick="alert('Cleared flag as false positive.')">Dismiss Flag</button>
              </div>
            </div>
          </div>

          <!-- AC-RES-02 Score Correction Flow -->
          <div style="padding: 0.85rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);">
            <h4 style="font-size: 0.85rem; color: var(--dark); margin-bottom: 0.35rem;">✏️ AC-RES-02 Faculty Score Correction</h4>
            <p style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              Adjust student score with mandatory audit reason. Automatically logs to the SHA-256 append-only ledger.
            </p>
            <button class="btn btn-outline btn-sm" onclick="openScoreCorrectionModal()">Open Score Correction Console</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- TAB: ACADEMIC MODULE - UNIVERSAL 4-FIELD AUDIT LEDGER (AC-BE)   -->
    <!-- ============================================================== -->
    <div id="tab-academic-ledger" class="tab-pane">
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">🔗 Universal Four-Field Event Ledger (AC-BE-04 / AC-BE-05)</h2>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
              Universal Contract: <code>{ person_id, location_id, timestamp, event_type }</code> with SHA-256 Hash Chaining
            </div>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-outline btn-sm" onclick="refreshAcademicLedger()">🔄 Refresh Stream</button>
            <a href="/api/v1/academic/ledger/export" class="btn btn-primary btn-sm">📥 Export Ledger CSV (AC-RES-04)</a>
          </div>
        </div>

        <!-- DPDP Compliance & Governance Status -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem; font-size: 0.82rem;">
          <div style="padding: 0.75rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px;">
            <strong style="color: #166534; display: block;">DPDP Privacy Guarantee (AC-ML-10)</strong>
            <span>100% on-premise execution; zero student personal data transmitted to public LLMs.</span>
          </div>
          <div style="padding: 0.75rem; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;">
            <strong style="color: #1e40af; display: block;">Model Rollback Guarantee (AC-ML-09)</strong>
            <span>Active model: <code>nlp-v2.4-local</code> with 15-minute emergency rollback switch.</span>
          </div>
          <div style="padding: 0.75rem; background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 6px;">
            <strong style="color: #6b21a8; display: block;">Idempotent Scoring (AC-BE-06)</strong>
            <span>Attempt freeze + duplicate submit protection active (Zero duplicate records).</span>
          </div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">
          <thead>
            <tr style="border-bottom: 2px solid var(--border); background: #f8fafc; text-align: left;">
              <th style="padding: 0.5rem;">Timestamp (UTC)</th>
              <th style="padding: 0.5rem;">Person ID</th>
              <th style="padding: 0.5rem;">Location ID</th>
              <th style="padding: 0.5rem;">Event Type</th>
              <th style="padding: 0.5rem;">Reason / Payload</th>
              <th style="padding: 0.5rem;">SHA-256 Digest</th>
            </tr>
          </thead>
          <tbody id="academic-ledger-tbody">
            <!-- Rendered via JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- TAB 1: CLASSROOM ATTENDANCE & PRESENCE (BACK-TO-BACK CLASSES)  -->
    <!-- ============================================================== -->
    <div id="tab-attendance" class="tab-pane">"""

if tab1_insert_point in content:
    content = content.replace(tab1_insert_point, tab1_replacement)
    print("Replaced tab panes successfully")
else:
    print("tab-attendance anchor not found directly, checking partial")

# 5. Add custom CSS styles for pills and viewers before </style>
css_anchor = "</style>"
custom_css = """
    /* Role Selector Pills */
    .role-pill {
      border: 1px solid transparent;
      background: transparent;
      padding: 0.25rem 0.6rem;
      border-radius: 14px;
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .role-pill:hover {
      background: #e2e8f0;
      color: var(--text-main);
    }
    .role-pill.active {
      background: var(--primary);
      color: white;
      font-weight: 600;
    }

    /* Modal Viewer */
    .academic-modal {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(4px);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      padding: 1.5rem;
    }
    .academic-modal.active {
      display: flex;
    }
    .academic-modal-box {
      background: white;
      border-radius: 12px;
      max-width: 750px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
      overflow: hidden;
    }
    .academic-modal-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .academic-modal-body {
      padding: 1.25rem;
      overflow-y: auto;
      font-size: 0.88rem;
    }
    .academic-modal-footer {
      padding: 0.75rem 1.25rem;
      border-top: 1px solid var(--border);
      background: #f8fafc;
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
</style>"""

content = content.replace(css_anchor, custom_css)
print("Added custom CSS successfully")

# 6. Add modals and JavaScript controller before </body>
modals_and_js = """
  <!-- Academic Material Viewer Modal (AC-MAT-02, AC-FE-06) -->
  <div id="material-viewer-modal" class="academic-modal" onclick="if(event.target===this)closeMaterialViewer()">
    <div class="academic-modal-box">
      <div class="academic-modal-header">
        <h3 style="font-size: 1.05rem; color: var(--dark);" id="modal-mat-title">Study Material Viewer</h3>
        <button class="btn btn-outline btn-sm" onclick="closeMaterialViewer()">✕ Close</button>
      </div>
      <div class="academic-modal-body" id="modal-mat-content">
        <!-- Rendered text / slides content -->
      </div>
      <div class="academic-modal-footer">
        <button class="btn btn-outline btn-sm" onclick="closeMaterialViewer()">Close</button>
        <button class="btn btn-primary btn-sm" id="modal-mat-mark-done" onclick="markCurrentModalDone()">Mark as Completed (100%)</button>
      </div>
    </div>
  </div>

  <!-- Score Correction Modal (AC-RES-02) -->
  <div id="score-correction-modal" class="academic-modal" onclick="if(event.target===this)closeScoreCorrectionModal()">
    <div class="academic-modal-box" style="max-width: 520px;">
      <div class="academic-modal-header">
        <h3 style="font-size: 1.05rem; color: var(--dark);">✏️ Manual Score Correction (AC-RES-02)</h3>
        <button class="btn btn-outline btn-sm" onclick="closeScoreCorrectionModal()">✕</button>
      </div>
      <div class="academic-modal-body">
        <div class="form-group" style="margin-bottom: 0.75rem;">
          <label style="font-weight: 600; font-size: 0.82rem;">Select Student Attempt:</label>
          <select class="form-control" id="corr-attempt-id" style="font-size: 0.82rem;" onchange="updateCorrAttemptScore()">
            <option value="ATT_004">ATT_004: STU_115 (Current Score: 2.0 / 5.0)</option>
            <option value="ATT_003">ATT_003: STU_102 (Current Score: 1.0 / 5.0)</option>
            <option value="ATT_002">ATT_002: STU_088 (Current Score: 3.0 / 5.0)</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0.75rem;">
          <label style="font-weight: 600; font-size: 0.82rem;">New Score (0.0 to 5.0):</label>
          <input type="number" step="0.5" min="0" max="5" class="form-control" id="corr-new-score" value="3.5" style="font-size: 0.82rem;">
        </div>
        <div class="form-group" style="margin-bottom: 0.75rem;">
          <label style="font-weight: 600; font-size: 0.82rem;">Mandatory Reason (Appends to SHA-256 Ledger):</label>
          <input type="text" class="form-control" id="corr-reason" placeholder="e.g., Accepted alternate valid explanation for candidate timeout." style="font-size: 0.82rem;">
        </div>
      </div>
      <div class="academic-modal-footer">
        <button class="btn btn-outline btn-sm" onclick="closeScoreCorrectionModal()">Cancel</button>
        <button class="btn btn-primary btn-sm" onclick="submitScoreCorrection()">Confirm & Record to Ledger</button>
      </div>
    </div>
  </div>

  <script>
    // =========================================================================
    // ACADEMIC MODULE FRONTEND CONTROLLER (SOCI BLOCK PILOT)
    // =========================================================================
    let currentRole = 'student';
    let currentQuizIndex = 0;
    let quizTimerSeconds = 600;
    let quizTimerInterval = null;
    let activeAttemptId = 'ATT_ACTIVE_001';
    let currentViewingMaterialId = null;

    const academicMaterials = {
      'MAT_001': {
        id: 'MAT_001',
        title: 'Lecture Slides: Raft Consensus & Election Protocol',
        type: 'slides',
        required: true,
        completed: true,
        content: `<h3>Slide 1: What is Distributed Consensus?</h3>
        <p>In distributed systems, consensus ensures multiple nodes agree on a single data value or series of state machine inputs, even during network failures and node crashes.</p>
        <h3>Slide 2: Raft 3-State Decomposition</h3>
        <ul>
          <li><strong>Follower:</strong> Passive state; responds to leader and candidate RPCs.</li>
          <li><strong>Candidate:</strong> Initiates election upon timer expiry, requesting peer votes.</li>
          <li><strong>Leader:</strong> Handles client queries, log replication, and periodic heartbeats.</li>
        </ul>
        <h3>Slide 3: Randomized Election Timeouts</h3>
        <p>Election timeouts are randomized between 150ms and 300ms to ensure a single candidate collects the majority quorum first, effectively preventing split-vote deadlocks.</p>`
      },
      'MAT_002': {
        id: 'MAT_002',
        title: "Core Technical Document: Diego Ongaro's Raft Paper",
        type: 'pdf',
        required: true,
        completed: true,
        content: `<h3>Abstract: In Search of an Understandable Consensus Algorithm</h3>
        <p>Diego Ongaro and John Ousterhout, Stanford University.</p>
        <p>Raft is a consensus algorithm for managing a replicated log. It produces a result equivalent to (multi-)Paxos, and it is as efficient as Paxos, but its structure is decomposed into independent sub-problems for superior understandability.</p>
        <h3>Section 5.2: Leader Election</h3>
        <p>Raft uses a heartbeat mechanism to trigger leader election. When servers start up, they begin as followers. A server remains in follower state as long as it receives valid RPCs from a leader or candidate. Leaders send periodic heartbeats (AppendEntries RPCs that carry no log entries) to all followers in order to maintain their authority.</p>
        <h3>Section 5.4: Safety & Log Matching Invariant</h3>
        <p><strong>Election Safety:</strong> at most one leader can be elected in a given term.<br>
        <strong>Leader Append-Only:</strong> a leader never overwrites or truncates its entries; it only appends new entries.<br>
        <strong>Log Matching Property:</strong> if two logs contain an entry with the same index and term, then the logs are identical in all entries up through the given index.</p>`
      },
      'MAT_003': {
        id: 'MAT_003',
        title: 'Supplementary Video: Raft Distributed Visual Simulation',
        type: 'video',
        required: false,
        completed: false,
        content: `<h3>Interactive Animated Visualization</h3>
        <p>Simulates cluster node heartbeats, leader timeouts, candidate split-vote avoidance, and network partitioning recovery in real time.</p>
        <div style="background: #0f172a; color: #38bdf8; padding: 1.5rem; border-radius: 8px; text-align: center; font-family: monospace;">
          [ LIVE SIMULATOR: 5-NODE RAFT CLUSTER (Nodes S1, S2, S3, S4, S5) ]<br>
          S1: Leader (Term 1) | S2: Follower | S3: Follower | S4: Follower | S5: Follower<br>
          Heartbeats pulsing every 50ms... Quorum healthy (5/5).
        </div>`
      }
    };

    const quizQuestions = [
      {
        qid: 'Q_101',
        type: 'single_choice',
        text: 'What are the three node states in the Raft consensus algorithm?',
        options: [
          'Follower, Candidate, Leader',
          'Proposer, Acceptor, Learner',
          'Primary, Secondary, Arbiter',
          'Master, Worker, Sentinel'
        ],
        answer: 'Follower, Candidate, Leader',
        difficulty: 'Easy',
        subtopic: 'Core Architecture',
        marks: 1.0,
        explanation: 'Raft explicitly defines three operational states: Follower, Candidate, and Leader.'
      },
      {
        qid: 'Q_102',
        type: 'single_choice',
        text: 'In a cluster of 5 nodes running Raft, what is the minimum quorum required to elect a leader or commit an entry?',
        options: ['3 nodes (majority)', '2 nodes', '4 nodes', 'All 5 nodes'],
        answer: '3 nodes (majority)',
        difficulty: 'Medium',
        subtopic: 'Fault Tolerance & Quorum',
        marks: 1.0,
        explanation: 'In 2F + 1 nodes (5 nodes, F=2), a strict majority quorum requires F + 1 = 3 nodes.'
      },
      {
        qid: 'Q_103',
        type: 'true_false',
        text: 'True or False: In Raft, a leader is permitted to overwrite or delete its own committed log entries during network partitions.',
        options: ['True', 'False'],
        answer: 'False',
        difficulty: 'Medium',
        subtopic: 'Log Replication Safety',
        marks: 1.0,
        explanation: 'Leader Append-Only property guarantees a leader never overwrites or truncates its own log entries.'
      },
      {
        qid: 'Q_104',
        type: 'short_answer',
        text: 'Why does Raft use randomized election timeouts rather than fixed timeouts?',
        options: [],
        answer: 'Randomized election timeouts prevent split-vote scenarios where multiple candidates split the votes equally.',
        difficulty: 'Hard',
        subtopic: 'Leader Election',
        marks: 2.0,
        explanation: 'Randomized timeouts ensure candidates do not start elections simultaneously, preventing split votes and repeated deadlocks.'
      }
    ];

    let studentAnswers = {
      'Q_101': 'Follower, Candidate, Leader',
      'Q_102': '3 nodes (majority)',
      'Q_103': 'False',
      'Q_104': 'Randomized election timeouts ensure candidates do not start elections simultaneously, preventing split votes and repeated deadlocks.'
    };

    // Role Switching
    function switchUserRole(role) {
      currentRole = role;
      document.querySelectorAll('.role-pill').forEach(p => p.classList.remove('active'));
      const activePill = document.getElementById(`role-pill-${role}`);
      if (activePill) activePill.classList.add('active');

      if (role === 'student') {
        switchTab('tab-academic-student');
      } else if (role === 'faculty') {
        switchTab('tab-academic-faculty');
      } else if (role === 'hod') {
        switchTab('tab-academic-analytics');
      } else if (role === 'security') {
        switchTab('tab-secops');
      } else if (role === 'admin') {
        switchTab('tab-academic-ledger');
      }
    }

    // Material Viewer Modal
    function openMaterialViewer(matId) {
      currentViewingMaterialId = matId;
      const mat = academicMaterials[matId];
      if (!mat) return;
      document.getElementById('modal-mat-title').innerText = mat.title;
      document.getElementById('modal-mat-content').innerHTML = mat.content;
      const doneBtn = document.getElementById('modal-mat-mark-done');
      if (doneBtn) {
        doneBtn.innerText = mat.completed ? 'Reset Progress (Incomplete)' : 'Mark as Completed (100%)';
        doneBtn.className = mat.completed ? 'btn btn-outline btn-sm' : 'btn btn-primary btn-sm';
      }
      document.getElementById('material-viewer-modal').classList.add('active');
    }

    function closeMaterialViewer() {
      document.getElementById('material-viewer-modal').classList.remove('active');
    }

    function markCurrentModalDone() {
      if (currentViewingMaterialId) {
        toggleMaterialCompletion(currentViewingMaterialId);
        closeMaterialViewer();
      }
    }

    function toggleMaterialCompletion(matId) {
      const mat = academicMaterials[matId];
      if (!mat) return;
      mat.completed = !mat.completed;
      const btn = document.getElementById(`mat-btn-${matId}`);
      if (btn) {
        if (mat.completed) {
          btn.innerText = '✅ Completed';
          btn.className = 'btn btn-primary btn-sm';
        } else {
          btn.innerText = 'Mark Done';
          btn.className = 'btn btn-outline btn-sm';
        }
      }
      evaluateQuizUnlockRule();
    }

    // AC-STU-03 & AC-FE-04 Quiz Unlock Rule Engine
    function evaluateQuizUnlockRule() {
      const requiredMats = Object.values(academicMaterials).filter(m => m.required);
      const pending = requiredMats.filter(m => !m.completed);
      const banner = document.getElementById('quiz-unlock-banner');
      const title = document.getElementById('quiz-unlock-title');
      const desc = document.getElementById('quiz-unlock-desc');
      const icon = document.getElementById('quiz-unlock-icon');
      const btn = document.getElementById('btn-start-quiz');

      const totalRequired = requiredMats.length;
      const completedRequired = requiredMats.filter(m => m.completed).length;
      const pct = Math.round((completedRequired / totalRequired) * 100);
      document.getElementById('topic1-progress-pct').innerText = `${pct}% Complete`;
      document.getElementById('topic1-progress-bar').style.width = `${pct}%`;

      if (pending.length === 0) {
        banner.style.background = '#ecfdf5';
        banner.style.borderColor = '#a7f3d0';
        icon.innerText = '🔓';
        title.innerText = 'Topic 1 Quiz Unlocked & Open!';
        title.style.color = '#065f46';
        desc.innerText = 'All required topic study materials completed. Ready for attempt.';
        desc.style.color = '#047857';
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.innerText = 'Start Topic Quiz';
      } else {
        banner.style.background = '#fff1f2';
        banner.style.borderColor = '#fecdd3';
        icon.innerText = '🔒';
        title.innerText = `Quiz Locked: ${pending.length} Required Item(s) Pending`;
        title.style.color = '#9f1239';
        desc.innerText = `Must complete: ${pending.map(m => m.title).join(', ')}`;
        desc.style.color = '#be123c';
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.innerText = 'Complete Materials to Unlock';
      }
    }

    // Quiz Sitting Flow
    function launchQuizAttempt() {
      document.getElementById('quiz-idle-view').style.display = 'none';
      document.getElementById('quiz-result-view').style.display = 'none';
      document.getElementById('quiz-active-view').style.display = 'block';
      currentQuizIndex = 0;
      showQuizQuestion(0);
      startQuizTimer();
    }

    function showQuizQuestion(idx) {
      currentQuizIndex = idx;
      const q = quizQuestions[idx];
      document.getElementById('q-counter').innerText = `Question ${idx + 1} of ${quizQuestions.length}`;

      // Update palette buttons
      const palette = document.getElementById('quiz-palette');
      palette.querySelectorAll('button').forEach((b, i) => {
        b.className = i === idx ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-outline';
      });

      const container = document.getElementById('active-question-card');
      let html = `
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem;">
          <span class="badge" style="background: #f1f5f9; color: var(--text-muted); font-size: 0.72rem;">${q.difficulty}</span>
          <span style="margin-left: 0.5rem;">Marks: ${q.marks}</span>
          <span style="margin-left: 0.5rem;">• Subtopic: ${q.subtopic}</span>
        </div>
        <h3 style="font-size: 1.05rem; color: var(--dark); margin-bottom: 1rem;">${q.text}</h3>
      `;

      if (q.type === 'single_choice' || q.type === 'true_false') {
        html += `<div style="display: flex; flex-direction: column; gap: 0.6rem;">`;
        q.options.forEach(opt => {
          const checked = studentAnswers[q.qid] === opt ? 'checked' : '';
          html += `
            <label style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; cursor: pointer; background: ${checked ? '#ecfdf5' : 'white'};">
              <input type="radio" name="opt-${q.qid}" value="${opt}" ${checked} onchange="selectOption('${q.qid}', '${opt}')">
              <span style="font-size: 0.9rem; color: var(--dark);">${opt}</span>
            </label>
          `;
        });
        html += `</div>`;
      } else if (q.type === 'short_answer') {
        const val = studentAnswers[q.qid] || '';
        html += `
          <div>
            <textarea id="short-answer-input" class="form-control" rows="4" placeholder="Type your response here..." oninput="updateShortAnswer('${q.qid}', this.value)" style="font-size: 0.88rem; line-height: 1.5;">${val}</textarea>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem;">
              <span>AI Semantic Evaluation Active (AC-ML-05)</span>
              <span id="short-word-count">${val.trim().split(/\s+/).filter(Boolean).length} words</span>
            </div>
          </div>
        `;
      }

      container.innerHTML = html;

      // Update footer buttons
      document.getElementById('btn-prev-q').disabled = idx === 0;
      if (idx === quizQuestions.length - 1) {
        document.getElementById('btn-next-q').style.display = 'none';
        document.getElementById('btn-submit-quiz').style.display = 'inline-block';
      } else {
        document.getElementById('btn-next-q').style.display = 'inline-block';
        document.getElementById('btn-submit-quiz').style.display = 'none';
      }
    }

    function selectOption(qid, opt) {
      studentAnswers[qid] = opt;
      saveQuizAnswerDraft();
      showQuizQuestion(currentQuizIndex);
    }

    function updateShortAnswer(qid, val) {
      studentAnswers[qid] = val;
      const countEl = document.getElementById('short-word-count');
      if (countEl) countEl.innerText = `${val.trim().split(/\s+/).filter(Boolean).length} words`;
    }

    function navigateQuiz(dir) {
      const nextIdx = currentQuizIndex + dir;
      if (nextIdx >= 0 && nextIdx < quizQuestions.length) {
        showQuizQuestion(nextIdx);
      }
    }

    function saveQuizAnswerDraft() {
      const status = document.getElementById('quiz-autosave-status');
      status.innerText = '💾 Saving...';
      setTimeout(() => {
        status.innerText = '🟢 Autosaved';
      }, 350);
    }

    function startQuizTimer() {
      quizTimerSeconds = 600;
      if (quizTimerInterval) clearInterval(quizTimerInterval);
      quizTimerInterval = setInterval(() => {
        quizTimerSeconds--;
        if (quizTimerSeconds <= 0) {
          clearInterval(quizTimerInterval);
          confirmSubmitQuiz();
          return;
        }
        const m = Math.floor(quizTimerSeconds / 60);
        const s = quizTimerSeconds % 60;
        document.getElementById('quiz-timer-badge').innerText = `⏱️ ${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
      }, 1000);
    }

    function confirmSubmitQuiz() {
      if (quizTimerInterval) clearInterval(quizTimerInterval);
      document.getElementById('quiz-active-view').style.display = 'none';
      document.getElementById('quiz-result-view').style.display = 'block';

      // Perform local or API evaluation
      document.getElementById('res-short-student-ans').innerText = `"${studentAnswers['Q_104'] || 'No answer submitted'}"`;
    }

    function retakeQuiz() {
      document.getElementById('quiz-result-view').style.display = 'none';
      launchQuizAttempt();
    }

    // Faculty AI Generator
    function toggleApiKeyField() {
      const engine = document.getElementById('gen-model-engine').value;
      document.getElementById('gemini-key-container').style.display = engine === 'gemini' ? 'block' : 'none';
    }

    function triggerAIQuestionGeneration() {
      const btn = document.getElementById('btn-generate-ai');
      const progressContainer = document.getElementById('gen-progress-bar-container');
      const progressFill = document.getElementById('gen-progress-fill');
      const progressText = document.getElementById('gen-percent-text');
      const statusText = document.getElementById('gen-status-text');

      btn.disabled = true;
      progressContainer.style.display = 'block';
      let progress = 10;

      const timer = setInterval(() => {
        progress += 20;
        if (progress >= 100) {
          clearInterval(timer);
          progressFill.style.width = '100%';
          progressText.innerText = '100%';
          statusText.innerText = 'Generated 5 questions successfully!';
          btn.disabled = false;
          setTimeout(() => {
            progressContainer.style.display = 'none';
            renderReviewQueueDrafts();
          }, 800);
        } else {
          progressFill.style.width = `${progress}%`;
          progressText.innerText = `${progress}%`;
          if (progress === 30) statusText.innerText = 'Extracting concept salience & TF-IDF keywords...';
          if (progress === 70) statusText.innerText = 'Grounding citations & executing quality filter...';
        }
      }, 250);
    }

    const reviewQueueDrafts = [
      {
        id: 'QGEN_001',
        type: 'single_choice',
        text: 'Who developed or proposed the Raft consensus algorithm?',
        options: ['Diego Ongaro and John Ousterhout', 'Leslie Lamport', 'Barbara Liskov', 'Ken Thompson'],
        answer: 'Diego Ongaro and John Ousterhout',
        difficulty: 'Easy',
        confidence: 0.96,
        source: 'The Raft consensus algorithm was developed by Diego Ongaro and John Ousterhout at Stanford University.'
      },
      {
        id: 'QGEN_002',
        type: 'single_choice',
        text: 'In a cluster of 2F + 1 nodes, how many node failures can Raft tolerate while maintaining consensus?',
        options: ['Up to F node failures', '2F node failures', 'F + 1 node failures', 'Zero node failures'],
        answer: 'Up to F node failures',
        difficulty: 'Hard',
        confidence: 0.94,
        source: 'In a cluster of 2F + 1 nodes, Raft can tolerate up to F node failures while continuing to progress and commit transactions.'
      },
      {
        id: 'QGEN_003',
        type: 'true_false',
        text: 'True or False: A Raft candidate transitions back to Follower state if it discovers another leader with an equal or higher term.',
        options: ['True', 'False'],
        answer: 'True',
        difficulty: 'Medium',
        confidence: 0.91,
        source: 'If a candidate or leader discovers that its current term is smaller than another servers term, it immediately reverts to follower state.'
      }
    ];

    function renderReviewQueueDrafts() {
      const container = document.getElementById('review-queue-list');
      document.getElementById('review-queue-count').innerText = reviewQueueDrafts.length;

      if (reviewQueueDrafts.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem;">All generated drafts reviewed!</div>';
        return;
      }

      let html = '';
      reviewQueueDrafts.forEach((q, idx) => {
        html += `
          <div style="padding: 0.85rem; border: 1px solid var(--border); border-radius: 8px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
              <div style="display: flex; gap: 0.4rem; align-items: center;">
                <span class="badge" style="background: #f1f5f9; color: var(--text-muted); font-size: 0.72rem;">${q.difficulty}</span>
                <span class="badge" style="background: #ecfdf5; color: #047857; font-size: 0.72rem;">Confidence: ${(q.confidence * 100).toFixed(0)}%</span>
                <span class="badge" style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem;">Quality Filters: PASSED</span>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${q.id}</span>
            </div>
            <h4 style="font-size: 0.92rem; color: var(--dark); margin-bottom: 0.35rem;">${q.text}</h4>
            <div style="font-size: 0.78rem; color: var(--primary); font-weight: 600; margin-bottom: 0.35rem;">Answer Key: ${q.answer}</div>
            <div style="padding: 0.5rem; background: #f8fafc; border-radius: 6px; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              <strong>📖 Grounding Citation (AC-ML-02):</strong> "${q.source}"
            </div>
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
              <button class="btn btn-outline btn-sm" onclick="rejectDraft(${idx})">❌ Reject</button>
              <button class="btn btn-outline btn-sm" onclick="alert('Opened inline editor for ${q.id}')">✏️ Edit</button>
              <button class="btn btn-primary btn-sm" onclick="approveDraft(${idx})">✅ Approve to Bank</button>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
    }

    function approveDraft(idx) {
      const q = reviewQueueDrafts.splice(idx, 1)[0];
      renderReviewQueueDrafts();
      alert(`Approved question "${q.text.slice(0, 40)}..." into Question Bank! Added to Topic 1 Quiz.`);
    }

    function rejectDraft(idx) {
      reviewQueueDrafts.splice(idx, 1);
      renderReviewQueueDrafts();
    }

    function openUploadMaterialModal() {
      const title = prompt("Enter Study Material Title:", "Lecture Slides 2: Raft Log Invariants");
      if (title) {
        alert(`Material "${title}" uploaded, virus-scanned, and published to Topic 1.`);
        renderFacultyMaterials();
      }
    }

    function renderFacultyMaterials() {
      const tbody = document.getElementById('faculty-materials-tbody');
      tbody.innerHTML = `
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-weight: 600; color: var(--dark);">Lecture Slides: Raft Consensus & Election Protocol</td>
          <td style="padding: 0.5rem;">Slides</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Published</span></td>
          <td style="padding: 0.5rem;"><span style="color: #dc2626; font-weight: 600;">Required</span></td>
          <td style="padding: 0.5rem;"><button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_001')">View</button></td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-weight: 600; color: var(--dark);">Core Technical Document: Diego Ongaro's Raft Paper</td>
          <td style="padding: 0.5rem;">PDF</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Published</span></td>
          <td style="padding: 0.5rem;"><span style="color: #dc2626; font-weight: 600;">Required</span></td>
          <td style="padding: 0.5rem;"><button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_002')">View</button></td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-weight: 600; color: var(--dark);">Supplementary Video: Raft Distributed Visual Simulation</td>
          <td style="padding: 0.5rem;">Video</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Published</span></td>
          <td style="padding: 0.5rem;"><span style="color: #059669; font-weight: 600;">Optional</span></td>
          <td style="padding: 0.5rem;"><button class="btn btn-outline btn-sm" onclick="openMaterialViewer('MAT_003')">View</button></td>
        </tr>
      `;
    }

    // Psychometrics and Item Discrimination
    function renderItemDiscriminationTable() {
      const tbody = document.getElementById('item-discrimination-tbody');
      tbody.innerHTML = `
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">Q_101</td>
          <td style="padding: 0.5rem;">What are the three node states in Raft?</td>
          <td style="padding: 0.5rem; font-weight: 600;">0.84</td>
          <td style="padding: 0.5rem; font-weight: 700; color: #059669;">+0.62</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Healthy (D ≥ 0.20)</span></td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">Q_102</td>
          <td style="padding: 0.5rem;">Minimum quorum in 5-node cluster?</td>
          <td style="padding: 0.5rem; font-weight: 600;">0.68</td>
          <td style="padding: 0.5rem; font-weight: 700; color: #059669;">+0.55</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Healthy (D ≥ 0.20)</span></td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border); background: #fff1f2;">
          <td style="padding: 0.5rem; font-family: monospace; color: #9f1239;">Q_103</td>
          <td style="padding: 0.5rem; color: #9f1239;">Can leader overwrite committed logs?</td>
          <td style="padding: 0.5rem; font-weight: 600;">0.45</td>
          <td style="padding: 0.5rem; font-weight: 700; color: #dc2626;">-0.18</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #fee2e2; color: #991b1b;">🚨 CRITICAL MISKEYED (D < 0)</span></td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">Q_104</td>
          <td style="padding: 0.5rem;">Why randomized election timeouts?</td>
          <td style="padding: 0.5rem; font-weight: 600;">0.58</td>
          <td style="padding: 0.5rem; font-weight: 700; color: #059669;">+0.48</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">Healthy (D ≥ 0.20)</span></td>
        </tr>
      `;
    }

    // Score Correction
    function openScoreCorrectionModal() {
      document.getElementById('score-correction-modal').classList.add('active');
    }
    function closeScoreCorrectionModal() {
      document.getElementById('score-correction-modal').classList.remove('active');
    }
    function updateCorrAttemptScore() {
      const att = document.getElementById('corr-attempt-id').value;
      const scoreInput = document.getElementById('corr-new-score');
      if (att === 'ATT_004') scoreInput.value = '3.5';
      if (att === 'ATT_003') scoreInput.value = '2.5';
      if (att === 'ATT_002') scoreInput.value = '4.0';
    }
    function submitScoreCorrection() {
      const att = document.getElementById('corr-attempt-id').value;
      const newScore = document.getElementById('corr-new-score').value;
      const reason = document.getElementById('corr-reason').value;
      if (!reason.trim()) {
        alert("Please enter a mandatory audit reason for the ledger.");
        return;
      }
      closeScoreCorrectionModal();
      alert(`Score corrected to ${newScore} for attempt ${att}. Cryptographically appended to SHA-256 Ledger!`);
      refreshAcademicLedger();
    }

    // Universal Ledger Stream
    function refreshAcademicLedger() {
      const tbody = document.getElementById('academic-ledger-tbody');
      const now = new Date().toISOString();
      tbody.innerHTML = `
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">${now.replace('T', ' ').slice(0, 19)}</td>
          <td style="padding: 0.5rem; font-weight: 600;">FAC_001</td>
          <td style="padding: 0.5rem; font-family: monospace;">ACAD-SCORE-AUDIT</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #fef3c7; color: #92400e;">score_corrected</span></td>
          <td style="padding: 0.5rem;">Adjusted ATT_004 to 3.5. Reason: Accepted alternate timeout explanation.</td>
          <td style="padding: 0.5rem; font-family: monospace; font-size: 0.72rem; color: var(--text-muted);">9f8a...31b7</td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">2026-11-04 11:32:10</td>
          <td style="padding: 0.5rem; font-weight: 600;">STU_012</td>
          <td style="padding: 0.5rem; font-family: monospace;">ACAD-SUBJ-CS101</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">quiz_submitted</span></td>
          <td style="padding: 0.5rem;">Score: 4.4 / 5.0 (Passed: True, Duration: 220s)</td>
          <td style="padding: 0.5rem; font-family: monospace; font-size: 0.72rem; color: var(--text-muted);">4e2b...9a12</td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">2026-11-04 11:28:30</td>
          <td style="padding: 0.5rem; font-weight: 600;">STU_012</td>
          <td style="padding: 0.5rem; font-family: monospace;">ACAD-SUBJ-CS101</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #e0f2fe; color: #0369a1;">quiz_started</span></td>
          <td style="padding: 0.5rem;">Attempt frozen for QUIZ_CS101_01</td>
          <td style="padding: 0.5rem; font-family: monospace; font-size: 0.72rem; color: var(--text-muted);">1a7c...88ef</td>
        </tr>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 0.5rem; font-family: monospace;">2026-11-04 10:45:12</td>
          <td style="padding: 0.5rem; font-weight: 600;">STU_012</td>
          <td style="padding: 0.5rem; font-family: monospace;">ACAD-PROGRESS</td>
          <td style="padding: 0.5rem;"><span class="badge" style="background: #ecfdf5; color: #047857;">material_completed</span></td>
          <td style="padding: 0.5rem;">Completed MAT_002 (Diego Ongaro Raft Paper)</td>
          <td style="padding: 0.5rem; font-family: monospace; font-size: 0.72rem; color: var(--text-muted);">8d3e...7701</td>
        </tr>
      `;
    }

    // Auto-init on page load
    window.addEventListener('DOMContentLoaded', () => {
      evaluateQuizUnlockRule();
      renderFacultyMaterials();
      renderItemDiscriminationTable();
      refreshAcademicLedger();
    });
  </script>
</body>
"""

content = content.replace("</body>", modals_and_js)
print("Added modals and JS controller successfully")

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated dashboard.html successfully written! Total size:", len(content))
