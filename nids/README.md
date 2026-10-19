# Network Intrusion Detection System (NIDS) — "RADAR WATCHTOWER"

### Department of Computer Science, University of Nigeria, Nsukka (UNN)
**Design and Implementation of a Network Intrusion Detection System Using Random Forest Machine Learning Algorithm**  
*Project Supervisor*: Dr. U.K Umeh | *Academic Year*: 2026

---

## 1. Overview & Concept: "RADAR WATCHTOWER"

This application provides real-time network traffic classification, batch CSV packet inspection, and threat monitoring using an ensemble **Random Forest Classifier** trained on the benchmark **NSL-KDD** dataset (`KDDTrain+` and `KDDTest+`).

Rather than adopting a generic dashboard design, this system is modeled as the **"RADAR WATCHTOWER"** — an air traffic control room for live network telemetry. The product operates as an interactive, real-time tactical instrument rather than a static reporting sheet.

### Key Visual & Architectural Highlights:
- **100% Offline Runtime**: Zero CDN dependencies. Self-hosted fonts and assets enable offline operation on air-gapped network defense infrastructure.
- **Custom HTML5 Canvas & SVG Visualizations**: Generic charts and Chart.js have been completely replaced with custom 60 FPS HTML5 Canvas radar sweeps, particle blips, ECG pulse heat-strips, and SVG telemetry gauges.
- **Self-Hosted Typography**:
  - `Barlow Condensed` (Bold, Uppercase, Wide Tracking) for telemetry headings, threat meters, and verdict stamps.
  - `JetBrains Mono` for packet vectors, terminal signal logs, odometer digits, and timestamps.
- **Dual High-Contrast Themes**:
  - **Dark Tactical (Default)**: `#070B12` void background with tactical grid overlay, CRT scanlines, `#0D1422` translucent panels with 1px `#1E2A40` borders and amber corner brackets. Amber `#FFB020` primary signal accents, Cyan `#4FD1C5` benign traffic, and Coral `#FF4D5E` threat alerts.
  - **Day Technical Paper**: Warm paper `#F1ECE0` with sharp ink borders `#1A1F2B`, preserving amber and coral indicators to resemble a precision printed aviation radar chart.
- **Hardware-Inspired Controls**: Industrial physical rocker switch with status lamp, sliding signature drawer, terminal boot sequences, and flight departure board logs.

---

## 2. Default Administrative Credentials

> **Important**: In compliance with security policy standards, administrative credentials are documented strictly here and never displayed within the user interface.

- **Username**: `admin`
- **Initial Password**: `NidsAdmin2026!`
- **Enforced Security Policy**: Upon first authentication, the system forces a mandatory redirect to the **Cryptographic Credential Rotation** screen. Monitoring views and APIs remain inaccessible until a new compliant password (minimum 8 characters, at least one numeric digit, differing from default) is established.

---

## 3. Operational Instrument Screens

### [01 // WATCH] — Air Traffic Control Room (Live Monitoring)
- **Central Canvas Radar**: Concentric range rings demarcated into **TCP (Core)**, **UDP (Mid-Range)**, and **ICMP (Perimeter)** with $360^\circ$ azimuth markings. A golden amber sweep beam rotates smoothly at 60 FPS.
  - **Packet Blips**: Angle is dynamically hashed from the service name ($0^\circ$ to $360^\circ$); radius corresponds to protocol type.
  - **Benign Blips**: Small cool cyan dots fading gradually.
  - **Attack Blips**: Enlarged coral pulses with expanding shockwave ripple rings, comet trails, and an 8-second persistence window.
  - **Hover HUD**: Tooltip detailing service, protocol, classification label, confidence score, and timestamp.
