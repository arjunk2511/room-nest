import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_or_promote_admin():
    User = get_user_model()
    target_username = 'roomnestadmin'
    
    try:
        user = User.objects.get(username=target_username)
        print("Existing user found.")
        
        # Check if the user already has admin permissions
        if user.is_staff and user.is_superuser and user.is_active:
            print("Admin permissions already present.")
        else:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            print("Promoted to superuser.")
            
    except User.DoesNotExist:
        # Create it using the Railway environment variables
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@roomnest.online')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not password:
            print("Error: DJANGO_SUPERUSER_PASSWORD environment variable is not set. Cannot create superuser.")
            return
            
        User.objects.create_superuser(username=target_username, email=email, password=password)
        print("Superuser created.")

if __name__ == '__main__':
    create_or_promote_admin()

