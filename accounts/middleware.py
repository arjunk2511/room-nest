import os
import requests
from django.contrib.auth.models import User
from accounts.models import UserProfile

class SupabaseAuthMiddleware:
    """
    Middleware that intercepts requests with a Supabase Bearer token,
    validates the token with Supabase Auth, and associates the request with the 
    corresponding Django User.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            parts = auth_header.split(' ')
            if len(parts) == 2:
                token = parts[1]
                user_data = self.get_supabase_user(token)
                if user_data:
                    email = user_data.get('email')
                    if email:
                        try:
                            user = User.objects.get(email=email)
                        except User.DoesNotExist:
                            # Create a Django user corresponding to the Supabase email
                            username = email.split('@')[0]
                            base_username = username
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}_{counter}"
                                counter += 1
                            
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=User.objects.make_random_password()
                            )
                            # Initialize UserProfile
                            UserProfile.objects.get_or_create(user=user)
                        
                        request.user = user

        return self.get_response(request)

    def get_supabase_user(self, token):
        # Read Supabase settings from environment
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            # Support mock authentication in local development mode
            if token == 'dev_admin':
                return {"email": "admin@roomnest.online"}
            elif token.startswith('dev_user_'):
                username = token.replace('dev_user_', '')
                return {"email": f"{username}@roomnest.online"}
            elif token == 'dev_user':
                return {"email": "temp_owner@roomnest.online"}
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": supabase_anon_key
        }
        try:
            response = requests.get(f"{supabase_url}/auth/v1/user", headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Supabase token validation error: {e}")
        return None
