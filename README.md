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

## Requirements

### Alexa Integration (Lambda)

- Python 3.10+
- AWS account with Lambda access
- Roku device with "Control by mobile apps" enabled

Core Python package dependencies (from `requirements.txt`):

- boto3 (AWS SDK)
- requests (HTTP client)

Alexa SDK functionality for the Lambda skill is vendored in this repository under the legacy virtualenv at `venv/lib/python2.7/site-packages/`. That directory is **only** used when building the Lambda deployment ZIP (it is bundled alongside `lambda_function.py`) and is not intended to be your local Python 3.10+ virtual environment.

If you want to run `lambda_function.py` locally with Python 3.10+ (for example, to debug the Alexa skill), you must either:

- Install the Alexa SDK packages into your local environment (recommended), e.g.:
  - `ask_sdk_core`
  - `ask_sdk_model`
  - `ask_sdk_runtime`
  - `ask_sdk_dynamodb`

  or

- Temporarily add the vendored site-packages directory (`venv/lib/python2.7/site-packages/`) to your `PYTHONPATH` so that `ask_sdk_*` modules can be imported.

The Alexa SDK is therefore **not** listed in `requirements.txt`; that file only covers shared/core dependencies and the mobile app/backend server dependencies for local development.
### Mobile App

- Python 3.10+
- Flask and related dependencies (included in `requirements.txt`)

All dependencies can be installed with:

```bash
pip install -r requirements.txt
```

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
2. Set up a Python 3.10+ virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure your Roku device IP address in `lambda_function.py`:
   - Open `lambda_function.py`
   - Replace `YOUR_ROKU_IP_ADDRESS` with your Roku's IP address
   - Find your Roku IP: Settings → Network → About

5. Configure your AWS credentials.
6. Create a deployment package with all dependencies.
7. Deploy `lambda_function.py` to AWS Lambda.

## Usage

### Mobile App

- **Voice Commands**: "Play", "Pause", "Open Netflix", "Volume up", etc.
- **Touch Controls**: D-pad navigation, volume buttons, app shortcuts
- **Configuration**: Set Roku IP in the app settings

### Alexa

Use Alexa to invoke your custom skill and control your Roku device:

**Supported Commands:**

- **App launching**: "Alexa, ask Roku to open Netflix"
- **Playback control**: "Alexa, ask Roku to play", "Alexa, ask Roku to pause"
- **Volume control**: "Alexa, ask Roku to turn up the volume", "Alexa, ask Roku to mute"
- **Navigation**: "Alexa, ask Roku to go home", "Alexa, ask Roku to go back"
- **Search**: "Alexa, ask Roku to search for [content]" (opens home screen for manual search)

Note: Configure your Roku IP in `lambda_function.py` before deploying to AWS Lambda.

## API Endpoints

The mobile API server provides REST endpoints:

- `POST /api/keypress` - Send remote control commands (e.g., `{"key": "Home"}`)
- `POST /api/launch` - Launch streaming apps (e.g., `{"app_name": "Netflix"}`)
- `POST /api/voice` - Process voice commands (e.g., `{"command": "play"}`)
- `POST /api/config` - Configure Roku IP address (e.g., `{"roku_ip": "192.168.1.100"}`)
- `GET /api/config` - Get current Roku IP configuration
- `GET /api/status` - Check API and Roku device status

See [mobile_app/README.md](mobile_app/README.md) for complete API documentation.

## Testing & CI

- **Security**: Automated security scanning with CodeQL (via GitHub default setup)
- **CI Workflows**: See `.github/workflows/` for automated checks
  - `voice-ci.yml`: Environment setup and dependency installation (Python and ffmpeg)

CodeQL security scanning is configured through GitHub's repository settings (Security > Code security and analysis) and runs automatically on push and pull requests.

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
- [x] Streaming app support (Netflix, Hulu, Disney+, Prime Video, YouTube, HBO Max)
- [x] Voice command processing
- [x] Error handling and timeout improvements
- [ ] Integrate Google Assistant
- [ ] Add authentication to mobile API
- [ ] Support for custom Roku app configurations
- [ ] Expand voice command vocabulary
