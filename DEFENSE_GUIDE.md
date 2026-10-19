# NIDS Project Defense Master Guide

### Department of Computer Science • University of Nigeria, Nsukka (UNN)
**Project Title**: *Design and Implementation of a Network Intrusion Detection System Using Random Forest Machine Learning Algorithm*  
**Candidate**: Okafor Ugochukwu Stanley (Reg No: `2022/249519`)  
**Group**: Group 2 (Okafor Michael Osinachi, Okafor Ugochukwu Stanley, Okechukwu Daniel Somtochukwu)  
**Supervisor**: Dr. U.K Umeh | **Academic Year**: 2026  
**Word Doc Version**: `NIDS_Project_Defense_Master_Guide.docx`

---

## 1. The 2-Minute Opening Pitch

> *"Good morning, distinguished panel of examiners. My name is **Okafor Ugochukwu Stanley**, presenting on behalf of Group 2. Our project is titled: **Design and Implementation of a Network Intrusion Detection System (NIDS) Using Random Forest Machine Learning Algorithm**, supervised by **Dr. U.K. Umeh**.*
>
> *Traditional perimeter firewalls rely on static signatures and static port rules. The moment an attacker modifies packet payloads or executes a zero-day exploit, rule-based defenses go blind.*
>
> *To solve this, we engineered an intelligent, anomaly-based NIDS powered by an ensemble **Random Forest classifier**. We trained our system on the benchmark **NSL-KDD dataset** across 41 network connection attributes, capturing protocol behaviors, byte exchange rates, and host-level traffic patterns.*
>
> *We then operationalized the machine learning pipeline into a web security operations center—**RADAR WATCHTOWER**—featuring live stream simulation, single-connection diagnosis, automated batch CSV classification, and tamper-resistant audit logging.*
>
> *With your permission, I would like to demonstrate how the system identifies and isolates network intrusions in real time."*

---

## 2. Key Numbers & Metrics (Commit to Memory)

| Parameter / Metric | Exact Value | Defense Significance & Explanation |
| :--- | :--- | :--- |
| **Benchmark Dataset** | **NSL-KDD** | 125,973 training packets (`KDDTrain+`), 22,544 test packets (`KDDTest+`). |
| **Model Architecture** | **Random Forest (`n_estimators=100`)** | 100 Decision Trees with `ColumnTransformer` & `OrdinalEncoder`. |
| **Test Precision** | **96.68%** | **Crucial:** When an intrusion alert triggers, it is 96.7% accurate. Virtually zero false alarms. |
| **False Positive Rate** | **2.82%** | Only 274 normal connections out of 9,711 were misclassified. |
| **Test Accuracy** | **77.28%** | Evaluated on official `KDDTest+`, which contains 17 novel zero-day attacks not in train data. |
| **Test Recall** | **62.23%** | Broad detection capability across known attacks and brand new test variants. |
| **F1-Score** | **75.72%** | Harmonic mean balancing precision and recall on the hardest benchmark test set. |
| **Top Discriminant Features** | `src_bytes` (18.5%), `flag` (13.1%), `dst_bytes` (9.9%) | Payload sizes and TCP connection flags drive over 41% of the model's predictive power. |

---

## 3. Step-by-Step Live Demo Script

### Step 1: Security & Authentication
- **Action**: Open `http://127.0.0.1:5000/login`.
- **Say**: *"We implemented OWASP authentication best practices. Passwords use PBKDF2 hashing with SHA-256 and salt. After 5 consecutive failed attempts, the system enforces a 15-minute brute-force lockout."*
- **Action**: Log in with your admin credentials.

### Step 2: RADAR Operations Dashboard
- **Action**: Point to the KPI cards and charts on `/dashboard`.
- **Say**: *"The dashboard provides the network administrator with real-time situational awareness: total monitored packets, attack vs normal distribution, and live Chart.js threat curves. The system runs an asynchronous traffic simulator simulating real-world gateway throughput."*

### Step 3: Single Packet Live Diagnosis (Show-Stopper)
- **Action**: Navigate to **Manual Predict** (`/predict`).
- **Action**: Click the preset **"Normal HTTP Traffic"** and analyze.
- **Say**: *"Here, standard TCP 3-way handshake with SF flag and high destination bytes results in a clean NORMAL verdict."*
- **Action**: Click the preset **"DoS SYN Flood Attack"** and analyze.
- **Say**: *"Notice that destination bytes drop to 0, status flag becomes S0 (SYN sent, no ACK), and same-host connection rates spike. The Random Forest instantly flags this as an INTRUSION with 99% probability."*

### Step 4: Batch CSV Packet Ingestion
- **Action**: Navigate to **Batch Upload** (`/upload`).
- **Action**: Drag and drop `nids/data/sample_upload.csv` and submit.
- **Say**: *"In enterprise deployments, thousands of packets are ingested in bulk. Our batch pipeline vectorizes 41 features per row, executes high-speed inference, assigns threat risk levels, and updates the database."*

