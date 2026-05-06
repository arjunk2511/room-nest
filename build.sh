#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building for Render..."
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
echo "Build complete."
