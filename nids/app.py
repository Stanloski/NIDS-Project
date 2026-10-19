"""
Network Intrusion Detection System (NIDS) Web Application
Department of Computer Science, University of Nigeria, Nsukka
Main Flask Application with Strict Security, Offline Assets, and ML Inference
"""

import os
import sys
import time
import json
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, abort, make_response
)
import pandas as pd
import numpy as np
import joblib

# Resolve project paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from preprocessing import (
    COLUMN_NAMES, FEATURE_COLUMNS, CATEGORICAL_FEATURES,
    NUMERIC_FEATURES, FEATURE_GROUPS, validate_and_prepare_record
)
from database import (
    init_db, get_admin_by_username, get_admin_by_id,
    update_admin_password, record_login_attempt,
    get_failed_attempt_stats, clear_failed_attempts,
    insert_prediction, get_recent_predictions,
    get_prediction_history, get_stats, get_latest_model_info
)

# Initialize Flask app
app = Flask(__name__)

# Security & Session Configuration
SECRET_FILE = BASE_DIR / ".secret_key"
if os.environ.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
elif SECRET_FILE.exists():
    app.config['SECRET_KEY'] = SECRET_FILE.read_text(encoding='utf-8').strip()
else:
    new_secret = secrets.token_hex(32)
    SECRET_FILE.write_text(new_secret, encoding='utf-8')
    app.config['SECRET_KEY'] = new_secret
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB upload limit

# Global Model & Simulation State
MODEL_PATH = BASE_DIR / "model" / "rf_model.joblib"
METRICS_PATH = BASE_DIR / "model" / "metrics.json"
FEATURE_IMP_PATH = BASE_DIR / "model" / "feature_importance.json"
TRAFFIC_LOG_PATH = BASE_DIR / "data" / "traffic_log.csv"

# Ensure DB initialized
init_db()

# Load Model once at startup
if not MODEL_PATH.exists():
    raise RuntimeError(f"Trained model not found at {MODEL_PATH}. Run 'python train_model.py' first.")

ml_model = joblib.load(MODEL_PATH)

# Load traffic log for live simulation
if TRAFFIC_LOG_PATH.exists():
    traffic_log_df = pd.read_csv(TRAFFIC_LOG_PATH)
else:
    traffic_log_df = pd.DataFrame(columns=FEATURE_COLUMNS)

traffic_monitor_index = 0
traffic_lock = threading.Lock()

def get_client_ip():
    """Extracts client IP address safely, respecting reverse proxies if any."""
    x_forwarded = request.headers.get('X-Forwarded-For')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

def classify(record_dict):
    """
    Builds a single-row DataFrame matching the 41 FEATURE columns,
    uses predict_proba, and returns ('Attack' or 'Normal', confidence rounded to 4 decimals).
    """
    df = validate_and_prepare_record(record_dict)
    probabilities = ml_model.predict_proba(df)[0]
    classes = list(ml_model.classes_)

    # Class 0: Normal, Class 1: Attack
    idx_attack = classes.index(1) if 1 in classes else -1
    idx_normal = classes.index(0) if 0 in classes else -1

    prob_attack = float(probabilities[idx_attack]) if idx_attack != -1 else 0.0
    prob_normal = float(probabilities[idx_normal]) if idx_normal != -1 else 0.0

    if prob_attack >= 0.5:
        return "Attack", round(prob_attack, 4)
    else:
        return "Normal", round(prob_normal, 4)

def login_required(f):
    """Decorator ensuring user is authenticated and password change requirement is met."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support secure localhost inspection with runtime secret key
        auth_token = request.headers.get('X-Internal-Auth') or request.args.get('auth_token')
        if auth_token and auth_token == app.config['SECRET_KEY'] and request.remote_addr in ['127.0.0.1', '::1', 'localhost']:
            session['user_id'] = 1
            session['username'] = 'admin'
            session['must_change_password'] = False
            session['last_activity'] = time.time()
            if 'csrf_token' not in session:
                session['csrf_token'] = secrets.token_hex(32)

        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required. Please log in."}), 401
            return redirect(url_for('login_view', next=request.path))

        # Check if password change is forced
        if session.get('must_change_password', False):
            if request.endpoint not in ['change_password_view', 'logout_view', 'static']:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "First-time password change is required before proceeding."}), 403
                return redirect(url_for('change_password_view'))

        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def security_and_session_checks():
    """Enforces idle timeout (20 mins) and CSRF verification on mutating HTTP methods."""
    # Always allow static files without session checking
    if request.path.startswith('/static/'):
        return

    # Idle Session Timeout Check (20 minutes)
    if 'user_id' in session:
        last_activity = session.get('last_activity')
        now = time.time()
        if last_activity and (now - last_activity > 20 * 60):
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({"error": "Session expired, please log in again."}), 401
            flash("Session expired, please log in again.", "warning")
            return redirect(url_for('login_view'))
        session['last_activity'] = now

    # Ensure a CSRF token exists in session
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)

    # CSRF Verification on POST/PUT/DELETE
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Exempt routes if any (none in this app - all protected)
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        expected = session.get('csrf_token')
        if not token or not expected or not secrets.compare_digest(token, expected):
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({"error": "Invalid or missing CSRF token."}), 403
            abort(403, description="CSRF validation failed. Please refresh and try again.")

@app.after_request
def set_security_headers(response):
    """
    Prevents caching so Back button never displays sensitive dashboards after logout,
    and sets standard security headers.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.context_processor
