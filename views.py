from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Subscription
from django.utils import timezone
import datetime
from django.contrib import messages

@login_required
def subscribe(request):
    if request.method == 'POST':
        # Create an inactive subscription (optional) or just redirect
        # The user will pay via WhatsApp, and the admin will manually activate
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'is_active': False, 'end_date': timezone.now() + datetime.timedelta(days=90)}
        )
        
        # WhatsApp Redirection
        owner_whatsapp = "919000000000" # NOTE: User must change this to their actual WhatsApp number
        import urllib.parse
        message = f"Hi, I want to subscribe to RoomNest for ₹49. My username is {request.user.username}."
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{owner_whatsapp}?text={encoded_message}"
        
        messages.info(request, 'Redirecting to WhatsApp to complete your payment...')
        return redirect(whatsapp_url)

    # If GET, just redirect home or show a simple pay page
    return redirect('home')
