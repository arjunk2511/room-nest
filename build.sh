#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building for Render..."
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations
# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --fake-initial

# Create non-interactive Django superuser securely using Render environment variables
echo "Checking superuser requirements..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@roomnest.online')
if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print('Superuser created successfully.')
    else:
        print('Superuser already exists.')
else:
    print('Superuser environment variables are not set. Skipping creation.')
"

echo "Build complete."
