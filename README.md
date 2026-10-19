# Network Intrusion Detection System (NIDS) — "RADAR WATCHTOWER"

### Department of Computer Science, University of Nigeria, Nsukka (UNN)
**Design and Implementation of a Network Intrusion Detection System Using Random Forest Machine Learning Algorithm**  
*Project Supervisor*: Dr. U.K Umeh | *Academic Year*: 2026

---

## Quick Start

### 1. Launch the System
```powershell
cd "c:\Users\Dell\Desktop\NIDS Project\nids"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train_model.py
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 2. Default Operator Credentials
- **Username**: `admin`
- **Initial Password**: `NidsAdmin2026!`
- *(Mandatory password rotation policy enforced on initial authentication).*

### 3. Run Automated End-to-End Test Suite (T1 - T17)
```powershell
python test_suite.py
```
*(All 17 security, classification, batch processing, and persistence tests execute with a 100% pass rate).*

---

## Architectural & Visual Concept

The user interface is designed as the **"RADAR WATCHTOWER"** — an air traffic control room for real-time network traffic defense:

- **[01 // WATCH]**: Fullscreen control room featuring a 60 FPS central canvas radar with concentric range rings (TCP, UDP, ICMP), rotating sweep beam, particle blips (cyan normal, coral attack with shockwaves), character-by-character SIGNAL FEED, 5-segment THREAT LEVEL meter, rolling odometers, industrial rocker switch, and an ECG-style PULSE heat-strip.
- **[02 // INSPECT]**: 41-feature specimen scanner with laser scanline animations, benchmark specimen preloaders, and impact verdict stamps with self-drawing confidence rings.
- **[03 // BATCH]**: Drag-and-drop CSV scanner bay displaying results as an animated micro-tile mosaic array.
- **[04 // ARCHIVE]**: Historical telemetry flight departure board with search, filter chips, and split-flap row animations.
- **ACCESS GATE**: Terminal login with faint background radar sweep and boot sequence typing diagnostics.
- **Visual Design**: Dark Tactical (`#070B12`) and Day Technical Paper (`#F1ECE0`) modes with self-hosted `Barlow Condensed` and `JetBrains Mono` fonts. Zero external CDN dependencies.

For complete documentation, security policies, test details, and screenshots inventory, see the comprehensive [nids/README.md](file:///c:/Users/Dell/Desktop/NIDS%20Project/nids/README.md).
