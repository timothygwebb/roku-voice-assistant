"""
Flask API server for Roku Voice Assistant mobile interface.
Provides REST API endpoints for controlling Roku devices from mobile apps.
"""

from __future__ import annotations

import json
import logging
import os
import re
import webbrowser
from typing import Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, redirect, render_template, request, Response
from flask_cors import CORS
from requests import Response as RequestsResponse
from typing import TypedDict

# ---------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SuppressSSLHandshakeFilter(logging.Filter):
    """Filter to suppress SSL/TLS handshake error messages in werkzeug logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "\x16\x03" in message or r"\x16\x03" in message or "\\x16\\x03" in message:
            return False
        return True


werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.addFilter(SuppressSSLHandshakeFilter())

# ---------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

CORS(app, resources={r"/api/*": {"origins": "*"}})

CONFIG_FILE: str = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_ROKU_PORT: int = 8060

# ---------------------------------------------------------
# Typed Models
# ---------------------------------------------------------


class RokuApp(TypedDict):
    id: str
    display_name: str
    aliases: List[str]


APP_CATALOG: Dict[str, RokuApp] = {
    "netflix": {
        "id": "12",
        "display_name": "Netflix",
        "aliases": ["netflix"],
    },
    "hulu": {
        "id": "2285",
        "display_name": "Hulu",
        "aliases": ["hulu"],
    },
    "disney_plus": {
        "id": "291097",
        "display_name": "Disney+",
        "aliases": ["disney", "disney plus", "disney+"],
    },
    "prime_video": {
        "id": "13",
        "display_name": "Prime Video",
        "aliases": ["prime", "prime video", "amazon", "amazon prime"],
    },
    "youtube": {
        "id": "837",
        "display_name": "YouTube",
        "aliases": ["youtube", "you tube"],
    },
    "hbo_max": {
        "id": "61322",
        "display_name": "HBO Max",
        "aliases": ["hbo", "hbo max", "max"],
    },
}

# ---------------------------------------------------------
# Configuration Manager
# ---------------------------------------------------------


class RokuConfig:
    """Manages Roku device configuration."""

    roku_ip: Optional[str]

    def __init__(self) -> None:
        self.roku_ip = None
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.roku_ip = config.get("roku_ip")
                    logger.info("Loaded config: Roku IP = %s", self.roku_ip)
            else:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                logger.info("Config file not found. Created default config at %s", CONFIG_FILE)
        except Exception:
            logger.exception("Error loading config from %s", CONFIG_FILE)

    def save_config(self, roku_ip: str) -> Tuple[bool, str]:
        """Save configuration to file. Returns (success, message)."""
        self.roku_ip = roku_ip
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"roku_ip": roku_ip}, f, indent=2)
            logger.info("Saved config: Roku IP = %s (to %s)", roku_ip, CONFIG_FILE)
            return True, "Configuration saved"
        except Exception as e:
            logger.exception("Error saving config to %s", CONFIG_FILE)
            return False, str(e)

    def get_roku_url(self, path: str) -> Optional[str]:
        """Get full Roku URL for a given path."""
        if not self.roku_ip:
            return None
        return f"http://{self.roku_ip}:{DEFAULT_ROKU_PORT}/{path}"


roku_config = RokuConfig()

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------


def resolve_app_from_name(app_name: str) -> Optional[RokuApp]:
    """Resolve a Roku app by friendly name or alias."""
    normalized: str = app_name.strip().lower()
    for metadata in APP_CATALOG.values():
        aliases: List[str] = [metadata["display_name"].lower()] + metadata["aliases"]
        if normalized in aliases:
            return metadata
    return None


def find_app_in_command(command: str) -> Optional[RokuApp]:
    """Find a known app referenced in a voice command."""
    for metadata in APP_CATALOG.values():
        aliases: List[str] = [metadata["display_name"].lower()] + metadata["aliases"]
        if any(alias in command for alias in aliases):
            return metadata
    return None


def send_roku_command(
    command_path: str,
    method: str = "POST",
    params: Optional[Dict[str, str]] = None,
) -> Tuple[bool, str]:
    """
    Send a command to the Roku device via ECP (External Control Protocol).

    Args:
        command_path: The ECP command path (e.g., 'keypress/Home')
        method: HTTP method ('POST' or 'GET')
        params: Optional parameters

    Returns:
        Tuple of (success, message)
    """
    url: Optional[str] = roku_config.get_roku_url(command_path)

    if not url:
        return False, "Roku IP address not configured"

    try:
        if method == "POST":
            response: RequestsResponse = requests.post(url, data="" if not params else params, timeout=10)
        else:
            response: RequestsResponse = requests.get(url, params=params, timeout=10)

        response.raise_for_status()
        logger.info("Roku command '%s' successful", command_path)
        return True, "Command sent successfully"
    except requests.exceptions.ConnectTimeout:
        logger.error("Connection to Roku timed out for command '%s'", command_path)
        return False, "Connection to Roku timed out"
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error for Roku command '%s': %s", command_path, e)
        return False, "HTTP error while communicating with Roku"
    except requests.exceptions.RequestException as e:
        logger.error("Error sending Roku command '%s': %s", command_path, e)
        return False, "Error sending command to Roku"


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------


@app.route("/ROKU")
def index() -> Response:
    """Serve the main mobile interface."""
    return render_template("index.html")


@app.route("/api/config", methods=["GET", "POST"])
def config() -> Response:
    """Get or set Roku configuration."""
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "message": "Invalid or missing JSON body"}), 400

        roku_ip = data.get("roku_ip")
        if not isinstance(roku_ip, str) or not roku_ip:
            return jsonify({"success": False, "message": "Roku IP address required"}), 400

        ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        if not ip_pattern.match(roku_ip):
            return jsonify({"success": False, "message": "Invalid IP address format"}), 400

        success, msg = roku_config.save_config(roku_ip)
        if success:
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "message": "Failed to save configuration", "error": msg}), 500

    return jsonify({"success": True, "roku_ip": roku_config.roku_ip})


@app.route("/api/keypress", methods=["POST"])
def keypress() -> Response:
    """Send a keypress command to Roku."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    key = data.get("key")
    if not isinstance(key, str) or not key:
        return jsonify({"success": False, "message": "Key parameter required"}), 400

    success, message = send_roku_command(f"keypress/{key}")
    return jsonify({"success": success, "message": message})


