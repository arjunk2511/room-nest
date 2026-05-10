from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Listing, ListingImage, Wishlist, Message, Review
from django.db.models import Q, Avg
from django.contrib.auth.models import User
from subscriptions.models import Subscription
from django.utils import timezone

from django.core.paginator import Paginator

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'welcome.html')
    featured_listings = Listing.objects.filter(is_sold=False).select_related('owner').order_by('-created_at')[:6]
    return render(request, 'index.html', {'listings': featured_listings})

def search(request):
    listings = Listing.objects.filter(is_sold=False).select_related('owner').prefetch_related('reviews').order_by('-created_at')
    
    location = request.GET.get('location')
    max_price = request.GET.get('price')
    listing_type = request.GET.get('type')
    furnishing = request.GET.get('furnishing')
    target_gender = request.GET.get('target_gender')
    
    if location:
        listings = listings.filter(location__icontains=location)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    if listing_type:
        listings = listings.filter(type__iexact=listing_type)
    if furnishing:
        listings = listings.filter(furnishing__iexact=furnishing)
    if target_gender:
        listings = listings.filter(target_gender__iexact=target_gender)
        
    # Standard 8 listings per page is perfect for mobile performance
    paginator = Paginator(listings, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    has_subscription = False
    if request.user.is_authenticated:
        has_subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()
    
    context = {
        'listings': page_obj,
        'page_obj': page_obj,
        'values': request.GET,
        'total_count': listings.count(),
        'has_subscription': has_subscription
    }
    return render(request, 'search.html', context)

def details(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Increment view counter (skip incrementing if owner views their own listing)
    if not request.user.is_authenticated or request.user != listing.owner:
        listing.views_count += 1
        listing.save(update_fields=['views_count'])

    has_subscription = False
    is_wishlisted = False
    

        
    if request.user.is_authenticated:
        if request.user == listing.owner:
            has_subscription = True
        else:
            has_subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).exists()
            
        # Check wishlist
        is_wishlisted = Wishlist.objects.filter(user=request.user, listing=listing).exists()

    similar_listings = Listing.objects.filter(
        type=listing.type,
        location=listing.location,
        is_sold=False
    ).exclude(id=listing.id).order_by('-created_at')[:3]

    reviews = listing.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'listing': listing,
        'has_subscription': has_subscription,
        'is_wishlisted': is_wishlisted,
        'similar_listings': similar_listings,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'details.html', context)

@login_required
def add_property(request):
    if request.method == 'POST':
        title = request.POST['title']
        location = request.POST['location']
        price = request.POST['price']
        listing_type = request.POST['type']
        description = request.POST['description']
        facilities = request.POST.getlist('facilities')
        address = request.POST['address']
        phone = request.POST['phone']
        
        exact_location = request.POST.get('exact_location', '')
        
        deposit = request.POST.get('deposit', 0)
        available_from = request.POST.get('available_from', 'Immediately')
        food_preference = request.POST.get('food_preference', 'Any')
        curfew = request.POST.get('curfew', 'No Curfew')
        visitors = request.POST.get('visitors', 'Allowed')
        landmark = request.POST.get('landmark', '')
        
        # New dynamic category fields
        listing_purpose = request.POST.get('listing_purpose', 'Rent')
        
        try:
            rooms_available = int(request.POST.get('rooms_available', 1))
        except (ValueError, TypeError):
            rooms_available = 1
            
        try:
            sharing_count = int(request.POST.get('sharing_count', 1))
        except (ValueError, TypeError):
            sharing_count = 1
            
        flatmate_preference = request.POST.get('flatmate_preference', '')
        target_gender = request.POST.get('target_gender', 'Any')
        furnishing = request.POST.get('furnishing', 'Unfurnished')
        commercial_type = request.POST.get('commercial_type', '')
        built_up_area = request.POST.get('built_up_area', '')
        
        images = request.FILES.getlist('images')
        if len(images) < 3:
            messages.error(request, 'You must upload at least 3 photos to publish your listing.')
            return render(request, 'add_property.html', {
                'error_msg': 'Minimum 3 photos required'
            })
        
        main_image = images[0]
        facilities_str = ', '.join(facilities)

        listing = Listing.objects.create(
            title=title,
            location=location,
            price=price,
            type=listing_type,
            description=description,
            facilities=facilities_str,
            address=address,
            exact_location=exact_location,
            phone=phone,
            deposit=deposit,
            available_from=available_from,
            food_preference=food_preference,
            curfew=curfew,
            visitors=visitors,
            landmark=landmark,
            image=main_image,
            owner=request.user,
            listing_purpose=listing_purpose,
            rooms_available=rooms_available,
            sharing_count=sharing_count,
            flatmate_preference=flatmate_preference,
            target_gender=target_gender,
            furnishing=furnishing,
            commercial_type=commercial_type,
            built_up_area=built_up_area
        )
        
        # Save extra images
        if len(images) > 1:
            for img in images[1:]:
                ListingImage.objects.create(listing=listing, image=img)
                
        return redirect('owner_dashboard')

    return render(request, 'add_property.html')

@login_required
def toggle_wishlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        wishlist_item.delete()
    return redirect('details', listing_id=listing.id)

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__owner').prefetch_related('listing__reviews')
    listings = [item.listing for item in wishlist_items]
    return render(request, 'wishlist.html', {'listings': listings})

