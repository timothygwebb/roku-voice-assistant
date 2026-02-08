# Roku Voice Assistant - Mobile Interface

## Overview

A mobile-optimized Progressive Web App (PWA) for controlling your Roku device from any smartphone, with special optimization for iPhone 13 and iOS devices.

## Features

- **Voice Control**: Use natural voice commands to control your Roku
- **Touch Interface**: Intuitive touch controls for navigation, volume, and playback
- **App Launcher**: Quick access to popular streaming apps
- **PWA Support**: Install as a native-like app on iOS and Android
- **Responsive Design**: Optimized for mobile devices, especially iPhone 13
- **Offline Capable**: Service worker enables basic functionality offline

## Setup Instructions

### Prerequisites

1. Python 3.10 or higher
2. A Roku device on the same network
3. Roku's "Control by mobile apps" enabled (Settings → System → Advanced system settings)

## Installation

### Install Dependencies

All required dependencies are in the main repository's `requirements.txt`:

```bash
# From the repository root
pip install -r requirements.txt
```

This includes:

- Flask and Flask-CORS for the web server
- Requests library for Roku communication
- Gunicorn for production deployment (optional)

### Start the Server

```bash
cd mobile_app
python app.py
```

The server will start on `http://0.0.0.0:5000` by default.

### Mobile Device Setup

#### iPhone 13 / iOS Setup

1. **Access the App**:
   - Open Safari on your iPhone
   - Navigate to `http://[YOUR_SERVER_IP]:5000`
   - Replace `[YOUR_SERVER_IP]` with your computer's IP address

2. **Install as PWA**:
   - Tap the Share button (square with arrow)
   - Scroll down and tap "Add to Home Screen"
   - Tap "Add" to install the app icon

3. **Configure Roku**:
   - Open the app from your home screen
   - Enter your Roku device's IP address
   - Find your Roku IP: Settings → Network → About
   - Tap "Save" to store the configuration

4. **Grant Microphone Permission** (for voice control):
   - First time using voice: Tap the microphone button
   - Safari will prompt for microphone access
   - Tap "Allow" to enable voice commands

#### Android Setup

1. Open Chrome browser
2. Navigate to `http://[YOUR_SERVER_IP]:5000`
3. Tap the menu (three dots) and select "Add to Home Screen"
4. Follow the same configuration steps as iOS

## Usage

### Voice Commands

Tap the microphone button and say commands like:

- "Home" - Go to home screen
- "Back" - Go back
- "Play" / "Pause" - Control playback
- "Rewind" / "Fast forward" - Skip backward/forward
- "Volume up" / "Volume down" - Adjust volume
- "Mute" - Toggle mute
- "Open Netflix" / "Launch Hulu" - Open streaming apps
- Navigation: "Up", "Down", "Left", "Right", "Select"

### Touch Controls

- **Quick Actions**: Home, Back, Play/Pause, Select
- **D-Pad Navigation**: Directional buttons and OK button
- **Volume Controls**: Volume up/down, Mute
- **Playback Controls**: Rewind, Play/Pause, Fast Forward
- **App Launcher**: One-tap access to popular streaming apps

## API Endpoints

The mobile API server exposes the following REST endpoints:

### Configuration

- `POST /api/config` - Set Roku IP address

   ```json
   {
      "roku_ip": "192.168.1.100"
   }
   ```

- `GET /api/config` - Get current Roku IP configuration

### Control

- `POST /api/keypress` - Send keypress command

   ```json
   {
      "key": "Home"
   }
   ```

- `POST /api/launch` - Launch an app (accepts `app_id`, `app_name`, or both)

   ```json
   {
      "app_name": "Netflix"
   }
   ```

- `POST /api/voice` - Process voice command

   ```json
   {
      "command": "play Netflix"
   }
   ```

### Status

- `GET /api/status` - Check API and Roku device status

## Roku App IDs

Common streaming app IDs:

- Netflix: `12`
- Hulu: `2285`
- YouTube: `837`
- Prime Video: `13`
- Disney+: `291097`
- HBO Max: `61322`

Supported `app_name` values (case-insensitive): Netflix, Hulu, Disney+, Prime Video, YouTube, HBO Max.

To find more app IDs, visit: `http://[ROKU_IP]:8060/query/apps`

## Troubleshooting

### Cannot Connect to Roku

1. Verify both devices are on the same network
2. Check Roku IP address is correct
3. Ensure "Control by mobile apps" is enabled on Roku
4. Test connection: `curl http://[ROKU_IP]:8060/query/device-info`

### Voice Commands Not Working

1. Ensure microphone permission is granted in Safari/Chrome
2. Use a quiet environment for better recognition
3. Speak clearly and use simple commands
4. Check browser console for error messages

### App Not Installing on iOS

1. Use Safari browser (not Chrome)
2. Ensure you're using "Add to Home Screen" feature
3. iOS 11.3+ required for PWA support

### Touch Controls Not Responsive

1. Ensure JavaScript is enabled
2. Check network connection to server
3. Verify Roku device is powered on and responsive

## Production Deployment

For production use, consider:

1. **Use HTTPS**: Required for voice recognition and PWA features
   - Set up SSL certificate (Let's Encrypt recommended)
   - Configure reverse proxy (nginx/Apache)

2. **Use Production Server**: Replace Flask development server

   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Network Configuration**:
   - Configure firewall rules
   - Set up port forwarding if accessing remotely
   - Consider VPN for secure remote access

4. **Security**:
   - Implement authentication
   - Add rate limiting
   - Use environment variables for sensitive config

## Browser Compatibility

- **iOS Safari**: Full support (iOS 11.3+)
- **Chrome (Android)**: Full support
- **Chrome (Desktop)**: Full support
- **Firefox**: Partial support (no voice recognition)
- **Edge**: Full support

## iOS-Specific Features

- PWA installation support
- Add to Home Screen
- Standalone display mode
- Status bar styling
- Safe area support for notched devices
- Touch-optimized interface
- Voice recognition via WebKit Speech API

## Development

To modify the mobile interface:

1. **Frontend**: Edit files in `mobile_app/static/` and `mobile_app/templates/`
   - `app.js` - JavaScript functionality
   - `styles.css` - Styling and layout
   - `index.html` - HTML structure

2. **Backend**: Edit `mobile_app/app.py`
   - Add new API endpoints
   - Modify Roku command handling
   - Extend voice command processing

3. **Testing**: Use browser developer tools
   - iOS: Safari Web Inspector
   - Android: Chrome DevTools

## Contributing

This project is part of the Roku Voice Assistant repository. For issues and questions, please open an issue on GitHub.
