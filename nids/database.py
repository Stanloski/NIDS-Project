"""
Database Management for NIDS
University of Nigeria, Nsukka - Department of Computer Science
SQLite Schema Definition, Admin Seeding, and Query Utilities
"""

import sqlite3
import os
import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# Resolve database path relative to project
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nids.db"

# Default Admin Credentials (documented in README.md only)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "NidsAdmin2026!"

def get_db_path():
    return str(DB_PATH)

def get_db_connection():
    """Returns a SQLite connection with row access by column name."""
    conn = sqlite3.connect(get_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Creates tables if they do not exist and seeds initial admin account."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admin Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            must_change_password INTEGER DEFAULT 1
        );
    """)

    # 2. PredictionHistory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PredictionHistory (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            traffic_record TEXT NOT NULL,
            predicted_label TEXT CHECK(predicted_label IN ('Normal', 'Attack')) NOT NULL,
            confidence_score REAL NOT NULL
        );
    """)

    # Index for fast filtering and history retrieval
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prediction_timestamp ON PredictionHistory(timestamp DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prediction_label ON PredictionHistory(predicted_label);
    """)

    # 3. ModelInformation Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ModelInformation (
            model_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            training_dataset TEXT NOT NULL,
            date_trained TEXT NOT NULL,
            accuracy REAL NOT NULL
        );
    """)

    # 4. LoginAttempts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LoginAttempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip_address TEXT,
            attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_attempted ON LoginAttempts(attempted_at DESC);
    """)

    # Seed initial Admin account if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM Admin;")
    row = cursor.fetchone()
    if row["count"] == 0:
        hashed_pw = generate_password_hash(DEFAULT_ADMIN_PASSWORD, method="scrypt")
        cursor.execute("""
            INSERT INTO Admin (username, password_hash, must_change_password)
            VALUES (?, ?, 1);
        """, (DEFAULT_ADMIN_USERNAME, hashed_pw))

    conn.commit()
    conn.close()

def get_admin_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Admin WHERE username = ?;", (username,))
    admin = cursor.fetchone()
    conn.close()
    return admin

def get_admin_by_id(admin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Admin WHERE admin_id = ?;", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin

def update_admin_password(admin_id, new_password):
    hashed_pw = generate_password_hash(new_password, method="scrypt")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Admin
        SET password_hash = ?, must_change_password = 0
        WHERE admin_id = ?;
    """, (hashed_pw, admin_id))
    conn.commit()
    conn.close()

def record_login_attempt(username, ip_address):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LoginAttempts (username, ip_address, attempted_at)
        VALUES (?, ?, datetime('now'));
    """, (username, ip_address))
    conn.commit()
    conn.close()

def get_failed_attempt_stats(username, ip_address, window_minutes=15):
    """
    Returns (count, retry_after_seconds) for attempts within the window.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT attempted_at,
               strftime('%s', 'now') - strftime('%s', attempted_at) AS elapsed_seconds
        FROM LoginAttempts
        WHERE (username = ? OR ip_address = ?)
          AND attempted_at >= datetime('now', '-' || ? || ' minutes')
        ORDER BY attempted_at DESC;
    """, (username, ip_address, window_minutes))
    rows = cursor.fetchall()
    conn.close()

    count = len(rows)
    if count >= 5:
        # Calculate lockout remaining from the latest attempt
        elapsed = rows[0]["elapsed_seconds"] if rows and rows[0]["elapsed_seconds"] is not None else 0
        retry_after = max(1, (window_minutes * 60) - int(elapsed))
        return count, retry_after
    return count, 0

def clear_failed_attempts(username, ip_address):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM LoginAttempts
        WHERE username = ? OR ip_address = ?;
    """, (username, ip_address))
    conn.commit()
    conn.close()

