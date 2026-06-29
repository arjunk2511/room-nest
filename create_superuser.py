import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    print("=== Creating Django Superuser ===")
    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if not username or not password:
        print("Missing environment variables")
        return

    if User.objects.filter(username=username).exists():
        print("Superuser already exists")
    else:
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superuser created successfully")

if __name__ == '__main__':
    create_superuser()
