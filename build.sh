#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building for Render..."
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations
# Run database migrations with self-healing fail-safe
echo "Applying database migrations..."
if ! python manage.py migrate; then
    echo "WARNING: Standard migration failed due to existing database schema mismatch. Initiating self-healing..."
    # Fake core listings migrations since columns already exist in PostgreSQL
    python manage.py migrate listings 0007 --fake || true
    python manage.py migrate listings 0008 --fake || true
    # Retry the migration process
    echo "Retrying database migrations..."
    python manage.py migrate
fi

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
