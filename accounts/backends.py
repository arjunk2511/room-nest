from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import UserProfile
from django.db.models import Q

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Check if username is an email, phone number, or standard username
            user = User.objects.get(
                Q(email=username) | 
                Q(userprofile__phone_number=username) | 
                Q(username=username)
            )
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                Q(email=username) | 
                Q(userprofile__phone_number=username) | 
                Q(username=username)
            ).first()
            if user.check_password(password):
                return user
        return None