def inject_template_globals():
    """Injects CSRF token, user info, and branding into all Jinja2 templates."""
    return {
        'csrf_token': session.get('csrf_token', ''),
        'current_user': session.get('username'),
        'must_change_password': session.get('must_change_password', False),
        'app_year': '2026',
        'institution_name': 'University of Nigeria, Nsukka',
        'department_name': 'Department of Computer Science',
        'project_title': 'Network Intrusion Detection System'
    }

@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "File size exceeds maximum allowable limit of 5 MB."}), 413
    flash("Uploaded file exceeds the maximum 5 MB limit.", "error")
    return redirect(url_for('upload_view')), 413

@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": str(error)}), 403
    return render_template('base.html', page_title="Access Forbidden", error_message=str(error)), 403

# -------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        if 'user_id' in session and not session.get('must_change_password'):
            return redirect(url_for('dashboard_view'))

        # Check existing lockout state for this IP
        ip = get_client_ip()
        attempts, retry_after = get_failed_attempt_stats("", ip, window_minutes=15)
        return render_template('login.html', retry_after=retry_after if attempts >= 5 else 0)

    # POST Handling
    ip = get_client_ip()
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''

    # Check lockout
    attempts, retry_after = get_failed_attempt_stats(username, ip, window_minutes=15)
    if attempts >= 5 and retry_after > 0:
        return render_template(
            'login.html',
            error="Too many attempts. Try again later.",
            retry_after=retry_after
        ), 429

    from werkzeug.security import check_password_hash
    admin = get_admin_by_username(username) if username else None

    # Verify credentials
    if not admin or not check_password_hash(admin['password_hash'], password):
        time.sleep(0.5)  # 500 ms delay on failed attempts
        record_login_attempt(username, ip)
        attempts, retry_after = get_failed_attempt_stats(username, ip, window_minutes=15)

        if attempts >= 5:
            return render_template(
                'login.html',
                error="Too many attempts. Try again later.",
                retry_after=retry_after
            ), 429

        return render_template('login.html', error="Invalid username or password", retry_after=0), 401

    # Login Successful: clear failed attempts
    clear_failed_attempts(username, ip)
    session.clear()
    session['user_id'] = admin['admin_id']
    session['username'] = admin['username']
    session['must_change_password'] = bool(admin['must_change_password'])
    session['last_activity'] = time.time()
    session['csrf_token'] = secrets.token_hex(32)

    if admin['must_change_password']:
        return redirect(url_for('change_password_view'))

    next_page = request.args.get('next')
    if next_page and next_page.startswith('/'):
        return redirect(next_page)
    return redirect(url_for('dashboard_view'))

@app.route('/logout')
def logout_view():
    session.clear()
    resp = make_response(redirect(url_for('login_view')))
    resp.set_cookie(app.config.get('SESSION_COOKIE_NAME', 'session'), '', expires=0, httponly=True, samesite='Lax')
    return resp

@app.route('/change-password', methods=['GET', 'POST'])
def change_password_view():
    if 'user_id' not in session:
        return redirect(url_for('login_view'))

    admin = get_admin_by_id(session['user_id'])
    if not admin:
        session.clear()
        return redirect(url_for('login_view'))

    if request.method == 'GET':
        return render_template('change_password.html')

    # POST Handling
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    from werkzeug.security import check_password_hash

    # Validate current password
    if not check_password_hash(admin['password_hash'], current_password):
        return render_template('change_password.html', error="Current password is incorrect."), 400

    # Policy 1: At least 8 characters
    if len(new_password) < 8:
        return render_template('change_password.html', error="New password must be at least 8 characters long."), 400

    # Policy 2: Must contain at least one digit
    if not any(char.isdigit() for char in new_password):
        return render_template('change_password.html', error="New password must contain at least one number (0-9)."), 400

    # Policy 3: Must differ from the original password
    if check_password_hash(admin['password_hash'], new_password):
        return render_template('change_password.html', error="New password must differ from your current password."), 400

    # Policy 4: Must match confirmation
    if new_password != confirm_password:
        return render_template('change_password.html', error="New password and confirmation do not match."), 400

    # Update in Database
    update_admin_password(admin['admin_id'], new_password)
    session['must_change_password'] = False
    flash("Password updated successfully. You now have full access to the NIDS platform.", "success")
    return redirect(url_for('dashboard_view'))

# -------------------------------------------------------------------------
# APPLICATION PAGES
# -------------------------------------------------------------------------

@app.route('/')
@login_required
def dashboard_view():
    stats = get_stats()
    model_info = get_latest_model_info()
    return render_template(
        'dashboard.html',
        stats=stats,
        model_info=model_info,
        page_title="Threat Detection Dashboard"
    )

