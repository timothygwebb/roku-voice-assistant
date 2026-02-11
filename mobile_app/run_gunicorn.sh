#!/bin/bash
# Run the Roku Voice Assistant Flask API using Gunicorn (recommended for production)
# Usage: ./run_gunicorn.sh

cd "$(dirname "$0")"
gunicorn -b 0.0.0.0:5000 app:app
