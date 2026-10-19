"""
Automated Screenshot Capture Script for UNN NIDS
Captures all major views in both Light (Day Technical Paper) and Dark (Tactical Radar Watchtower) Mode,
plus 375px mobile responsive control room testing.
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import app

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SECRET_KEY = app.config['SECRET_KEY']
BASE_URL = "http://127.0.0.1:5000"
SCREENSHOTS_DIR = Path("screenshots").resolve()
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

USER_DATA_DIR = tempfile.mkdtemp()

views = [
    # (name, url_path, window_size)
    ("login_light", f"{BASE_URL}/login?theme=light&booted=1", "1440,900"),
    ("login_dark", f"{BASE_URL}/login?theme=dark&booted=1", "1440,900"),
    ("dashboard_light", f"{BASE_URL}/?theme=light&auth_token={SECRET_KEY}", "1440,900"),
    ("dashboard_dark", f"{BASE_URL}/?theme=dark&auth_token={SECRET_KEY}", "1440,900"),
    ("dashboard_mobile_375", f"{BASE_URL}/?theme=dark&auth_token={SECRET_KEY}", "375,812"),
    ("predict_light", f"{BASE_URL}/predict?theme=light&auth_token={SECRET_KEY}", "1440,900"),
    ("predict_dark", f"{BASE_URL}/predict?theme=dark&auth_token={SECRET_KEY}", "1440,900"),
    ("upload_light", f"{BASE_URL}/upload?theme=light&auth_token={SECRET_KEY}", "1440,900"),
    ("upload_dark", f"{BASE_URL}/upload?theme=dark&auth_token={SECRET_KEY}", "1440,900"),
    ("history_light", f"{BASE_URL}/history?theme=light&auth_token={SECRET_KEY}", "1440,900"),
    ("history_dark", f"{BASE_URL}/history?theme=dark&auth_token={SECRET_KEY}", "1440,900"),
]

print("Capturing application screenshots across all pages in light and dark mode...")

for name, url, win_size in views:
    out_file = SCREENSHOTS_DIR / f"{name}.png"
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={USER_DATA_DIR}",
        f"--window-size={win_size}",
        "--run-all-compositor-stages-before-draw",
        f"--screenshot={str(out_file)}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if out_file.exists() and out_file.stat().st_size > 0:
        print(f"[OK] {name}.png ({out_file.stat().st_size} bytes)")
    else:
        print(f"[ERROR] Failed to capture {name}: {res.stderr}")

# Also sync to nids/screenshots
nids_screenshots = BASE_DIR / "screenshots"
nids_screenshots.mkdir(exist_ok=True, parents=True)
for f in SCREENSHOTS_DIR.glob("*.png"):
    import shutil
    shutil.copy(f, nids_screenshots / f.name)

print("All screenshots generated and saved in /screenshots and /nids/screenshots!")
