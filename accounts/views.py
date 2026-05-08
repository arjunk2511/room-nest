from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from subscriptions.models import Subscription
from django.utils import timezone
from .models import UserProfile

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registration successful.')
            return redirect('home')
        messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
        form.fields['username'].label = "Email / Phone / Username"
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('home')

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        phone_number = request.POST.get('phone_number', '').strip() or None
        if phone_number:
            # Check if this phone number is already registered by a DIFFERENT user profile
            existing_profile = UserProfile.objects.filter(phone_number=phone_number).exclude(user=request.user).first()
            if existing_profile:
                messages.error(request, 'This phone number is already registered to another account.')
                return redirect('profile')
        
        user_profile.phone_number = phone_number
        user_profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    subscription = Subscription.objects.filter(
        user=request.user, 
        is_active=True, 
        end_date__gte=timezone.now()
    ).first()
    
    context = {
        'profile': user_profile,
        'subscription': subscription
    }
    return render(request, 'profile.html', context)
