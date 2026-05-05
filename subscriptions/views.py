from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Subscription
from django.utils import timezone
import datetime
from django.contrib import messages

@login_required
def subscribe(request):
    if request.method == 'POST':
        # Simulate payment: click button -> activate subscription
        # Plan is valid for 3 months
        end_date = timezone.now() + datetime.timedelta(days=90)
        
        # Check if user already has an active subscription to extend or create a new one
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'is_active': True, 'end_date': end_date}
        )
        
        if not created:
            subscription.is_active = True
            subscription.end_date = end_date
            subscription.save()

        messages.success(request, 'Payment successful! You are now subscribed for 3 months.')
        # redirect to the page they came from, if possible, or home
        next_url = request.POST.get('next', 'home')
        return redirect(next_url)

    # If GET, just redirect home or show a simple pay page
    return redirect('home')
