"""
Flask API server for Roku Voice Assistant mobile interface.
Provides REST API endpoints for controlling Roku devices from mobile apps.
"""

from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import requests
import logging
import os
import json
import errno
import re
import webbrowser
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom logging filter to suppress SSL/TLS handshake errors on HTTP server
class SuppressSSLHandshakeFilter(logging.Filter):
    """Filter to suppress SSL/TLS handshake error messages in werkzeug logs.
    
    When clients attempt HTTPS connections to the HTTP server, werkzeug logs
    'Bad request version' and 'Bad HTTP/0.9 request type' errors. These are
    harmless but create log noise. This filter suppresses them.
    """
    def filter(self, record):
        # Suppress SSL/TLS handshake errors (starts with \x16\x03 in hex)
        # Werkzeug generates two log messages for SSL handshake attempts:
        # 1. ERROR: "code 400, message Bad request syntax ('\x16\x03...')"
        # 2. INFO: '"\x16\x03..." 400 -'
        message = record.getMessage()
        
        # Check for SSL/TLS handshake patterns in various forms
        # (literal bytes, raw string, or double-escaped)
        if '\x16\x03' in message or r'\x16\x03' in message or '\\x16\\x03' in message:
            return False  # Suppress SSL/TLS handshake errors
        
        return True  # Allow other messages

# Apply the filter to werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(SuppressSSLHandshakeFilter())

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Enable CORS for mobile app access
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_ROKU_PORT = 8060