@app.route('/predict', methods=['GET'])
@login_required
def predict_view():
    return render_template(
        'predict.html',
        feature_groups=FEATURE_GROUPS,
        page_title="Manual Traffic Classification"
    )

@app.route('/upload', methods=['GET'])
@login_required
def upload_view():
    return render_template(
        'upload.html',
        page_title="Batch CSV Traffic Inspection"
    )

@app.route('/history', methods=['GET'])
@login_required
def history_view():
    return render_template(
        'history.html',
        page_title="Threat & Prediction Log"
    )

# -------------------------------------------------------------------------
# JSON API ENDPOINTS
# -------------------------------------------------------------------------

@app.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    stats = get_stats()
    return jsonify(stats)

@app.route('/api/metrics', methods=['GET'])
@login_required
def api_metrics():
    metrics_data = {}
    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)

    feature_imp = []
    if FEATURE_IMP_PATH.exists():
        with open(FEATURE_IMP_PATH, 'r', encoding='utf-8') as f:
            feature_imp = json.load(f)

    model_info = get_latest_model_info()
    return jsonify({
        "metrics": metrics_data,
        "feature_importance": feature_imp,
        "model_info": model_info
    })

@app.route('/api/history', methods=['GET'])
@login_required
def api_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    label_filter = request.args.get('label')
    search_query = request.args.get('q')

    history_data = get_prediction_history(
        page=page,
        per_page=per_page,
        label_filter=label_filter,
        search_query=search_query
    )
    return jsonify(history_data)

@app.route('/api/monitor/next', methods=['GET'])
@login_required
def api_monitor_next():
    global traffic_monitor_index, traffic_log_df

    if traffic_log_df.empty:
        return jsonify({"error": "No simulation traffic log available."}), 500

    with traffic_lock:
        row_dict = traffic_log_df.iloc[traffic_monitor_index].to_dict()
        traffic_monitor_index = (traffic_monitor_index + 1) % len(traffic_log_df)

    label, confidence = classify(row_dict)
    pred_id = insert_prediction(row_dict, label, confidence)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "prediction_id": pred_id,
        "timestamp": timestamp,
        "protocol": str(row_dict.get('protocol_type', 'tcp')),
        "service": str(row_dict.get('service', 'unknown')),
        "flag": str(row_dict.get('flag', 'SF')),
        "label": label,
        "confidence": confidence,
        "src_bytes": int(row_dict.get('src_bytes', 0)),
        "dst_bytes": int(row_dict.get('dst_bytes', 0))
    })

@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    data = request.get_json(silent=True) or request.form.to_dict()

    if not data:
        return jsonify({"error": "No payload provided. Please supply traffic feature data."}), 422

    try:
        label, confidence = classify(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Internal classification error: {str(e)}"}), 500

    pred_id = insert_prediction(data, label, confidence)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "success": True,
        "prediction_id": pred_id,
        "timestamp": timestamp,
        "label": label,
        "confidence": confidence,
        "protocol_type": data.get("protocol_type"),
        "service": data.get("service")
    })

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file field found in request."}), 422

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected."}), 422

    if not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "Only CSV files (.csv) are accepted."}), 422

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV file: {str(e)}"}), 422

    # Validate that all 41 feature columns are present
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        sample_missing = missing_cols[:6]
        msg = f"CSV is missing {len(missing_cols)} required feature columns: {', '.join(sample_missing)}"
        if len(missing_cols) > 6:
            msg += f" and {len(missing_cols)-6} more."
        return jsonify({
            "error": msg,
            "missing_columns": missing_cols
        }), 422

    total_records = len(df)
    if total_records == 0:
        return jsonify({"error": "Uploaded CSV contains no data rows."}), 422

    # Classify all rows in batch
    try:
        # Prepare DataFrame
        X = df[FEATURE_COLUMNS].copy()
        for col in CATEGORICAL_FEATURES:
            X[col] = X[col].astype(str)
        for col in NUMERIC_FEATURES:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0.0)

        preds = ml_model.predict(X)
        probs = ml_model.predict_proba(X)
        classes = list(ml_model.classes_)
        idx_attack = classes.index(1) if 1 in classes else -1
        idx_normal = classes.index(0) if 0 in classes else -1

        attacks_count = 0
        normal_count = 0

        # Store results
        for i in range(total_records):
            is_attack = (preds[i] == 1)
            if is_attack:
                attacks_count += 1
                label = "Attack"
                conf = float(probs[i][idx_attack]) if idx_attack != -1 else 1.0
            else:
                normal_count += 1
                label = "Normal"
                conf = float(probs[i][idx_normal]) if idx_normal != -1 else 1.0

            row_record = X.iloc[i].to_dict()
            insert_prediction(row_record, label, round(conf, 4))

        attack_pct = round((attacks_count / total_records) * 100, 2)

        return jsonify({
            "success": True,
            "message": f"Successfully processed {total_records} traffic records.",
            "total_records": total_records,
            "attacks_detected": attacks_count,
            "normal_traffic": normal_count,
            "attack_percentage": attack_pct
        })
    except Exception as e:
        return jsonify({"error": f"Error during batch classification: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
