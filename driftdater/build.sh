#!/usr/bin/env bash
# build.sh
# --------
# Render runs this as the Build Command for the backend service.
# Installs Python dependencies then applies any pending database migrations.
set -o errexit   # Exit immediately if any command fails

pip install -r requirements.txt
flask --app app db upgrade