@login_required
def owner_dashboard(request):
    listings = Listing.objects.filter(owner=request.user)
    active_count = listings.filter(is_sold=False).count()
    sold_count = listings.filter(is_sold=True).count()
    
    # Aggregate view stats and lead clicks across all properties
    total_views = sum(l.views_count for l in listings)
    total_whatsapp_clicks = sum(l.whatsapp_clicks_count for l in listings)
    
    return render(request, 'owner_dashboard.html', {
        'listings': listings,
        'active_count': active_count,
        'sold_count': sold_count,
        'total_views': total_views,
        'total_whatsapp_clicks': total_whatsapp_clicks,
    })

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def track_whatsapp_click(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    listing.whatsapp_clicks_count += 1
    listing.save(update_fields=['whatsapp_clicks_count'])
    return JsonResponse({'status': 'success', 'whatsapp_clicks_count': listing.whatsapp_clicks_count})

@login_required
def toggle_sold_status(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    listing.is_sold = not listing.is_sold
    listing.save()
    return redirect('owner_dashboard')

@login_required
def edit_property(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    
    if request.method == 'POST':
        listing.title = request.POST['title']
        listing.location = request.POST['location']
        listing.price = request.POST['price']
        listing.type = request.POST['type']
        listing.description = request.POST['description']
        listing.address = request.POST['address']
        listing.phone = request.POST['phone']
        listing.exact_location = request.POST.get('exact_location', '')
        listing.deposit = request.POST.get('deposit', 0)
        listing.available_from = request.POST.get('available_from', 'Immediately')
        listing.food_preference = request.POST.get('food_preference', 'Any')
        listing.curfew = request.POST.get('curfew', 'No Curfew')
        listing.visitors = request.POST.get('visitors', 'Allowed')
        listing.landmark = request.POST.get('landmark', '')
        
        # Parse and update new dynamic category fields
        listing.listing_purpose = request.POST.get('listing_purpose', 'Rent')
        
        try:
            listing.rooms_available = int(request.POST.get('rooms_available', 1))
        except (ValueError, TypeError):
            listing.rooms_available = 1
            
        try:
            listing.sharing_count = int(request.POST.get('sharing_count', 1))
        except (ValueError, TypeError):
            listing.sharing_count = 1
            
        listing.flatmate_preference = request.POST.get('flatmate_preference', '')
        listing.target_gender = request.POST.get('target_gender', 'Any')
        listing.furnishing = request.POST.get('furnishing', 'Unfurnished')
        listing.commercial_type = request.POST.get('commercial_type', '')
        listing.built_up_area = request.POST.get('built_up_area', '')
        
        facilities = request.POST.getlist('facilities')
        listing.facilities = ', '.join(facilities)
        
        # Handle new image files if uploaded
        images = request.FILES.getlist('images')
        if images:
            if len(images) < 3:
                messages.error(request, 'If you decide to upload new photos, you must upload at least 3 photos.')
                return redirect('edit_property', listing_id=listing.id)
            
            # Update main image to first new image
            listing.image = images[0]
            
            # Delete existing extra gallery images and save new ones
            listing.images.all().delete()
            for img in images[1:]:
                ListingImage.objects.create(listing=listing, image=img)
        
        listing.save()
        messages.success(request, 'Property listing updated successfully!')
        return redirect('owner_dashboard')
    
    # Pre-select facilities list for the template context
    selected_facilities = [f.strip() for f in listing.facilities.split(',')] if listing.facilities else []
    
    return render(request, 'edit_property.html', {
        'listing': listing,
        'selected_facilities': selected_facilities,
    })

import re

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        listing_id = request.POST.get('listing_id')
        listing = Listing.objects.filter(id=listing_id).first() if listing_id else None
        
        if content:
            # Masking disabled temporarily while subscription system is inactive
            masked_content = content
            
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                listing=listing,
                content=masked_content
            )
        return redirect(f"{request.path}?listing_id={listing_id}" if listing_id else request.path)
        
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    listing_id = request.GET.get('listing_id')
    listing = Listing.objects.filter(id=listing_id).first() if listing_id else None

    return render(request, 'chat.html', {
        'chat_messages': messages,
        'other_user': other_user,
        'listing': listing
    })

@login_required
def inbox_view(request):
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')
    
    chat_users = []
    seen_users = set()
    
    for msg in messages:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user not in seen_users:
            seen_users.add(other_user)
            unread_count = Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).count()
            chat_users.append({
                'user': other_user,
                'last_message': msg,
                'unread_count': unread_count
            })
            
    return render(request, 'inbox.html', {'chat_users': chat_users})

@login_required
def add_review(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.method == 'POST' and request.user != listing.owner:
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        Review.objects.update_or_create(
            listing=listing, user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
    return redirect('details', listing_id=listing.id)

def about_us(request):
    return render(request, 'about_us.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    return render(request, 'terms_conditions.html')

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        messages.success(request, f"Thank you, {name}! Your message has been sent successfully. Our support team will get back to you shortly.")
        return redirect('contact_us')
        
    return render(request, 'contact_us.html')

@login_required
def delete_property(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if listing.owner != request.user:
        messages.error(request, "You are not authorized to delete this property.")
        return redirect('owner_dashboard')
        
    if request.method == 'POST':
        listing.delete()
        messages.success(request, "Property listing deleted successfully!")
    return redirect('owner_dashboard')