### Step 5: Forensic Audit Logs & Export
- **Action**: Navigate to **History** (`/history`).
- **Say**: *"Every verdict is timestamped and logged with its complete feature vector for forensic analysis. The administrator can filter by classification status or export the audit trail directly to CSV."*

---

## 4. The 8 Tough Defense Questions & Winning Answers

### Q1: Why did you choose Random Forest over Deep Learning (CNN/LSTM) or Logistic Regression?
> *"Sir/Ma, we evaluated that trade-off carefully:*  
> *1) **Logistic Regression** is a linear model that fails to capture complex non-linear interactions across 41 network attributes.*  
> *2) **Deep Learning** models act as black boxes, require GPU compute, and exhibit inference latency too high for packet inspection at line speed.*  
> *3) **Random Forest** is an ensemble of decision trees using bagging (bootstrap aggregation). It natively handles mixed continuous and categorical data, resists overfitting, provides transparent feature importance (Explainable AI), and executes predictions in under 2 milliseconds on commodity CPU hardware."*

---

### Q2: Isn't 77% accuracy too low for machine learning?
> *"That is an insightful question, Sir. In academic literature, papers reporting 98% or 99% accuracy on KDD typically perform a random split on `KDDTrain+`, which creates severe data leakage.*  
> *Our research evaluated the model against the official, standardized **`KDDTest+`** benchmark. `KDDTest+` was intentionally designed by cybersecurity researchers to contain **17 novel zero-day attack variants** (such as `mscan`, `udpstorm`, and `ps`) that never appeared in the training set.*  
> *In network security, **Precision (96.68%)** and **False Positive Rate (2.82%)** are vastly more critical than raw accuracy. Our system ensures legitimate network traffic is virtually never blocked, and any triggered alert represents a high-probability security incident."*

---

### Q3: How is this NIDS different from a standard Firewall?
> *"A **Firewall** acts as a security guard checking static ID badges at the door—filtering based on static IP addresses, port numbers, or protocol types. If malicious traffic is disguised over port 80 (HTTP) or port 443 (HTTPS), the firewall allows it through.*  
> *Our **NIDS** functions like a security camera with behavioral analysis inside the building. It inspects packet dynamics, payload byte ratios, error rates, and connection frequency to detect malicious behavior regardless of which port or address the traffic originates from."*

---

### Q4: How does your pipeline handle categorical text features like `protocol_type` or `service`?
> *"We built a Scikit-Learn `Pipeline` integrating a `ColumnTransformer`. Categorical features—`protocol_type`, `service`, and `flag`—are encoded using an `OrdinalEncoder` with `handle_unknown='use_encoded_value'` set to `-1`.*  
> *This guarantees that if the system encounters an unmapped service during live inspection, the application will not crash; it assigns a fallback token and completes classification safely."*

---

### Q5: What are the most important features that identify an intrusion?
> *"According to Gini impurity feature importance derived from our 100 decision trees:*  
> *1) **`src_bytes` (18.53%)**: Source-to-destination payload bytes. Abnormal surges or zero-byte anomalies are typical of DoS and scanning attacks.*  
> *2) **`flag` (13.14%)**: TCP connection status flags. Normal traffic establishes connection (`SF`), whereas SYN floods or port scans leave connections half-open (`S0` or `REJ`).*  
> *3) **`dst_bytes` (9.91%)**: Destination-to-source bytes.*  
> *Together, these top features drive over 41% of the model's predictive capability."*

---

### Q6: What happens if the database locks or network connection drops?
> *"Our system decouples model inference from database persistence. The Random Forest model (`rf_model.joblib`) is deserialized into server RAM upon application startup. Real-time classification executes completely in-memory.*  
> *Furthermore, all web assets—fonts, icons, and Chart.js—are bundled locally. The application can run entirely offline in an air-gapped security operations center without external internet dependencies."*

---

### Q7: How did you test and validate the system before deployment?
> *"We authored an automated test suite containing 17 comprehensive test cases (`test_suite.py`) spanning unit testing, database CRUD integrity, authentication lockouts, single and batch ML inference, and edge-case payload validation. All 17 tests execute with a 100% pass rate."*

---

### Q8: What was YOUR specific personal contribution to this project?
> *"As a core member of Group 2, my contributions centered on:*  
> *1) Constructing the machine learning preprocessing and training pipeline on the NSL-KDD dataset.*  
> *2) Developing the Flask backend architecture, database schema, and OWASP security controls.*  
> *3) Engineering the operations dashboard interface and automating the 17-part test suite to verify end-to-end reliability."*

---

## 5. Pre-Flight Defense Day Checklist

- [ ] **Laptop Power**: Charged to 100% and connected to AC power.
- [ ] **Application Running**: Run `python app.py` and open `http://127.0.0.1:5000`.
- [ ] **Clean Presentation**: Full-screen browser window (F11), no cluttered desktop icons.
- [ ] **GitHub Backup**: Keep [Stanloski/NIDS-Project](https://github.com/Stanloski/NIDS-Project) open in a tab to prove commit history.
- [ ] **Delivery Style**: Speak calmly, listen attentively, acknowledge examiners with *"Thank you, Sir/Ma"*, and answer directly.
