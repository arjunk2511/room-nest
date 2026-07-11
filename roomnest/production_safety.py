import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.utils import OperationalError
from django.conf import settings


def validate_database_configuration(config, is_production=False, database_url=None):
    if is_production and config.get('ENGINE') == 'django.db.backends.sqlite3':
        raise ImproperlyConfigured('SQLite database cannot be used in production.')
    if is_production and not database_url and not os.environ.get('PGHOST'):
        raise ImproperlyConfigured('Production requires PostgreSQL configuration.')
    return config


def verify_static_files(base_dir=None):
    base_dir = Path(base_dir or settings.BASE_DIR)
    required_paths = [base_dir / 'static', base_dir / 'staticfiles']
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f'Missing required static paths: {missing}')
    return True


def verify_cloudinary_connection():
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    api_key = os.environ.get('CLOUDINARY_API_KEY', '')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')
    if not all([cloud_name, api_key, api_secret]) or any(v in {'your_cloud_name_here', 'your_api_key_here', 'your_api_secret_here'} for v in [cloud_name, api_key, api_secret]):
        return False, 'Cloudinary credentials are not configured.'
    return True, 'Cloudinary credentials configured.'


def run_production_verification():
    log_lines = []
    timestamp = datetime.utcnow().isoformat()

    from django.contrib.auth import get_user_model
    from django.db.migrations.recorder import MigrationRecorder
    from listings.models import Listing, ListingImage

    User = get_user_model()
    baseline_counts = {
        'users': User.objects.count(),
        'owners': Listing.objects.values('owner').distinct().count(),
        'listings': Listing.objects.count(),
        'images': ListingImage.objects.count(),
    }
    log_lines.append(f'[{timestamp}] Deployment Started')
    log_lines.append(f'[{timestamp}] Total Users: {baseline_counts["users"]}')
    log_lines.append(f'[{timestamp}] Total Listings: {baseline_counts["listings"]}')
    log_lines.append(f'[{timestamp}] Total Images: {baseline_counts["images"]}')

    try:
        validate_database_configuration(
            settings.DATABASES['default'],
            is_production=getattr(settings, 'IS_PRODUCTION', False),
            database_url=os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL'),
        )
        log_lines.append(f'[{timestamp}] Database Connected')
    except Exception as exc:
        raise RuntimeError(f'Production database verification failed: {exc}') from exc

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    try:
        table_names = connection.introspection.table_names()
        required_tables = ['auth_user', 'listings_listing', 'django_migrations']
        missing = [table for table in required_tables if table not in table_names]
        if missing:
            raise RuntimeError(f'Missing required tables: {missing}')
    except Exception as exc:
        raise RuntimeError(f'Table verification failed: {exc}') from exc

    try:
        recorder = MigrationRecorder(connection)
        applied_migrations = recorder.applied_migrations()
        if not applied_migrations:
            raise RuntimeError('No migrations were found in django_migrations.')
        last_migration = str(applied_migrations[-1][0]) if applied_migrations else 'None'
    except Exception as exc:
        raise RuntimeError(f'Migration verification failed: {exc}') from exc

    try:
        verify_static_files()
    except Exception as exc:
        raise RuntimeError(f'Static files verification failed: {exc}') from exc

    cloud_status, cloud_message = verify_cloudinary_connection()
    if not cloud_status:
        raise RuntimeError(f'Cloudinary verification failed: {cloud_message}')

    counts = {
        'users': User.objects.count(),
        'owners': Listing.objects.values('owner').distinct().count(),
        'listings': Listing.objects.count(),
        'images': ListingImage.objects.count(),
    }

    log_lines.append(f'[{timestamp}] Migration Status: {last_migration}')
    log_lines.append(f'[{timestamp}] Total Users: {counts["users"]}')
    log_lines.append(f'[{timestamp}] Total Listings: {counts["listings"]}')
    log_lines.append(f'[{timestamp}] Total Images: {counts["images"]}')
    for metric in ('users', 'listings', 'images'):
        if counts[metric] < baseline_counts[metric]:
            log_lines.append(f'[{timestamp}] WARNING: {metric} count decreased unexpectedly from {baseline_counts[metric]} to {counts[metric]}')
    log_lines.append(f'[{timestamp}] Deployment Finished')

    log_path = Path(settings.BASE_DIR) / 'production_logs.txt'
    with log_path.open('a', encoding='utf-8') as handle:
        handle.write('\n'.join(log_lines) + '\n')

    return {
        'last_migration': last_migration,
        'counts': counts,
        'cloud_message': cloud_message,
        'log_path': str(log_path),
    }
