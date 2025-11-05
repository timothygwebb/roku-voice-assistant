# Roku Voice Assistant

## Overview

Roku Voice Assistant lets you control your Roku device(s) using voice commands integrated via AWS Lambda and Alexa Skills Kit.

## Setup

1. Clone this repo.
2. Set up a Python 3.11+ virtual environment.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure your AWS credentials.
5. Deploy `lambda_function.py` to AWS Lambda.

## Usage

- Use Alexa to invoke your custom skill and control your Roku TV via API calls in `lambda_function.py`.
- Supported commands: Power on/off, volume control, app launching.

## Testing & CI

- Code style is checked via Flake8 and Black.
- Security scanning is automated by Bandit.
- See `.github/workflows/*` for CI details.

## Roadmap

- [ ] Add streaming app support.
- [ ] Integrate Google Assistant.
- [ ] Improve error handling and logging.
- [ ] Expand documentation.