import subprocess
import sys
import time
import requests
import os
import signal
import pytest

MOBILE_APP_DIR = os.path.join(os.path.dirname(__file__), 'mobile_app')
APP_PATH = os.path.join(MOBILE_APP_DIR, 'app.py')

@pytest.fixture(scope="module")
def flask_server():
    # Start the Flask app as a subprocess
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "1"
    process = subprocess.Popen([sys.executable, APP_PATH], cwd=MOBILE_APP_DIR, env=env)
    # Wait for the server to start
    time.sleep(3)
    yield
    # Teardown: terminate the Flask process
    if process.poll() is None:
        if os.name == 'nt':
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_flask_status(flask_server):
    # Health check for the Flask API
    url = "http://127.0.0.1:5000/api/status"
    for _ in range(10):
        try:
            r = requests.get(url, timeout=2)
            assert r.status_code == 200
            assert r.json().get('success') is True
            break
        except Exception:
            time.sleep(1)
    else:
        pytest.fail("Flask API did not start or /api/status not reachable")
