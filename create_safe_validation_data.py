import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.core.management import call_command

def ensure_validation_data():
    print("Ensuring validation/test data is cleared from the active database...")
    call_command('cleanup_validation_data', noinput=True)

if __name__ == '__main__':
    ensure_validation_data()
