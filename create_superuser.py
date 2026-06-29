import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if not username or not password:
        print("Superuser environment variables (DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD) are not set. Skipping.")
        return

    if User.objects.filter(username=username).exists():
        print(f"Superuser '{username}' already exists. Skipping creation.")
    else:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully.")

if __name__ == '__main__':
    create_superuser()