APP_CATALOG = {
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

class RokuConfig:
    """Manages Roku device configuration"""
    def __init__(self):
        self.roku_ip = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.roku_ip = config.get('roku_ip')
                        logger.info("Loaded config: Roku IP = %s", self.roku_ip)
                except json.JSONDecodeError:
                    # Backup corrupted config and create a fresh one
                    try:
                        corrupt_backup = CONFIG_FILE + ".corrupt_" + (os.path.getmtime(CONFIG_FILE) and str(int(os.path.getmtime(CONFIG_FILE))))
                        os.replace(CONFIG_FILE, corrupt_backup)
                        logger.warning("Config file was corrupted. Backed up to %s and creating a fresh config.", corrupt_backup)
                    except Exception:
                        logger.exception("Failed to back up corrupted config file %s", CONFIG_FILE)
                    # create default
                    try:
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump({}, f)
                        self.roku_ip = None
                        logger.info("Created new default config at %s", CONFIG_FILE)
                    except Exception:
                        logger.exception("Failed to create default config at %s", CONFIG_FILE)
            else:
                # Create a safe default config file so later saves are more likely to succeed
                try:
                    dirpath = os.path.dirname(CONFIG_FILE)
                    if dirpath and not os.path.exists(dirpath):
                        os.makedirs(dirpath, exist_ok=True)
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    logger.info("Config file not found. Created default config at %s", CONFIG_FILE)
                except Exception:
                    logger.exception("Failed to create default config at %s", CONFIG_FILE)

            # Log file permission info to help diagnose save failures
            try:
                exists = os.path.exists(CONFIG_FILE)
                readable = os.access(CONFIG_FILE, os.R_OK)
                writable = os.access(CONFIG_FILE, os.W_OK)
                st = os.stat(CONFIG_FILE) if exists else None
                logger.info("Config path=%s exists=%s readable=%s writable=%s stat=%s", CONFIG_FILE, exists, readable, writable, st)
            except Exception:
                logger.debug("Could not stat or access config file %s", CONFIG_FILE)
        except Exception:
            logger.exception("Error loading config from %s", CONFIG_FILE)
    
    def save_config(self, roku_ip):
        """Save configuration to file. Returns (success, message)."""
        self.roku_ip = roku_ip
        try:
            # Ensure directory exists
            dirpath = os.path.dirname(CONFIG_FILE)
            if dirpath and not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({'roku_ip': roku_ip}, f, indent=2)
            logger.info("Saved config: Roku IP = %s (to %s)", roku_ip, CONFIG_FILE)
            return True, "Configuration saved"
        except Exception as e:
            # Map common errors to friendlier messages
            logger.exception("Error saving config to %s", CONFIG_FILE)
            if isinstance(e, PermissionError):
                return False, f"Permission denied writing to config file {CONFIG_FILE}. Check file permissions or run as a user that can write to this path."
            if isinstance(e, OSError):
                if getattr(e, 'errno', None) == errno.ENOSPC:
                    return False, f"No space left on device when writing {CONFIG_FILE}. Free disk space and try again."
                if getattr(e, 'errno', None) == errno.EACCES:
                    return False, f"Access denied when writing {CONFIG_FILE}. Check file permissions."
            # Generic inspection for locked file (Windows common message)
            msg = str(e)
            if 'used by another process' in msg or 'being used by another process' in msg:
                return False, f"Config file appears locked by another process: {msg}"
            return False, msg
    
    def get_roku_url(self, path):
        """Get full Roku URL for a given path"""
        if not self.roku_ip:
            return None
        return f"http://{self.roku_ip}:{DEFAULT_ROKU_PORT}/{path}"

# Global configuration instance
roku_config = RokuConfig()

def resolve_app_from_name(app_name):
    """Resolve a Roku app by friendly name or alias."""
    normalized = app_name.strip().lower()
    for metadata in APP_CATALOG.values():
        aliases = [metadata["display_name"].lower()] + metadata["aliases"]
        if normalized in aliases:
            return metadata
    return None

def find_app_in_command(command):
    """Find a known app referenced in a voice command."""
    for metadata in APP_CATALOG.values():
        aliases = [metadata["display_name"].lower()] + metadata["aliases"]
        if any(alias in command for alias in aliases):
            return metadata
    return None

def send_roku_command(command_path, method="POST", params=None):
    """
    Send a command to the Roku device via ECP (External Control Protocol).
    
    Args:
        command_path: The ECP command path (e.g., 'keypress/Home')
        method: HTTP method ('POST' or 'GET')
        params: Optional parameters
    
    Returns:
        Tuple of (success, message)
    """
    url = roku_config.get_roku_url(command_path)
    
    if not url:
        return False, "Roku IP address not configured"
    
    try:
        if method == "POST":
            response = requests.post(url, data="" if not params else params, timeout=10)  # Increased timeout to 10 seconds
        else:
            response = requests.get(url, params=params, timeout=10)  # Increased timeout to 10 seconds
        
        response.raise_for_status()
        logger.info(f"Roku command '{command_path}' successful")
        return True, "Command sent successfully"
    
    except requests.exceptions.ConnectTimeout:
        logger.error(f"Connection to Roku timed out for command '{command_path}'")
        return False, "Connection to Roku timed out"

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for Roku command '{command_path}': {e}")
        return False, "HTTP error while communicating with Roku"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Roku command '{command_path}': {e}")
        return False, "Error sending command to Roku"

# Routes

@app.route('/ROKU')
def index():
    """Serve the main mobile interface"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or set Roku configuration"""
    if request.method == 'POST':
        # Try to get JSON body, allow silent failure and fallback to raw body parsing
        data = request.get_json(silent=True)
        if not data:
            try:
                raw = request.data or b''
                if raw:
                    data = json.loads(raw.decode('utf-8'))
                else:
                    data = None
            except Exception:
                data = None

        if not data:
            return jsonify({'success': False, 'message': 'Invalid or missing JSON body'}), 400

        roku_ip = data.get('roku_ip')
        
        if not roku_ip:
            return jsonify({'success': False, 'message': 'Roku IP address required'}), 400
        
        # Validate IP format
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        if not ip_pattern.match(roku_ip):
            return jsonify({'success': False, 'message': 'Invalid IP address format'}), 400
        
        success, msg = roku_config.save_config(roku_ip)
        if success:
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration', 'error': msg}), 500
    
    else:  # GET
        return jsonify({
            'success': True,
            'roku_ip': roku_config.roku_ip
        })

@app.route('/api/keypress', methods=['POST'])
def keypress():
    """Send a keypress command to Roku"""
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({'success': False, 'message': 'Key parameter required'}), 400
    
    success, message = send_roku_command(f"keypress/{key}")
    
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/api/launch', methods=['POST'])
def launch():
    """Launch an app on Roku"""
    data = request.get_json()
    app_id = data.get('app_id')
    app_name = data.get('app_name')

    resolved_app = None
    if not app_id and app_name:
        resolved_app = resolve_app_from_name(app_name)
        if resolved_app:
            app_id = resolved_app["id"]

    if not app_id:
        success, message = send_roku_command('keypress/Home')
        return jsonify({
            'success': success,
            'message': "Unknown app. Opening Home." if success else message
        }), 200 if success else 400

    display_name = (
        app_name
        or (resolved_app["display_name"] if resolved_app else None)
        or "app"
    )
    success, message = send_roku_command(f"launch/{app_id}")

    return jsonify({
        'success': success,
        'message': f"Launched {display_name}" if success else message
    })

@app.route('/api/voice', methods=['POST'])
def voice():
    """Process voice commands"""
    data = request.get_json()
    command = data.get('command', '').lower()
    
    if not command:
        return jsonify({'success': False, 'message': 'Command required'}), 400
    
    # Parse voice commands and map to Roku actions
    success = False
    message = "Command not recognized"
    
    # Navigation commands
    if 'home' in command:
        success, message = send_roku_command('keypress/Home')
    elif 'back' in command:
        success, message = send_roku_command('keypress/Back')
    elif 'up' in command:
        success, message = send_roku_command('keypress/Up')
    elif 'down' in command:
        success, message = send_roku_command('keypress/Down')
    elif 'left' in command:
        success, message = send_roku_command('keypress/Left')
    elif 'right' in command:
        success, message = send_roku_command('keypress/Right')
    elif 'select' in command or 'ok' in command:
        success, message = send_roku_command('keypress/Select')
    
    # Playback commands
    elif 'play' in command or 'pause' in command:
        success, message = send_roku_command('keypress/Play')
    elif 'rewind' in command:
        success, message = send_roku_command('keypress/Rev')
    elif 'forward' in command or 'fast forward' in command:
        success, message = send_roku_command('keypress/Fwd')
    
    # Volume commands
    elif 'volume up' in command or 'louder' in command:
        success, message = send_roku_command('keypress/VolumeUp')
    elif 'volume down' in command or 'quieter' in command:
        success, message = send_roku_command('keypress/VolumeDown')
    elif 'mute' in command:
        success, message = send_roku_command('keypress/VolumeMute')
    
    # App launches
    else:
        resolved_app = find_app_in_command(command)
        if resolved_app:
            success, message = send_roku_command(f"launch/{resolved_app['id']}")
            message = (
                f"Launching {resolved_app['display_name']}" if success else message
            )
        elif any(trigger in command for trigger in ["open", "launch", "start"]):
            success, message = send_roku_command('keypress/Home')
            message = "App not recognized. Opening Home." if success else message
    
    return jsonify({
        'success': success,
        'message': message,
        'command': command
    })

@app.route('/api/status', methods=['GET'])
def status():
    """Check API and Roku device status"""
    is_configured = roku_config.roku_ip is not None
    roku_reachable = False
    
    if is_configured:
        try:
            url = roku_config.get_roku_url('query/device-info')
            response = requests.get(url, timeout=3)
            roku_reachable = response.status_code == 200
        except:
            pass
    
    return jsonify({
        'success': True,
        'configured': is_configured,
        'roku_ip': roku_config.roku_ip,
        'roku_reachable': roku_reachable
    })

@app.route('/api/power', methods=['POST'])
def power():
    """Toggle power on/off for Roku"""
    success, message = send_roku_command("keypress/Power")

    return jsonify({
        'success': success,
        'message': message
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/')
def root():
    """Redirect root to the mobile interface path"""
    return redirect('/ROKU')


# Update to dynamically open the correct URL with /ROKU path
if __name__ == '__main__':
    # Path to SSL certificate and key files
    cert_path = os.path.join(os.getcwd(), 'cert.pem')
    key_path = os.path.join(os.getcwd(), 'key.pem')

    port = 8443
    use_ssl = os.path.exists(cert_path) and os.path.exists(key_path)
    scheme = 'https' if use_ssl else 'http'
    url = f"{scheme}://localhost:{port}/ROKU"

    if not use_ssl:
        logger.warning('SSL certificate or key not found. Running without HTTPS.')

    # Open the browser to the correct URL before starting the server
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning('Could not open browser: %s', e)

    if use_ssl:
        app.run(host='localhost', port=port, ssl_context=(cert_path, key_path))
    else:
        app.run(host='localhost', port=port)
