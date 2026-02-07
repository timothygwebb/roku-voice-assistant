# Roku Voice Assistant

## Overview

Roku Voice Assistant lets you control your Roku device(s) using voice commands through multiple interfaces:

- **Alexa Integration**: AWS Lambda function with Alexa Skills Kit
- **Mobile App**: Progressive Web App optimized for iPhone 13 and iOS devices
- **REST API**: Backend server for mobile and web integration

## Features

### Alexa Integration

- Control Roku via voice through Alexa devices
- Launch apps, control playback, adjust volume
- Search and play content

### Mobile App (NEW!)

- 📱 **iPhone 13 Optimized**: Responsive design with iOS-specific features
- 🎤 **Voice Control**: Native speech recognition for voice commands
- 📲 **PWA Support**: Install as a native-like app on iOS/Android
- 🎮 **Touch Controls**: Intuitive interface for navigation and control
- 🚀 **Quick App Launch**: One-tap access to streaming services
- 🌐 **Cross-Platform**: Works on any modern mobile browser

## Quick Start

### Mobile App Setup (iPhone 13 / iOS)

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the mobile server**:

   ```bash
   cd mobile_app
   python app.py
   ```

3. **Access from iPhone**:
   - Open Safari and go to `http://[YOUR_SERVER_IP]:5000`
   - Tap Share → "Add to Home Screen"
   - Open the app and configure your Roku IP address

4. **Enable Roku control**:
   - On your Roku: Settings → System → Advanced → "Control by mobile apps"
   - Find Roku IP: Settings → Network → About

📖 **Full mobile documentation**: See [mobile_app/README.md](mobile_app/README.md)

### Alexa Integration Setup

1. Clone this repo.
2. Set up a Python 3.11+ virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure your AWS credentials.
5. Deploy `lambda_function.py` to AWS Lambda.

## Usage

### Mobile App

- **Voice Commands**: "Play", "Pause", "Open Netflix", "Volume up", etc.
- **Touch Controls**: D-pad navigation, volume buttons, app shortcuts
- **Configuration**: Set Roku IP in the app settings

### Alexa

- Use Alexa to invoke your custom skill and control your Roku TV
- Supported commands: Power on/off, volume control, app launching

## API Endpoints

The mobile API server provides REST endpoints:

- `POST /api/keypress` - Send remote control commands
- `POST /api/launch` - Launch streaming apps
- `POST /api/voice` - Process voice commands
- `POST /api/config` - Configure Roku IP address
- `GET /api/status` - Check device status

See [mobile_app/README.md](mobile_app/README.md) for complete API documentation.

## Testing & CI

- Code style is checked via Flake8 and Black.
- Security scanning is automated by Bandit.
- See `.github/workflows/*` for CI details.

## Browser Compatibility (Mobile App)

- ✅ iOS Safari 11.3+ (iPhone 13 fully supported)
- ✅ Chrome (Android)
- ✅ Chrome (Desktop)
- ⚠️ Firefox (limited voice support)
- ✅ Edge

## Roadmap

- [x] Mobile-friendly web interface
- [x] iOS/iPhone 13 optimization
- [x] REST API for mobile communication
- [x] Progressive Web App (PWA) support
- [x] Add streaming app support.
- [ ] Integrate Google Assistant.
- [ ] Improve error handling and logging.
- [ ] Expand documentation.
