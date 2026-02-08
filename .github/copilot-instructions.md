# Copilot Instructions for Roku Voice Assistant

## Project Architecture
- **Alexa Integration**: AWS Lambda function (`lambda_function.py`) using Alexa Skills Kit SDK. Handles voice commands for Roku control.
- **Mobile App**: Located in `mobile_app/`. Progressive Web App (PWA) optimized for iPhone 13/iOS, provides touch and voice control. Backend server exposes REST API endpoints.
- **REST API**: Mobile app backend exposes endpoints for Roku control, app launching, voice processing, and device configuration.
- **SDKs**: Alexa SDK modules are vendored in the `venv/` directory for Lambda deployment packaging.

## Developer Workflows
- **Install dependencies**: `pip install -r requirements.txt`
- **Mobile App server**: `cd mobile_app && python app.py` (see `mobile_app/README.md` for details)
- **Alexa Lambda deployment**: Deploy `lambda_function.py` to AWS Lambda after configuring AWS credentials.
- **Testing & CI**: CI workflow in `.github/workflows/voice-ci.yml` handles build and dependency checks. CodeQL security scanning via GitHub default setup.

## Project-Specific Patterns
- **Roku IP Configuration**: Set Roku device IP via mobile app or Alexa skill configuration.
- **API Endpoints**: Mobile app backend provides `/api/keypress`, `/api/launch`, `/api/voice`, `/api/config`, `/api/status`.
- **Alexa Skill**: Uses Alexa SDK modules for request/response handling (vendored in venv/ for Lambda packaging).
- **Mobile App**: Designed for iOS, but works cross-platform. Uses native speech recognition and touch controls.

## Integration Points
- **Roku Device**: Controlled via local network; ensure "Control by mobile apps" is enabled on Roku.
- **AWS Lambda**: Alexa skill backend must be deployed to AWS Lambda.
- **Mobile App**: Access via browser at `http://[YOUR_SERVER_IP]:5000`.

## Key Files & Directories
- [lambda_function.py]: Alexa skill entry point
- [mobile_app/]: Mobile app source and backend
- [venv/]: Contains Alexa SDK dependencies for Lambda deployment
- [requirements.txt]: Python dependencies
- [.github/workflows/]: CI/CD workflows

## Examples
- To launch Netflix via Alexa: "Alexa, ask Roku to open Netflix"
- To send a keypress via API: `POST /api/keypress` with JSON `{ "key": "Home" }`
- To start the mobile app server: `cd mobile_app && python app.py`

---

**For unclear or incomplete sections, please provide feedback or request more details.**