- **Left Panel — "SIGNAL FEED"**: Translucent terminal log typing incoming packet records character-by-character. Malicious lines flash coral with an animated status marker (capped at 25 lines).
- **Right Panel — "THREAT LEVEL" & Odometers**: Vertical 5-segment meter (**CALM**, **WATCH**, **ELEVATED**, **HIGH**, **CRITICAL**) driven by the attack rate over the last 20 records. Accompanied by large rolling odometer counters for observed records, intercepted attacks, attack percentage, and an SVG model confidence gauge.
- **Center Pod — Industrial Rocker Switch**: Physical rocker toggle with an LED status lamp (`ENGAGE SWEEP` / `STANDBY (STOP)`).
- **Bottom Strip — "PULSE" ECG Heat-Strip & Ticker Tape**: Scrolling canvas drawing the last 120 packets as vertical confidence bars alongside a real-time attack ticker tape.
- **Slide-out "SIGNATURE" Panel**: Right-side drawer revealing the top NSL-KDD Gini feature importances rendered as horizontal amber scan lines.
- **Tactical Alarm**: Red vignette screen-edge flash and optional synthesized Web Audio API sonar pings and hostile sirens.

### [02 // INSPECT] — Specimen Scanner (Manual Packet Classification)
- 41 NSL-KDD telemetry attributes organized inside a bracketed tactical panel across four sectors: Basic Connection Features, Content & Payload Features, Time-Based Traffic Features, and Host-Based Traffic Features.
- Quick preload tabs: `[ LOAD BENIGN SAMPLE ]` and `[ LOAD ATTACK SAMPLE ]`.
- Laser sweep scanline animation traversing the specimen matrix on submission.
- Heavy impact verdict stamp (`MALICIOUS THREAT DETECTED` or `BENIGN NETWORK TRAFFIC`) accompanied by a self-drawing animated confidence ring.

### [03 // BATCH] — Batch Scanner Bay (Bulk CSV Classification)
- Scanner bay dropzone supporting drag-and-drop CSV uploads (up to 5 MB).
- Real-time progress bar tracking vector ingestion and Random Forest inference.
- Results bay featuring an interactive micro-square tile mosaic (cyan normal, coral attack) populating sequentially alongside breakdown odometers.

### [04 // ARCHIVE] — Flight Departure Board (Historical Audit Trail)
- Dense historical log structured like an airport flight departure board with monospace typography and split-flap row loading animations.
- Real-time search by service or protocol, instant filter chips (`[ ALL TRAFFIC ]`, `[ BENIGN ONLY ]`, `[ THREATS ONLY ]`), and sector pagination.

### Access Gate (Terminal Login & Credential Rotation)
- Fullscreen terminal gateway with faint background canvas radar sweep.
- Animated boot sequence:
  ```text
  > Initialising Random Forest model... OK
  > Loading NSL-KDD signatures... OK
  > Awaiting operator credentials
  ```
- UNN Crest and institutional motto: *"To Restore the Dignity of Man"*.
- Strict rate-limiting lockout (5 failed attempts within 15 minutes trigger an HTTP 429 response with a live countdown timer in monospace digits).

---

## 4. Windows Installation & Setup Guide

