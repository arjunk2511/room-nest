import os
import subprocess
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from listings.models import Listing, ListingImage
from roomnest.production_safety import verify_cloudinary_connection


@staff_member_required
def system_health_view(request):
    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    User = get_user_model()
    db_engine = settings.DATABASES['default'].get('ENGINE', 'unknown')
    db_name = settings.DATABASES['default'].get('NAME', 'unknown')
    db_status = 'Connected'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        db_status = 'Disconnected'

    recorder = MigrationRecorder(connection)
    applied_migrations = recorder.applied_migrations()
    last_migration = str(applied_migrations[-1][0]) if applied_migrations else 'None'

    cloud_status, cloud_message = verify_cloudinary_connection()
    counts = {
        'users': User.objects.count(),
        'owners': Listing.objects.values('owner').distinct().count(),
        'listings': Listing.objects.count(),
        'images': ListingImage.objects.count(),
    }

    context = {
        'db_engine': db_engine,
        'db_name': db_name,
        'db_status': db_status,
        'counts': counts,
        'last_migration': last_migration,
        'git_commit': os.environ.get('HEROKU_SLUG_COMMIT') or os.environ.get('RAILWAY_GIT_COMMIT') or 'local',
        'railway_environment': os.environ.get('RAILWAY_ENVIRONMENT', 'local'),
        'cloudinary_status': cloud_message if cloud_status else 'Not configured',
        'last_deployment_time': os.environ.get('LAST_DEPLOYMENT_TIME') or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
    }
    return render(request, 'admin/system_health.html', context)