@app.route("/api/launch", methods=["POST"])
def launch() -> Response:
    """Launch an app on Roku."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    app_id = data.get("app_id")
    app_name = data.get("app_name")

    resolved_app: Optional[RokuApp] = None
    if not app_id and isinstance(app_name, str):
        resolved_app = resolve_app_from_name(app_name)
        if resolved_app:
            app_id = resolved_app["id"]

    if not isinstance(app_id, str) or not app_id:
        success, message = send_roku_command("keypress/Home")
        return jsonify(
            {
                "success": success,
                "message": "Unknown app. Opening Home." if success else message,
            }
        ), 200 if success else 400

    display_name: str = (
        app_name
        if isinstance(app_name, str)
        else (resolved_app["display_name"] if resolved_app else "app")
    )

    success, message = send_roku_command(f"launch/{app_id}")
    return jsonify(
        {
            "success": success,
            "message": f"Launched {display_name}" if success else message,
        }
    )


@app.route("/api/voice", methods=["POST"])
def voice() -> Response:
    """Process voice commands."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    raw_command = data.get("command", "")
    command: str = raw_command.lower() if isinstance(raw_command, str) else ""

    if not command:
        return jsonify({"success": False, "message": "Command required"}), 400

    success: bool = False
    message: str = "Command not recognized"

    # Navigation commands
    if "home" in command:
        success, message = send_roku_command("keypress/Home")
    elif "back" in command:
        success, message = send_roku_command("keypress/Back")
    elif "up" in command:
        success, message = send_roku_command("keypress/Up")
    elif "down" in command:
        success, message = send_roku_command("keypress/Down")
    elif "left" in command:
        success, message = send_roku_command("keypress/Left")
    elif "right" in command:
        success, message = send_roku_command("keypress/Right")
    elif "select" in command or "ok" in command:
        success, message = send_roku_command("keypress/Select")

    # Playback commands
    elif "play" in command or "pause" in command:
        success, message = send_roku_command("keypress/Play")
    elif "rewind" in command:
        success, message = send_roku_command("keypress/Rev")
    elif "forward" in command or "fast forward" in command:
        success, message = send_roku_command("keypress/Fwd")

    # Volume commands
    elif "volume up" in command or "louder" in command:
        success, message = send_roku_command("keypress/VolumeUp")
    elif "volume down" in command or "quieter" in command:
        success, message = send_roku_command("keypress/VolumeDown")
    elif "mute" in command:
        success, message = send_roku_command("keypress/VolumeMute")

    # App launches
    else:
        resolved_app = find_app_in_command(command)
        if resolved_app:
            success, message = send_roku_command(f"launch/{resolved_app['id']}")
            message = f"Launching {resolved_app['display_name']}" if success else message
        elif any(trigger in command for trigger in ["open", "launch", "start"]):
            success, message = send_roku_command("keypress/Home")
            message = "App not recognized. Opening Home." if success else message

    return jsonify({"success": success, "message": message, "command": command})


