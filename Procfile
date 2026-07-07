web: python manage.py migrate --no-input && python verify_production_db.py && python create_superuser.py && python verify_deployment.py && gunicorn roomnest.wsgi:application
