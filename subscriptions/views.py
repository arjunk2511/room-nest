from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Subscription
from django.utils import timezone
import datetime
from django.contrib import messages

@login_required
def subscribe(request):
    # Check if they already have an active subscription
    active_sub = Subscription.objects.filter(user=request.user, is_active=True, end_date__gt=timezone.now()).first()
    if active_sub:
        messages.info(request, "You already have an active subscription!")
        return redirect('home')

    # Check if they have a pending subscription
    pending_sub = Subscription.objects.filter(user=request.user, payment_status='Pending').first()

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id', '').strip()
        if not transaction_id:
            messages.error(request, "Please enter a valid Transaction ID / UTR Number.")
            return redirect('subscribe')
        
        # Save or update subscription
        end_date = timezone.now() + datetime.timedelta(days=90) # 90 days plan
        Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                'is_active': False,
                'end_date': end_date,
                'transaction_id': transaction_id,
                'payment_status': 'Pending'
            }
        )
        messages.success(request, "Payment details submitted! Your subscription is pending verification.")
        return redirect('home')

    # For GET requests, render the pay.html
    upi_id = "7981629660@ybl"  # ⚠️ CHANGE THIS TO YOUR ACTUAL UPI ID ⚠️
    
    # Generate UPI deep link
    import urllib.parse
    upi_payment_link = f"upi://pay?pa={upi_id}&pn=RoomNest&am=49&cu=INR&tn=RoomNest_Sub_for_{request.user.username}"
    # QR Code API url
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(upi_payment_link)}"

    context = {
        'upi_id': upi_id,
        'upi_link': upi_payment_link,
        'qr_code_url': qr_code_url,
        'pending_sub': pending_sub,
    }
    return render(request, 'pay.html', context)