@app.route("/api/status", methods=["GET"])
def status() -> Response:
    """Check API and Roku device status."""
    is_configured: bool = roku_config.roku_ip is not None
    roku_reachable: bool = False

    if is_configured:
        try:
            url = roku_config.get_roku_url("query/device-info")
            if url is not None:
                response: RequestsResponse = requests.get(url, timeout=3)
                roku_reachable = response.status_code == 200
        except Exception:
            roku_reachable = False

    return jsonify(
        {
            "success": True,
            "configured": is_configured,
            "roku_ip": roku_config.roku_ip,
            "roku_reachable": roku_reachable,
        }
    )


@app.route("/api/power", methods=["POST"])
def power() -> Response:
    """Toggle power on/off for Roku."""
    success, message = send_roku_command("keypress/Power")
    return jsonify({"success": success, "message": message})


@app.route("/api/roku", methods=["POST"])
def roku() -> Response:
    """Generic Roku command endpoint used by the mobile app."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    command = data.get("command")
    if not isinstance(command, str) or not command:
        return jsonify({"success": False, "message": "Command required"}), 400

    # Launch commands: "Launch:<app_id>"
    if command.startswith("Launch:"):
        app_id = command.split(":", 1)[1]
        success, message = send_roku_command(f"launch/{app_id}")
        return jsonify({"success": success, "message": message})

    # Keypress commands
    success, message = send_roku_command(f"keypress/{command}")
    return jsonify({"success": success, "message": message})


# ---------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------


@app.errorhandler(404)
def not_found(error: Exception) -> Response:
    """Handle 404 errors."""
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> Response:
    """Handle 500 errors."""
    return jsonify({"success": False, "message": "Internal server error"}), 500


# ---------------------------------------------------------
# Root Redirect
# ---------------------------------------------------------


@app.route("/")
def root() -> Response:
    """Redirect root to the mobile interface path."""
    return redirect("/ROKU")


# ---------------------------------------------------------
# Server Startup
# ---------------------------------------------------------


if __name__ == "__main__":
    cert_path = os.path.join(os.getcwd(), "cert.pem")
    key_path = os.path.join(os.getcwd(), "key.pem")

    port: int = 8443
    use_ssl: bool = os.path.exists(cert_path) and os.path.exists(key_path)
    scheme: str = "https" if use_ssl else "http"
    url: str = f"{scheme}://localhost:{port}/ROKU"

    if not use_ssl:
        logger.warning("SSL certificate or key not found. Running without HTTPS.")

    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning("Could not open browser: %s", e)

    if use_ssl:
        app.run(host="localhost", port=port, ssl_context=(cert_path, key_path))
    else:
        app.run(host="localhost", port=port)
