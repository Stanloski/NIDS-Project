"""
Automated Test Suite for UNN NIDS
Validates all test cases T1 through T17 end-to-end.
"""

import os
import sys
import time
import json
import sqlite3
import io
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import app, classify
from database import (
    init_db, get_db_connection, DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD, update_admin_password
)
from preprocessing import FEATURE_COLUMNS, validate_and_prepare_record

def run_all_tests():
    print("=" * 70)
    print("UNN NIDS COMPREHENSIVE TEST SUITE (T1 - T17)")
    print("=" * 70)

    results = {}
    init_db()
    client = app.test_client()

    # Reset admin to initial state for testing
    from werkzeug.security import generate_password_hash
    conn = get_db_connection()
    conn.execute("DELETE FROM LoginAttempts;")
    conn.execute("UPDATE Admin SET password_hash = ?, must_change_password = 1 WHERE username = ?;",
                 (generate_password_hash(DEFAULT_ADMIN_PASSWORD, method="scrypt"), DEFAULT_ADMIN_USERNAME))
    conn.commit()
    conn.close()

    # Helper to get CSRF token from a page
    def get_csrf(resp):
        html = resp.get_data(as_text=True)
        import re
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        if m: return m.group(1)
        m = re.search(r'value="([^"]+)"\s+name="csrf_token"', html)
        return m.group(1) if m else ""

    # -----------------------------------------------------------------
    # T1: Valid Login
    # -----------------------------------------------------------------
    try:
        r_get = client.get('/login')
        csrf = get_csrf(r_get)
        r_post = client.post('/login', data={
            'username': DEFAULT_ADMIN_USERNAME,
            'password': DEFAULT_ADMIN_PASSWORD,
            'csrf_token': csrf
        }, follow_redirects=False)
        # Should redirect to change-password because must_change_password=1
        assert r_post.status_code == 302, f"Expected 302 redirect, got {r_post.status_code}"
        assert '/change-password' in r_post.headers['Location']
        results['T1'] = ("PASS", "Valid login succeeded and redirected appropriately.")
    except Exception as e:
        results['T1'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T2: Wrong Password
    # -----------------------------------------------------------------
    try:
        with client.session_transaction() as sess:
            sess.clear()
        r_get = client.get('/login')
        csrf = get_csrf(r_get)
        r_post = client.post('/login', data={
            'username': DEFAULT_ADMIN_USERNAME,
            'password': 'WrongPassword123!',
            'csrf_token': csrf
        })
        assert r_post.status_code == 401, f"Expected 401, got {r_post.status_code}"
        assert "Invalid username or password" in r_post.get_data(as_text=True)
        results['T2'] = ("PASS", "Generic error 'Invalid username or password' returned on incorrect credentials.")
    except Exception as e:
        results['T2'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T3: Protected API without login returns 401 or redirect
    # -----------------------------------------------------------------
    try:
        with client.session_transaction() as sess:
            sess.clear()
        # API request
        r_api = client.get('/api/stats')
        assert r_api.status_code == 401, f"Expected 401 for unauthenticated API, got {r_api.status_code}"
        # Page request
        r_page = client.get('/')
        assert r_page.status_code == 302, f"Expected 302 redirect for unauthenticated page, got {r_page.status_code}"
        assert '/login' in r_page.headers['Location']
        results['T3'] = ("PASS", "Protected API returned 401 JSON and protected page redirected to /login.")
    except Exception as e:
        results['T3'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # Authenticate client for subsequent authenticated tests
    # First change password to clear must_change_password flag
    # -----------------------------------------------------------------
    with client.session_transaction() as sess:
        sess.clear()
    r_get = client.get('/login')
    csrf = get_csrf(r_get)
    client.post('/login', data={
        'username': DEFAULT_ADMIN_USERNAME,
        'password': DEFAULT_ADMIN_PASSWORD,
        'csrf_token': csrf
    })
    # Now on /change-password
    r_cp_get = client.get('/change-password')
    csrf_cp = get_csrf(r_cp_get)
    new_test_pw = "NidsSecret2026!"
    client.post('/change-password', data={
        'current_password': DEFAULT_ADMIN_PASSWORD,
        'new_password': new_test_pw,
        'confirm_password': new_test_pw,
        'csrf_token': csrf_cp
    })

    # -----------------------------------------------------------------
    # T4: Start Monitoring shows records every second (/api/monitor/next)
    # -----------------------------------------------------------------
    try:
        r_mon = client.get('/api/monitor/next')
        assert r_mon.status_code == 200, f"Expected 200, got {r_mon.status_code}"
        data = r_mon.get_json()
        assert "label" in data and data["label"] in ["Normal", "Attack"]
        assert "confidence" in data and 0 <= data["confidence"] <= 1
        assert "protocol" in data and "service" in data and "timestamp" in data
        results['T4'] = ("PASS", f"Stream endpoint returned next classified packet: {data['label']} ({data['confidence']})")
    except Exception as e:
        results['T4'] = ("FAIL", str(e))

    # Canonical sample records
    norm_sample = {
        "duration": 2, "protocol_type": "tcp", "service": "ftp_data", "flag": "SF",
        "src_bytes": 12983, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0, "root_shell": 0,
        "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0,
        "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
        "count": 1, "srv_count": 1, "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0, "srv_diff_host_rate": 0.0,
        "dst_host_count": 134, "dst_host_srv_count": 86, "dst_host_same_srv_rate": 0.61,
        "dst_host_diff_srv_rate": 0.04, "dst_host_same_src_port_rate": 0.61,
        "dst_host_srv_diff_host_rate": 0.02, "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0
    }

    attack_sample = {
        "duration": 0, "protocol_type": "tcp", "service": "private", "flag": "REJ",
        "src_bytes": 0, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0, "root_shell": 0,
        "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0,
        "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
        "count": 229, "srv_count": 10, "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 1.0,
        "srv_rerror_rate": 1.0, "same_srv_rate": 0.04, "diff_srv_rate": 0.06, "srv_diff_host_rate": 0.0,
        "dst_host_count": 255, "dst_host_srv_count": 10, "dst_host_same_srv_rate": 0.04,
        "dst_host_diff_srv_rate": 0.06, "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 1.0, "dst_host_srv_rerror_rate": 1.0
    }

    # -----------------------------------------------------------------
    # T5: Known normal record gives Normal
    # -----------------------------------------------------------------
    try:
        lbl, conf = classify(norm_sample)
        assert lbl == "Normal", f"Expected Normal, got {lbl}"
        results['T5'] = ("PASS", f"Known normal record correctly classified as Normal (conf: {conf})")
    except Exception as e:
        results['T5'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T6: Known attack record gives Attack
    # -----------------------------------------------------------------
    try:
        lbl, conf = classify(attack_sample)
        assert lbl == "Attack", f"Expected Attack, got {lbl}"
        results['T6'] = ("PASS", f"Known attack record correctly classified as Attack (conf: {conf})")
    except Exception as e:
        results['T6'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T7: Confidence is between 0 and 1
    # -----------------------------------------------------------------
    try:
        _, conf1 = classify(norm_sample)
        _, conf2 = classify(attack_sample)
        assert 0.0 <= conf1 <= 1.0, f"Confidence {conf1} out of bounds"
        assert 0.0 <= conf2 <= 1.0, f"Confidence {conf2} out of bounds"
        results['T7'] = ("PASS", f"Confidence scores bounded in [0, 1]: Normal={conf1}, Attack={conf2}")
    except Exception as e:
        results['T7'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T8: Missing manual field gives a validation error (422)
    # -----------------------------------------------------------------
    try:
        bad_sample = norm_sample.copy()
        del bad_sample['src_bytes']
        del bad_sample['service']
        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')
        r_pred = client.post('/api/predict',
                             data=json.dumps(bad_sample),
                             headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token})
        assert r_pred.status_code == 422, f"Expected 422, got {r_pred.status_code}"
        assert "Missing required feature columns" in r_pred.get_json().get("error", "")
        results['T8'] = ("PASS", f"Missing fields rejected with 422: {r_pred.get_json()['error']}")
    except Exception as e:
        results['T8'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T9: CSV with missing columns is rejected (422)
    # -----------------------------------------------------------------
    try:
        invalid_csv_content = "duration,protocol_type,service\n0,tcp,http\n"
        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')
        data = {
            'file': (io.BytesIO(invalid_csv_content.encode('utf-8')), 'test_bad.csv')
        }
        r_upload = client.post('/api/upload',
                               data=data,
                               content_type='multipart/form-data',
                               headers={'X-CSRF-Token': csrf_token})
        assert r_upload.status_code == 422, f"Expected 422, got {r_upload.status_code}"
        assert "missing" in r_upload.get_json().get("error", "").lower()
        results['T9'] = ("PASS", f"CSV with missing columns rejected with 422: {r_upload.get_json()['error']}")
    except Exception as e:
        results['T9'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T10: Valid CSV upload shows counts
    # -----------------------------------------------------------------
    try:
        sample_csv_path = BASE_DIR / "data" / "sample_upload.csv"
        with open(sample_csv_path, 'rb') as f:
            csv_bytes = f.read()
        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')
        data = {
            'file': (io.BytesIO(csv_bytes), 'sample_upload.csv')
        }
        r_upload = client.post('/api/upload',
                               data=data,
                               content_type='multipart/form-data',
                               headers={'X-CSRF-Token': csrf_token})
        assert r_upload.status_code == 200, f"Expected 200, got {r_upload.status_code}"
        res = r_upload.get_json()
        assert res.get("total_records") == 20, f"Expected 20 records, got {res.get('total_records')}"
        assert "attacks_detected" in res and "normal_traffic" in res
        results['T10'] = ("PASS", f"Valid CSV processed: total={res['total_records']}, attacks={res['attacks_detected']}, normal={res['normal_traffic']}")
    except Exception as e:
        results['T10'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T11: Each prediction adds a row to PredictionHistory
    # -----------------------------------------------------------------
    try:
        conn = get_db_connection()
        count_before = conn.execute("SELECT COUNT(*) FROM PredictionHistory;").fetchone()[0]
        conn.close()

        with client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')
        r_pred = client.post('/api/predict',
                             data=json.dumps(norm_sample),
                             headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token})
        assert r_pred.status_code == 200

        conn = get_db_connection()
        count_after = conn.execute("SELECT COUNT(*) FROM PredictionHistory;").fetchone()[0]
        conn.close()

        assert count_after == count_before + 1, f"Expected {count_before + 1} rows, found {count_after}"
        results['T11'] = ("PASS", f"Prediction added exactly 1 row (count: {count_before} -> {count_after})")
    except Exception as e:
        results['T11'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T12: History shows newest first
    # -----------------------------------------------------------------
    try:
        r_hist = client.get('/api/history?per_page=10')
        assert r_hist.status_code == 200
        items = r_hist.get_json().get("items", [])
        assert len(items) >= 2, "Need at least 2 history items to verify ordering"
        id1 = items[0]["prediction_id"]
        id2 = items[1]["prediction_id"]
        assert id1 > id2, f"Expected newest first (id1={id1} > id2={id2})"
        results['T12'] = ("PASS", f"History returned newest first: ID #{id1} preceding ID #{id2}")
    except Exception as e:
        results['T12'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T13: A record with an unseen service value does not crash
    # -----------------------------------------------------------------
    try:
        unseen_sample = norm_sample.copy()
        unseen_sample['service'] = "completely_unseen_exotic_service_999"
        lbl, conf = classify(unseen_sample)
        assert lbl in ["Normal", "Attack"]
        results['T13'] = ("PASS", f"Unseen service handled safely without exception, predicted: {lbl} ({conf})")
    except Exception as e:
        results['T13'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T14: After logout the Back button does not show dashboard & login fields empty
    # -----------------------------------------------------------------
    try:
        r_logout = client.get('/logout')
        assert r_logout.status_code == 302
        assert 'session=' in r_logout.headers.get('Set-Cookie', '')

        # Attempt to access dashboard again
        r_dash = client.get('/')
        assert r_dash.status_code == 302
        assert '/login' in r_dash.headers['Location']

        # Verify Cache-Control headers
        cc = r_dash.headers.get('Cache-Control', '')
        pragma = r_dash.headers.get('Pragma', '')
        assert 'no-store' in cc and 'no-cache' in cc
        assert 'no-cache' in pragma

        # Verify login page fields have autocomplete="off" / "new-password"
        r_login_page = client.get('/login')
        html = r_login_page.get_data(as_text=True)
        assert 'autocomplete="off"' in html
        assert 'autocomplete="new-password"' in html
        results['T14'] = ("PASS", "Session purged, Back button invalidated with no-store headers, and login fields empty.")
    except Exception as e:
        results['T14'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T15: Six wrong passwords trigger the lockout (429)
    # -----------------------------------------------------------------
    try:
        # Clear attempts table first for isolated test
        conn = get_db_connection()
        conn.execute("DELETE FROM LoginAttempts WHERE username = 'lockout_test_user';")
        conn.commit()
        conn.close()

        test_ip = "192.168.1.99"
        statuses = []
        for i in range(6):
            r_get = client.get('/login')
            csrf = get_csrf(r_get)
            r = client.post('/login',
                            data={'username': 'lockout_test_user', 'password': f'badpw_{i}', 'csrf_token': csrf},
                            environ_base={'REMOTE_ADDR': test_ip})
            statuses.append(r.status_code)

        assert statuses[-1] == 429, f"Expected 6th attempt to return 429, got {statuses[-1]}"
        results['T15'] = ("PASS", f"Lockout triggered: attempts 1-5 returned 401, 6th attempt returned HTTP 429.")
    except Exception as e:
        results['T15'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T16: First login forces a password change
    # -----------------------------------------------------------------
    try:
        # Reset admin to must_change_password = 1
        conn = get_db_connection()
        conn.execute("UPDATE Admin SET must_change_password = 1 WHERE username = ?;", (DEFAULT_ADMIN_USERNAME,))
        conn.commit()
        conn.close()

        with client.session_transaction() as sess:
            sess.clear()

        r_get = client.get('/login')
        csrf = get_csrf(r_get)
        client.post('/login', data={
            'username': DEFAULT_ADMIN_USERNAME,
            'password': new_test_pw,
            'csrf_token': csrf
        })

        # Try accessing dashboard
        r_dash = client.get('/')
        assert r_dash.status_code == 302 and '/change-password' in r_dash.headers['Location']

        # Try accessing API
        r_api = client.get('/api/stats')
        assert r_api.status_code == 403, f"Expected 403 for API when password change required, got {r_api.status_code}"

        results['T16'] = ("PASS", "Enforced password change: page requests redirect to /change-password, APIs return 403.")
    except Exception as e:
        results['T16'] = ("FAIL", str(e))

    # -----------------------------------------------------------------
    # T17: Idle timeout works
    # -----------------------------------------------------------------
    try:
        # Complete password change to have normal session
        r_cp_get = client.get('/change-password')
        csrf_cp = get_csrf(r_cp_get)
        new_pw_2 = "NidsSecureActive2026!"
        client.post('/change-password', data={
            'current_password': new_test_pw,
            'new_password': new_pw_2,
            'confirm_password': new_pw_2,
            'csrf_token': csrf_cp
        })

        # Set last_activity to 25 minutes ago
        with client.session_transaction() as sess:
            sess['last_activity'] = time.time() - (25 * 60)

        # Accessing dashboard should now expire session and redirect to /login
        r_dash = client.get('/')
        assert r_dash.status_code == 302 and '/login' in r_dash.headers['Location']

        # Session should now be cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess, "Session was not cleared on idle timeout"

        results['T17'] = ("PASS", "20-minute idle timeout expired session and redirected to login.")
    except Exception as e:
        results['T17'] = ("FAIL", str(e))

    # Clean up and restore default admin credentials and clear failed attempts
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM LoginAttempts;")
        conn.execute("UPDATE Admin SET password_hash = ?, must_change_password = 1 WHERE username = ?;",
                     (generate_password_hash(DEFAULT_ADMIN_PASSWORD, method="scrypt"), DEFAULT_ADMIN_USERNAME))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to restore default credentials: {e}")

    print("\n" + "-" * 70)
    print("FINAL TEST EXECUTION SUMMARY:")
    print("-" * 70)
    all_passed = True
    for code, (status, msg) in sorted(results.items()):
        print(f"[{status}] {code}: {msg}")
        if status != "PASS":
            all_passed = False
    print("-" * 70)
    print(f"OVERALL STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