def insert_prediction(traffic_record, predicted_label, confidence_score):
    """
    Inserts a classified traffic record into PredictionHistory.
    traffic_record is serialized to JSON string if it's a dict.
    """
    if isinstance(traffic_record, dict):
        traffic_str = json.dumps(traffic_record)
    else:
        traffic_str = str(traffic_record)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO PredictionHistory (traffic_record, predicted_label, confidence_score)
        VALUES (?, ?, ?);
    """, (traffic_str, predicted_label, float(confidence_score)))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id

def get_recent_predictions(limit=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prediction_id, timestamp, traffic_record, predicted_label, confidence_score
        FROM PredictionHistory
        ORDER BY prediction_id DESC
        LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        rec_data = {}
        try:
            rec_data = json.loads(r["traffic_record"])
        except Exception:
            pass
        results.append({
            "prediction_id": r["prediction_id"],
            "timestamp": r["timestamp"],
            "predicted_label": r["predicted_label"],
            "confidence_score": round(r["confidence_score"], 4),
            "protocol_type": rec_data.get("protocol_type", "unknown"),
            "service": rec_data.get("service", "unknown"),
            "flag": rec_data.get("flag", "unknown"),
            "src_bytes": rec_data.get("src_bytes", 0),
            "dst_bytes": rec_data.get("dst_bytes", 0)
        })
    return results

def get_prediction_history(page=1, per_page=20, label_filter=None, search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if label_filter and label_filter.strip().lower() in ['normal', 'attack']:
        conditions.append("predicted_label = ?")
        params.append(label_filter.strip().capitalize())

    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        conditions.append("(traffic_record LIKE ? OR predicted_label LIKE ? OR timestamp LIKE ?)")
        params.extend([q, q, q])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Total count
    cursor.execute(f"SELECT COUNT(*) as total FROM PredictionHistory {where_clause};", params)
    total_count = cursor.fetchone()["total"]

    # Paginated data
    offset = (page - 1) * per_page
    cursor.execute(f"""
        SELECT prediction_id, timestamp, traffic_record, predicted_label, confidence_score
        FROM PredictionHistory
        {where_clause}
        ORDER BY prediction_id DESC
        LIMIT ? OFFSET ?;
    """, params + [per_page, offset])

    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        rec_data = {}
        try:
            rec_data = json.loads(r["traffic_record"])
        except Exception:
            pass
        items.append({
            "prediction_id": r["prediction_id"],
            "timestamp": r["timestamp"],
            "predicted_label": r["predicted_label"],
            "confidence_score": round(r["confidence_score"], 4),
            "protocol_type": rec_data.get("protocol_type", "-"),
            "service": rec_data.get("service", "-"),
            "flag": rec_data.get("flag", "-"),
            "src_bytes": rec_data.get("src_bytes", "-"),
            "dst_bytes": rec_data.get("dst_bytes", "-"),
            "full_record": rec_data
        })

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    return {
        "items": items,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM PredictionHistory;")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as attacks FROM PredictionHistory WHERE predicted_label = 'Attack';")
    attacks = cursor.fetchone()["attacks"]

    cursor.execute("SELECT COUNT(*) as normal FROM PredictionHistory WHERE predicted_label = 'Normal';")
    normal = cursor.fetchone()["normal"]

    # Last 50 predictions for trend sparkline / chart
    cursor.execute("""
        SELECT predicted_label, timestamp
        FROM PredictionHistory
        ORDER BY prediction_id DESC
        LIMIT 50;
    """)
    recent = cursor.fetchall()

    cursor.execute("""
        SELECT accuracy, model_name, training_dataset, date_trained
        FROM ModelInformation
        ORDER BY model_id DESC
        LIMIT 1;
    """)
    model_info = cursor.fetchone()
    conn.close()

    attack_pct = round((attacks / total * 100), 2) if total > 0 else 0.0
    accuracy = round(model_info["accuracy"] * 100, 2) if model_info and model_info["accuracy"] else 0.0

    recent_reversed = list(reversed(recent))
    trend = [1 if r["predicted_label"] == 'Attack' else 0 for r in recent_reversed]
    timestamps = [r["timestamp"] for r in recent_reversed]

    return {
        "total_records": total,
        "attacks_detected": attacks,
        "normal_traffic": normal,
        "attack_percentage": attack_pct,
        "model_accuracy": accuracy,
        "model_name": model_info["model_name"] if model_info else "Random Forest Classifier",
        "training_dataset": model_info["training_dataset"] if model_info else "NSL-KDD",
        "date_trained": model_info["date_trained"] if model_info else "2026-10-04",
        "trend": trend,
        "trend_timestamps": timestamps
    }

def insert_model_info(model_name, dataset, date_trained, accuracy):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ModelInformation (model_name, training_dataset, date_trained, accuracy)
        VALUES (?, ?, ?, ?);
    """, (model_name, dataset, date_trained, float(accuracy)))
    conn.commit()
    conn.close()

def get_latest_model_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ModelInformation
        ORDER BY model_id DESC
        LIMIT 1;
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