### Step 1: Open PowerShell or Terminal
```powershell
cd "c:\Users\Dell\Desktop\NIDS Project\nids"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 3: Install Locked Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Train Machine Learning Model (NSL-KDD)
Train the Random Forest pipeline on the benchmark dataset:
```powershell
python train_model.py
```
This generates:
- `model/rf_model.joblib`: Compressed `ColumnTransformer` + `RandomForestClassifier` pipeline.
- `model/metrics.json`: Accuracy ($77.28\%$), precision, recall, F1, false positive rate, confusion matrix.
- `model/feature_importance.json`: Top 15 ranked Gini feature importances.
- `data/traffic_log.csv`: 500 sampled vectors for real-time live monitoring.
- `data/sample_upload.csv`: 20 sampled vectors for batch upload verification.
- `nids.db`: SQLite database seeded with default admin credentials.

### Step 5: Start the Web Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. Security & Defense Architecture

1. **Anti-Autofill Enforcement**: `autocomplete="off"` and `autocomplete="new-password"` combined with client-side cache purging on `pageshow` ensure credentials are never cached by browsers.
2. **Back-Button Invalidation**: Strict response headers (`Cache-Control: no-store, no-cache, must-revalidate` and `Pragma: no-cache`) ensure unauthorized operators cannot navigate back into active sessions after logout.
3. **Brute-Force Lockout Defense**: 5 failed login attempts for any username or IP trigger an HTTP 429 response with a dynamic countdown timer in monospace digits.
4. **Mandatory Credential Rotation**: Forced initial password reset prior to accessing operational monitoring routes.
5. **Idle Session Invalidation**: Automatic 20-minute idle session timeout.
6. **Strict Schema & Vector Validation**: Missing or malformed features in manual prediction or CSV uploads trigger explicit HTTP 422 responses.
7. **CSRF Protection**: Token validation on all mutable endpoints.

---

## 6. Comprehensive Verification Test Suite

The automated test suite evaluates all 17 security, operational, and classification flows:

```powershell
python test_suite.py
```

### Test Suite Execution Results:
| Test ID | Test Category | Description | Status |
| :--- | :--- | :--- | :--- |
| **T1** | Authentication | Valid administrative authentication and redirect | **PASS** |
| **T2** | Authentication | Generic error returned on incorrect credentials | **PASS** |
| **T3** | Access Control | Unauthenticated access rejected with 401 / redirect | **PASS** |
| **T4** | Telemetry Stream | Real-time packet simulation stream returns valid record | **PASS** |
| **T5** | Inference Engine | Known normal benchmark vector classified as Normal | **PASS** |
| **T6** | Inference Engine | Known attack benchmark vector classified as Attack | **PASS** |
| **T7** | Probability Metric | Prediction confidence bounded in $[0.0, 1.0]$ | **PASS** |
| **T8** | Schema Validation | Missing required feature attributes rejected with 422 | **PASS** |
| **T9** | Batch Processing | CSV missing required column schema rejected with 422 | **PASS** |
| **T10** | Batch Processing | Valid 20-row CSV processed (16 normal, 4 attacks) | **PASS** |
| **T11** | Audit Persistence | Single inference appends exactly 1 database row | **PASS** |
| **T12** | Audit Persistence | Historical departure board returns newest first | **PASS** |
| **T13** | Model Robustness | Unseen service tokens handled safely without error | **PASS** |
| **T14** | Session Security | Session purged, no-store headers prevent Back navigation | **PASS** |
| **T15** | Rate Limiting | 5 failed attempts trigger HTTP 429 lockout | **PASS** |
| **T16** | Credential Policy | Forced password change locks routes until fulfilled | **PASS** |
| **T17** | Session Timeout | 20-minute idle inactivity terminates session | **PASS** |

**Summary**: 17 / 17 Tests Passed ($100\%$ Success Rate).

---

## 7. Project File Structure

```
nids/
├── app.py                      # Main Flask application and RESTful API endpoints
├── train_model.py              # NSL-KDD machine learning training pipeline
├── database.py                 # SQLite database schema, queries, and admin seeding
├── preprocessing.py            # NSL-KDD 43-column schema, transformations, and validation
├── test_suite.py               # Automated end-to-end verification suite (T1 - T17)
├── capture_screenshots.py      # Automated headless screenshot generator
├── requirements.txt            # Python dependencies (Flask, scikit-learn, pandas, numpy)
├── README.md                   # Detailed project documentation
├── .gitignore                  # Git ignore rules (venv, *.db, cache)
├── data/
│   ├── KDDTrain+.txt           # NSL-KDD training partition (125,973 samples)
│   ├── KDDTest+.txt            # NSL-KDD testing partition (22,544 samples)
│   ├── traffic_log.csv         # 500 sampled rows for real-time sweep simulation
│   └── sample_upload.csv       # 20 sampled rows for testing batch uploads
├── model/
│   ├── rf_model.joblib         # Serialized Random Forest Pipeline
│   ├── metrics.json            # Model evaluation metrics & confusion matrix
│   └── feature_importance.json # Top 15 Gini feature importances
├── templates/
│   ├── base.html               # Master Watchtower layout with topbar, clock & audio
│   ├── login.html              # Fullscreen terminal access gate with boot sequence
│   ├── change_password.html    # Mandatory credential rotation interface
│   ├── dashboard.html          # Air traffic control room with central radar canvas
│   ├── predict.html            # 41-feature specimen scanner with laser scanline
│   ├── upload.html             # Scanner bay dropzone & square tile mosaic
│   └── history.html            # Flight departure board telemetry audit table
├── static/
│   ├── unn-logo.png            # Official University of Nigeria, Nsukka crest
│   ├── css/
│   │   ├── fonts.css           # Self-hosted @font-face declarations
│   │   └── style.css           # Radar Watchtower design system (Dark & Day themes)
│   ├── js/
│   │   ├── main.js             # Live UTC clock, theme switcher & Web Audio synthesizer
│   │   ├── dashboard.js        # 60 FPS Canvas radar, signal feed, threat meter, pulse
│   │   ├── predict.js          # Specimen form validation, laser scan, verdict stamp
│   │   ├── upload.js           # CSV drag-and-drop, progress sweep, mosaic generator
│   │   └── history.js          # Flight departure board table, split-flap row animations
│   └── fonts/
│       ├── BarlowCondensed-*   # Self-hosted Barlow Condensed woff2 files
│       └── JetBrainsMono-*     # Self-hosted JetBrains Mono woff2 files
└── screenshots/                # Visual artifact captures in Dark, Day, and Mobile modes
```

---

## 8. Visual Artifacts & Screenshots

High-resolution captures are maintained in both [`screenshots/`](file:///c:/Users/Dell/Desktop/NIDS%20Project/screenshots) and [`nids/screenshots/`](file:///c:/Users/Dell/Desktop/NIDS%20Project/nids/screenshots):

| View | Mode / Resolution | Description |
| :--- | :--- | :--- |
| `dashboard_dark.png` | Dark Tactical / 1440px | Air traffic control room with active radar, signal feed, and threat meter |
| `dashboard_light.png` | Day Paper / 1440px | Technical warm paper radar chart with ink lines and sepia beam |
| `dashboard_mobile_375.png` | Dark / 375px Mobile | Responsive mobile stack: radar on top, stacked signal feed & threat meter |
| `predict_dark.png` | Dark Tactical / 1440px | 41-feature specimen scanner with sector brackets and sample loaders |
| `predict_light.png` | Day Paper / 1440px | Specimen scanner in high-contrast technical day paper mode |
| `upload_dark.png` | Dark Tactical / 1440px | Batch scanner bay with CSV dropzone and progress sweep |
| `upload_light.png` | Day Paper / 1440px | Batch scanner bay in day paper mode |
| `history_dark.png` | Dark Tactical / 1440px | Flight departure board table with coral threat highlights and chips |
| `history_light.png` | Day Paper / 1440px | Flight departure board in technical day paper mode |
| `login_dark.png` | Dark Tactical / 1440px | Terminal access gate with boot sequence and faint background radar |
| `login_light.png` | Day Paper / 1440px | Terminal access gate in technical day paper mode |

To re-capture all views automatically:
```powershell
python capture_screenshots.py
```

---

## 9. Institutional Attribution

**University of Nigeria, Nsukka (UNN)**  
**Faculty of Physical Sciences**  
**Department of Computer Science**  
*Motto*: *"To Restore the Dignity of Man"*  
*Project Supervisor*: Dr. U.K Umeh  
*Academic Year*: 2026
