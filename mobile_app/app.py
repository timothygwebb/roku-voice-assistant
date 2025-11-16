"""
Flask API server for Roku Voice Assistant mobile interface.
Provides REST API endpoints for controlling Roku devices from mobile apps.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import logging
import os
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Enable CORS for mobile app access
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
CONFIG_FILE = 'config.json'
DEFAULT_ROKU_PORT = 8060

class RokuConfig:
    """Manages Roku device configuration"""
    def __init__(self):
        self.roku_ip = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.roku_ip = config.get('roku_ip')
                    logger.info(f"Loaded config: Roku IP = {self.roku_ip}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
    
    def save_config(self, roku_ip):
        """Save configuration to file"""
        self.roku_ip = roku_ip
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'roku_ip': roku_ip}, f)
            logger.info(f"Saved config: Roku IP = {roku_ip}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_roku_url(self, path):
        """Get full Roku URL for a given path"""
        if not self.roku_ip:
            return None
        return f"http://{self.roku_ip}:{DEFAULT_ROKU_PORT}/{path}"

# Global configuration instance
roku_config = RokuConfig()

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
            response = requests.post(url, data="" if not params else params, timeout=5)
        else:
            response = requests.get(url, params=params, timeout=5)
        
        response.raise_for_status()
        logger.info(f"Roku command '{command_path}' successful")
        return True, "Command sent successfully"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Roku command '{command_path}': {e}")
        return False, str(e)

# Routes

@app.route('/')
def index():
    """Serve the main mobile interface"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or set Roku configuration"""
    if request.method == 'POST':
        data = request.get_json()
        roku_ip = data.get('roku_ip')
        
        if not roku_ip:
            return jsonify({'success': False, 'message': 'Roku IP address required'}), 400
        
        # Validate IP format
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        if not ip_pattern.match(roku_ip):
            return jsonify({'success': False, 'message': 'Invalid IP address format'}), 400
        
        if roku_config.save_config(roku_ip):
            return jsonify({'success': True, 'message': 'Configuration saved'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
    
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
    app_name = data.get('app_name', 'app')
    
    if not app_id:
        return jsonify({'success': False, 'message': 'App ID required'}), 400
    
    success, message = send_roku_command(f"launch/{app_id}")
    
    return jsonify({
        'success': success,
        'message': f"Launched {app_name}" if success else message
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
    elif 'netflix' in command:
        success, message = send_roku_command('launch/12')
        message = "Launching Netflix" if success else message
    elif 'hulu' in command:
        success, message = send_roku_command('launch/2285')
        message = "Launching Hulu" if success else message
    elif 'youtube' in command:
        success, message = send_roku_command('launch/837')
        message = "Launching YouTube" if success else message
    elif 'prime' in command or 'amazon' in command:
        success, message = send_roku_command('launch/13')
        message = "Launching Prime Video" if success else message
    elif 'disney' in command:
        success, message = send_roku_command('launch/291097')
        message = "Launching Disney+" if success else message
    
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

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the server
    # For production, use a proper WSGI server like gunicorn
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
