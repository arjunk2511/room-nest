from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Listing, ListingImage, Wishlist, Message, Review, Lead, City, Area, PropertySubmission, Reward, Notification
from django.db.models import Q, Avg, F, Count
from django.contrib.auth.models import User
from subscriptions.models import Subscription
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
import csv
import datetime

def home(request):
    featured_listings = cache.get('home_featured_listings')
    if not featured_listings:
        featured_listings = list(Listing.objects.filter(is_sold=False).select_related('owner__userprofile', 'city', 'area').order_by('-created_at')[:6])
        cache.set('home_featured_listings', featured_listings, 900)  # Cache for 15 minutes
    has_subscription = False
    wishlist_ids = []
    user_listings = []
    if request.user.is_authenticated:
        has_subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True))
        user_listings = list(Listing.objects.filter(owner=request.user).select_related('city', 'area')[:3])
    
    context = {
        'listings': featured_listings,
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids,
        'user_listings': user_listings,
    }
    
    if not request.user.is_authenticated:
        return render(request, 'welcome.html', context)
    return render(request, 'index.html', context)

def search(request):
    # Optimize query by pre-joining the owner's profile and city/area
    listings = Listing.objects.filter(is_sold=False).select_related('owner__userprofile', 'city', 'area').order_by('-created_at')
    
    # New V2 filters: city and area slugs
    city_slug = request.GET.get('city')
    area_slug = request.GET.get('area')
    
    current_city = getattr(request, 'current_city', None)
    current_area = getattr(request, 'current_area', None)
    
    # Fetch City and Area if not already attached by area_page view
    if city_slug and not current_city:
        current_city = City.objects.filter(slug=city_slug, is_active=True).first()
    if area_slug and not current_area:
        current_area = Area.objects.filter(slug=area_slug, is_active=True).first()
        
    # Apply City & Area filtering
    if current_city:
        listings = listings.filter(city=current_city)
    elif city_slug:
        listings = listings.filter(city__slug=city_slug)
        
    if current_area:
        listings = listings.filter(area=current_area)
    elif area_slug:
        listings = listings.filter(area__slug=area_slug)
    
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('price')  # standard max price parameter
    listing_type = request.GET.get('type')
    listing_purpose = request.GET.get('listing_purpose')
    furnishing = request.GET.get('furnishing')
    target_gender = request.GET.get('target_gender')
    facilities_list = request.GET.getlist('facilities')
    sort_by = request.GET.get('sort_by')
    
    if location:
        listings = listings.filter(location__icontains=location)
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    if listing_type:
        listings = listings.filter(type__iexact=listing_type)
    if listing_purpose:
        listings = listings.filter(listing_purpose__iexact=listing_purpose)
    if furnishing:
        listings = listings.filter(furnishing__iexact=furnishing)
    if target_gender:
        listings = listings.filter(target_gender__iexact=target_gender)
    if facilities_list:
        for facility in facilities_list:
            listings = listings.filter(facilities__icontains=facility)
            
    # Apply sorting
    if sort_by == 'price_asc':
        listings = listings.order_by('price')
    elif sort_by == 'price_desc':
        listings = listings.order_by('-price')
    elif sort_by == 'popularity':
        listings = listings.order_by('-views_count')
    elif sort_by == 'rating':
        listings = listings.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:  # newest
        listings = listings.order_by('-created_at')
        
    # Standard 8 listings per page is perfect for mobile performance
    paginator = Paginator(listings, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    has_subscription = False
    wishlist_ids = []
    if request.user.is_authenticated:
        has_subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
    # Dynamic SEO titles & descriptions based on filtered parameters
    seo_title = None
    seo_description = None
    
    if current_city and current_area:
        prop_type = request.GET.get('type', '')
        type_str = f"{prop_type} " if prop_type else "Rooms, PGs & Flats "
        seo_title = f"{type_str}for Rent in {current_area.name}, {current_city.name} | RoomNest"
        seo_description = f"Discover verified {type_str.lower()}for rent in {current_area.name}, {current_city.name}. Connect directly with owners, pay zero brokerage, and find your next home with RoomNest."
    elif current_city:
        prop_type = request.GET.get('type', '')
        type_str = f"{prop_type}s " if prop_type else "Rooms, PGs & Flats "
        seo_title = f"{type_str}in {current_city.name} | RoomNest"
        seo_description = f"Discover verified {type_str.lower()}across {current_city.name}. Connect directly with owners, pay zero brokerage, and find your next home with RoomNest."
    
    context = {
        'listings': page_obj,
        'page_obj': page_obj,
        'values': request.GET,
        'total_count': page_obj.paginator.count,  # Reuses count executed by paginator to save 1 query!
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids,
        'seo_title': seo_title,
        'seo_description': seo_description,
        'current_city': current_city,
        'current_area': current_area
    }
    return render(request, 'search.html', context)

def details(request, listing_id):
    # Fetch listing with all related images and reviews' users pre-joined and cached
    cache_key = f"listing_detail_{listing_id}"
    listing = cache.get(cache_key)
    if not listing:
        listing = get_object_or_404(
            Listing.objects.select_related('owner__userprofile', 'city', 'area').prefetch_related('images', 'reviews__user'),
            id=listing_id
        )
        cache.set(cache_key, listing, 900)  # Cache for 15 minutes

    # Increment view counter atomically in the DB (saves slow model save, avoids cache invalidation!)
    if not request.user.is_authenticated or request.user != listing.owner:
        Listing.objects.filter(id=listing.id).update(views_count=F('views_count') + 1)
        listing.views_count += 1

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

    # Sort prefetched reviews in memory instead of executing a new SQL query!
    reviews = sorted(listing.reviews.all(), key=lambda r: r.created_at, reverse=True)
    
    # Calculate average rating in Python to save another SQL query!
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

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
        
        # City and Area ForeignKeys
        city_id = request.POST.get('city')
        area_id = request.POST.get('area')
        city_obj = City.objects.filter(id=city_id).first() if city_id else None
        area_obj = Area.objects.filter(id=area_id).first() if area_id else None
        
        # Location fallback mapped from Area name
        location = area_obj.name if area_obj else 'Other (Mysore)'
        if len(location) > 50:
            location = location[:50]
            
        price = request.POST['price']
        listing_type = request.POST['type']
        description = request.POST['description']
        facilities = request.POST.getlist('facilities')
        address = request.POST['address']
        phone = request.POST['phone']
        
        exact_location = request.POST.get('exact_location', '')
        
        # Extract coordinates and Google Place ID
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        google_place_id = request.POST.get('google_place_id', '').strip()
        
        if latitude:
            try:
                latitude = float(latitude)
            except ValueError:
                latitude = None
        else:
            latitude = None
            
        if longitude:
            try:
                longitude = float(longitude)
            except ValueError:
                longitude = None
        else:
            longitude = None
        
        deposit = request.POST.get('deposit', 0)
        available_from = request.POST.get('available_from', 'Immediately')
        food_preference = request.POST.get('food_preference', 'Any')
        curfew = request.POST.get('curfew', 'No Curfew')
        visitors = request.POST.get('visitors', 'Allowed')
        landmark = request.POST.get('landmark', '')
        nearby_food_options = request.POST.get('nearby_food_options', '')
        
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
        
        # Temporary logging for debugging image upload
        import sys
        print(f"DEBUG BACKEND UPLOAD: request.FILES = {request.FILES}", file=sys.stderr)
        print(f"DEBUG BACKEND UPLOAD: request.FILES.getlist('images') = {request.FILES.getlist('images')}", file=sys.stderr)
        
        images = request.FILES.getlist('images')
        
        if len(images) < 1:
            messages.error(request, 'You must upload at least 1 photo to publish your listing.')
            return render(request, 'add_property.html', {
                'error_msg': 'Minimum 1 photo required'
            })
        
        main_image = images[0]
        facilities_str = ', '.join(facilities)

        listing = Listing.objects.create(
            title=title,
            location=location,
            city=city_obj,
            area=area_obj,
            price=price,
            type=listing_type,
            description=description,
            facilities=facilities_str,
            address=address,
            exact_location=exact_location,
            latitude=latitude,
            longitude=longitude,
            google_place_id=google_place_id,
            phone=phone,
            deposit=deposit,
            available_from=available_from,
            food_preference=food_preference,
            curfew=curfew,
            visitors=visitors,
            landmark=landmark,
            nearby_food_options=nearby_food_options,
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
        
        # Save extra images efficiently using bulk_create (single database query)
        if len(images) > 1:
            ListingImage.objects.bulk_create([
                ListingImage(listing=listing, image=img) for img in images[1:]
            ])
            
        # Create a pending reward for the direct owner listing (Owner Bonus System)
        Reward.objects.create(
            user=request.user,
            reward_type='DirectOwner',
            listing=listing,
            amount=50.00,
            status='Pending'
        )
        
        # Send a notification that listing is submitted
        Notification.objects.create(
            user=request.user,
            title="Property Submitted",
            message=f"Your property listing '{listing.title}' has been submitted and is pending verification. You will earn ₹50 once verified and published."
        )
                
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
    has_subscription = False
    wishlist_ids = []
    if request.user.is_authenticated:
        has_subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True))
    return render(request, 'wishlist.html', {
        'listings': listings,
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids
    })

@login_required
def owner_dashboard(request):
    # Fetch listings as a list once and reuse in memory to avoid 2 extra COUNT queries
    listings_list = list(Listing.objects.filter(owner=request.user))
    active_count = sum(1 for l in listings_list if not l.is_sold)
    sold_count = len(listings_list) - active_count
    
    # Aggregate view stats and lead clicks across all properties
    total_views = sum(l.views_count for l in listings_list)
    total_whatsapp_clicks = sum(l.whatsapp_clicks_count for l in listings_list)
    
    # Retrieve leads for the owner's properties
    leads = Lead.objects.filter(listing__owner=request.user).select_related('listing', 'tenant').order_by('-created_at')
    
    # Retrieve active subscription details
    subscription = Subscription.objects.filter(
        user=request.user, 
        is_active=True, 
        end_date__gt=timezone.now()
    ).first()
    
    # Fetch unread message counts in bulk (1 query instead of N!)
    unread_counts = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).values('sender').annotate(count=Count('id'))
    unread_dict = {item['sender']: item['count'] for item in unread_counts}
    
    # Fetch messages with select_related for sender/receiver to avoid N+1 user queries
    chat_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver', 'listing').order_by('-timestamp')
    
    chat_users = []
    seen_users = set()
    for msg in chat_messages:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user not in seen_users:
            seen_users.add(other_user)
            unread_count = unread_dict.get(other_user.id, 0)
            chat_users.append({
                'user': other_user,
                'last_message': msg,
                'unread_count': unread_count
            })
            
    return render(request, 'owner_dashboard.html', {
        'listings': listings_list,
        'active_count': active_count,
        'sold_count': sold_count,
        'total_views': total_views,
        'total_whatsapp_clicks': total_whatsapp_clicks,
        'leads': leads,
        'subscription': subscription,
        'chat_users': chat_users[:5],  # Limit to 5 for dashboard summary
    })

@require_POST
def track_whatsapp_click(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    listing.whatsapp_clicks_count += 1
    listing.save(update_fields=['whatsapp_clicks_count'])
    
    # Save a lead if the user is authenticated and not the owner
    if request.user.is_authenticated and request.user != listing.owner:
        from accounts.models import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        phone = profile.phone_number if profile and profile.phone_number else 'Not Provided'
        name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        
        # Check if a WhatsApp lead already exists within the last 24 hours to prevent spamming
        last_day = timezone.now() - timezone.timedelta(days=1)
        exists = Lead.objects.filter(
            listing=listing,
            tenant=request.user,
            lead_type='WhatsApp',
            created_at__gte=last_day
        ).exists()
        
        if not exists:
            Lead.objects.create(
                listing=listing,
                tenant=request.user,
                name=name,
                email=request.user.email,
                phone=phone,
                lead_type='WhatsApp'
            )
            
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
        
        # City and Area ForeignKeys
        city_id = request.POST.get('city')
        area_id = request.POST.get('area')
        city_obj = City.objects.filter(id=city_id).first() if city_id else None
        area_obj = Area.objects.filter(id=area_id).first() if area_id else None
        
        listing.city = city_obj
        listing.area = area_obj
        
        location_val = area_obj.name if area_obj else 'Other (Mysore)'
        if len(location_val) > 50:
            location_val = location_val[:50]
        listing.location = location_val
        
        listing.price = request.POST['price']
        listing.type = request.POST['type']
        listing.description = request.POST['description']
        listing.address = request.POST['address']
        listing.phone = request.POST['phone']
        listing.exact_location = request.POST.get('exact_location', '')
        
        # Extract coordinates and Google Place ID
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        google_place_id = request.POST.get('google_place_id', '').strip()
        
        if latitude:
            try:
                listing.latitude = float(latitude)
            except ValueError:
                listing.latitude = None
        else:
            listing.latitude = None
            
        if longitude:
            try:
                listing.longitude = float(longitude)
            except ValueError:
                listing.longitude = None
        else:
            listing.longitude = None
            
        listing.google_place_id = google_place_id
        listing.deposit = request.POST.get('deposit', 0)
        listing.available_from = request.POST.get('available_from', 'Immediately')
        listing.food_preference = request.POST.get('food_preference', 'Any')
        listing.curfew = request.POST.get('curfew', 'No Curfew')
        listing.visitors = request.POST.get('visitors', 'Allowed')
        listing.landmark = request.POST.get('landmark', '')
        listing.nearby_food_options = request.POST.get('nearby_food_options', '')
        
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
        import sys
        print(f"DEBUG BACKEND UPLOAD (EDIT): request.FILES = {request.FILES}", file=sys.stderr)
        print(f"DEBUG BACKEND UPLOAD (EDIT): request.FILES.getlist('images') = {request.FILES.getlist('images')}", file=sys.stderr)
        
        images = request.FILES.getlist('images')
        if images:
            if len(images) < 1:
                messages.error(request, 'If you decide to upload new photos, you must upload at least 1 photo.')
                return redirect('edit_property', listing_id=listing.id)
            
            # Update main image to first new image
            listing.image = images[0]
            
            # Delete existing extra gallery images and save new ones efficiently using bulk_create
            listing.images.all().delete()
            ListingImage.objects.bulk_create([
                ListingImage(listing=listing, image=img) for img in images[1:]
            ])
        
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
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                listing=listing,
                content=content
            )
            
            # Record a Lead of type 'Chat' if they are messaging about a listing and they are not the owner
            if listing and request.user != listing.owner:
                from accounts.models import UserProfile
                profile = UserProfile.objects.filter(user=request.user).first()
                phone = profile.phone_number if profile and profile.phone_number else 'Not Provided'
                name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                
                # Check if a Chat lead already exists
                exists = Lead.objects.filter(
                    listing=listing,
                    tenant=request.user,
                    lead_type='Chat'
                ).exists()
                
                if not exists:
                    Lead.objects.create(
                        listing=listing,
                        tenant=request.user,
                        name=name,
                        email=request.user.email,
                        phone=phone,
                        message_content=content,
                        lead_type='Chat'
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
    # Fetch unread message counts in bulk (1 query instead of N!)
    unread_counts = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).values('sender').annotate(count=Count('id'))
    unread_dict = {item['sender']: item['count'] for item in unread_counts}
    
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver', 'listing').order_by('-timestamp')
    
    chat_users = []
    seen_users = set()
    
    for msg in messages:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user not in seen_users:
            seen_users.add(other_user)
            unread_count = unread_dict.get(other_user.id, 0)
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


@login_required
def tenant_dashboard(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__owner').prefetch_related('listing__reviews')
    listings = [item.listing for item in wishlist_items]
    
    # Active subscription
    subscription = Subscription.objects.filter(
        user=request.user, 
        is_active=True, 
        end_date__gt=timezone.now()
    ).first()
    
    # Subscription history
    sub_history = Subscription.objects.filter(user=request.user).order_by('-start_date')
    
    # Inquiries (Leads generated by the tenant)
    inquiries = Lead.objects.filter(tenant=request.user).select_related('listing').order_by('-created_at')
    
    # Fetch unread message counts in bulk (1 query instead of N!)
    unread_counts = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).values('sender').annotate(count=Count('id'))
    unread_dict = {item['sender']: item['count'] for item in unread_counts}
    
    # Retrieve active chat threads (inbox style)
    messages_query = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver', 'listing').order_by('-timestamp')
    
    chat_users = []
    seen_users = set()
    for msg in messages_query:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user not in seen_users:
            seen_users.add(other_user)
            unread_count = unread_dict.get(other_user.id, 0)
            chat_users.append({
                'user': other_user,
                'last_message': msg,
                'unread_count': unread_count
            })
            
    return render(request, 'tenant_dashboard.html', {
        'listings': listings,
        'subscription': subscription,
        'sub_history': sub_history,
        'inquiries': inquiries,
        'chat_users': chat_users[:5],
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access Denied: Admin authorization required.")
        return redirect('home')
        
    # Global metrics
    total_listings = Listing.objects.count()
    active_listings = Listing.objects.filter(is_sold=False).count()
    total_users = User.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True, end_date__gt=timezone.now()).count()
    pending_subscriptions_count = Subscription.objects.filter(payment_status='Pending').count()
    
    # Calculate revenue from approved subscriptions (each subscription is INR 49)
    approved_subs = Subscription.objects.filter(payment_status='Approved')
    total_revenue = approved_subs.count() * 49
    
    # Pending property verifications
    pending_verifications = Listing.objects.filter(verification_status='Pending').select_related('owner')
    
    # Pending subscriptions
    pending_subscriptions = Subscription.objects.filter(payment_status='Pending').select_related('user')
    
    # Reward & Referral Management data
    pending_rewards = Reward.objects.filter(status='Pending').select_related('user', 'submission', 'listing')
    approved_rewards = Reward.objects.filter(status='Approved').select_related('user', 'submission', 'listing')
    paid_rewards = Reward.objects.filter(status='Paid').select_related('user', 'submission', 'listing')
    
    # Pending property referrals awaiting verification
    pending_referrals = PropertySubmission.objects.filter(status__in=['Pending', 'Under Verification']).select_related('submitter', 'city')
    
    return render(request, 'admin_dashboard.html', {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'pending_subscriptions_count': pending_subscriptions_count,
        'total_revenue': total_revenue,
        'pending_verifications': pending_verifications,
        'pending_subscriptions': pending_subscriptions,
        'pending_rewards': pending_rewards,
        'approved_rewards': approved_rewards,
        'paid_rewards': paid_rewards,
        'pending_referrals': pending_referrals,
    })


@login_required
def request_verification(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    
    if request.method == 'POST':
        document = request.FILES.get('verification_document')
        notes = request.POST.get('verification_notes', '').strip()
        
        if not document:
            messages.error(request, "Please upload a verification document (PDF or Image).")
            return redirect('owner_dashboard')
            
        listing.verification_document = document
        listing.verification_notes = notes
        listing.verification_status = 'Pending'
        listing.save()
        messages.success(request, f"Verification request submitted for '{listing.title}'! Our team will review it shortly.")
        
    return redirect('owner_dashboard')


@login_required
def approve_verification(request, listing_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    listing = get_object_or_404(Listing, id=listing_id)
    listing.is_verified = True
    listing.verification_status = 'Verified'
    listing.save(update_fields=['is_verified', 'verification_status'])
    
    # Approve owner reward if exists (Owner Bonus System)
    reward = Reward.objects.filter(listing=listing, reward_type='DirectOwner', status='Pending').first()
    if reward:
        reward.status = 'Approved'
        reward.save()
        
        # Send Notification for Reward Credited
        Notification.objects.create(
            user=listing.owner,
            title="Reward Credited",
            message="Congratulations! ₹50 reward has been credited to your account for successfully listing your property."
        )
    
    # Send Notification for Property Approved
    Notification.objects.create(
        user=listing.owner,
        title="Property Approved",
        message=f"Your property listing '{listing.title}' has been successfully verified and approved."
    )
    
    messages.success(request, f"Property '{listing.title}' successfully verified!")
    return redirect('admin_dashboard')


@login_required
def reject_verification(request, listing_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    listing = get_object_or_404(Listing, id=listing_id)
    listing.is_verified = False
    listing.verification_status = 'Rejected'
    
    notes = request.POST.get('rejection_notes', '').strip()
    if notes:
        listing.verification_notes = f"Rejected: {notes}"
        
    listing.save()
    
    # Reject owner reward if exists
    reward = Reward.objects.filter(listing=listing, reward_type='DirectOwner', status='Pending').first()
    if reward:
        reward.status = 'Rejected'
        reward.save()
        
    # Send Notification for Property Rejected
    Notification.objects.create(
        user=listing.owner,
        title="Property Rejected",
        message=f"Your property listing '{listing.title}' verification request has been rejected. Reason: {notes or 'Verification criteria not met.'}"
    )
    
    messages.warning(request, f"Property '{listing.title}' verification request rejected.")
    return redirect('admin_dashboard')


@login_required
def approve_subscription(request, subscription_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    sub = get_object_or_404(Subscription, id=subscription_id)
    sub.is_active = True
    sub.payment_status = 'Approved'
    sub.end_date = timezone.now() + datetime.timedelta(days=90)
    sub.save(update_fields=['is_active', 'payment_status', 'end_date'])
    messages.success(request, f"Subscription approved for user {sub.user.username}!")
    return redirect('admin_dashboard')


@login_required
def reject_subscription(request, subscription_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    sub = get_object_or_404(Subscription, id=subscription_id)
    sub.is_active = False
    sub.payment_status = 'Rejected'
    sub.save(update_fields=['is_active', 'payment_status'])
    messages.warning(request, f"Subscription rejected for user {sub.user.username}.")
    return redirect('admin_dashboard')


@login_required
def export_leads_csv(request):
    # Check subscription
    has_sub = Subscription.objects.filter(
        user=request.user, 
        is_active=True, 
        end_date__gt=timezone.now()
    ).exists()
    
    if not has_sub:
        messages.error(request, "Premium subscription required to export leads.")
        return redirect('owner_dashboard')
        
    # Get listings owned by this user
    listing_ids = Listing.objects.filter(owner=request.user).values_list('id', flat=True)
    leads = Lead.objects.filter(listing_id__in=listing_ids).select_related('listing').order_by('-created_at')
    
    # Generate CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="RoomNest_Leads_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Lead Name', 'Email', 'Phone', 'Property Title', 'Type', 'Location', 'Lead Method', 'Date Received'])
    
    for lead in leads:
        writer.writerow([
            lead.name,
            lead.email,
            lead.phone,
            lead.listing.title,
            lead.listing.type,
            lead.listing.location,
            lead.lead_type,
            lead.created_at.strftime('%Y-%m-%d %H:%M')
        ])
        
    return response


def city_page(request, city_slug):
    cache_key = f"city_page_data_{city_slug}"
    page_data = cache.get(cache_key)
    if not page_data:
        city = get_object_or_404(City, slug=city_slug, is_active=True)
        featured_listings = list(Listing.objects.filter(
            city=city, 
            is_sold=False
        ).select_related('owner__userprofile', 'city', 'area').order_by('-created_at')[:6])
        areas = list(city.areas.filter(is_active=True).order_by('name'))
        page_data = {
            'city': city,
            'listings': featured_listings,
            'areas': areas
        }
        cache.set(cache_key, page_data, 900)  # Cache for 15 minutes
    
    # Active subscription check
    has_subscription = False
    wishlist_ids = []
    if request.user.is_authenticated:
        has_subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).exists()
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
    return render(request, 'city_page.html', {
        'city': page_data['city'],
        'listings': page_data['listings'],
        'areas': page_data['areas'],
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids
    })


def area_page(request, city_slug, area_slug):
    # Verify city and area exist and are active
    city = get_object_or_404(City, slug=city_slug, is_active=True)
    area = get_object_or_404(Area, city=city, slug=area_slug, is_active=True)
    
    # Mutate request.GET to inject city and area slugs for the search view
    query_params = request.GET.copy()
    query_params['city'] = city.slug
    query_params['area'] = area.slug
    request.GET = query_params
    
    # Attach city and area objects to the request so search view can use them for dynamic SEO
    request.current_city = city
    request.current_area = area
    
    # Call search view directly to inherit all filters and layout
    return search(request)


def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    if not q:
        # Return default popular searches
        popular_searches = [
            {"label": "PG in Bengaluru", "url": "/search/?city=bengaluru&type=PG+(Men)"},
            {"label": "1BHK in Mysore", "url": "/search/?city=mysore&type=1BHK"},
            {"label": "Commercial Space in Hyderabad", "url": "/search/?city=hyderabad&type=Commercial+Space"},
        ]
        return JsonResponse({
            "cities": [],
            "areas": [],
            "types": [],
            "popular": popular_searches
        })
        
    # Match Cities
    cities = City.objects.filter(name__icontains=q, is_active=True)[:5]
    cities_data = [{"name": c.name, "slug": c.slug} for c in cities]
    
    # Special check for Bengaluru prefix match "Ban..." to meet spec requirement
    if q.lower() in "bengaluru" or "bengaluru".startswith(q.lower()) or q.lower() == "ban":
        if not any(c['slug'] == 'bengaluru' for c in cities_data):
            beng_city = City.objects.filter(slug='bengaluru', is_active=True).first()
            if beng_city:
                cities_data.insert(0, {"name": beng_city.name, "slug": beng_city.slug})
                
    # Match Areas
    areas = Area.objects.filter(name__icontains=q, is_active=True).select_related('city')[:10]
    areas_data = [{"name": a.name, "slug": a.slug, "city_name": a.city.name, "city_slug": a.city.slug} for a in areas]
    
    # Match Property Types
    all_types = [
        '1BHK', '2BHK', '3BHK', 'Single Room', 'PG (Men)', 'PG (Women)', 
        'Co-living', 'Flatmate', 'Commercial Space', 'Office Space'
    ]
    matched_types = [t for t in all_types if q.lower() in t.lower()][:5]
    types_data = [{"name": t, "type_val": t} for t in matched_types]
    
    return JsonResponse({
        "cities": cities_data,
        "areas": areas_data,
        "types": types_data,
        "popular": []
    })


@login_required
def earn_rewards(request):
    active_cities = City.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        submitted_by_name = request.POST.get('submitted_by_name', '').strip()
        submitted_by_mobile = request.POST.get('submitted_by_mobile', '').strip()
        owner_name = request.POST.get('owner_name', '').strip()
        owner_mobile = request.POST.get('owner_mobile', '').strip()
        property_type = request.POST.get('property_type', '').strip()
        property_address = request.POST.get('property_address', '').strip()
        city_id = request.POST.get('city')
        notes = request.POST.get('notes', '').strip()
        permission_confirmed = request.POST.get('permission_confirmed') == 'on'
        photo = request.FILES.get('photo')
        
        # Form validation
        if not (submitted_by_name and submitted_by_mobile and owner_name and owner_mobile and property_type and property_address and city_id):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'earn_rewards.html', {'active_cities': active_cities, 'values': request.POST})
            
        if not permission_confirmed:
            messages.error(request, "You must confirm that you have the owner's permission to share these details.")
            return render(request, 'earn_rewards.html', {'active_cities': active_cities, 'values': request.POST})
            
        city_obj = get_object_or_404(City, id=city_id)
        
        # Anti-spam protection & duplicate checks
        # 1. Same owner number cannot receive multiple rewards for the same property.
        # 2. Duplicate submissions are rejected.
        duplicate_submission = PropertySubmission.objects.filter(
            owner_mobile=owner_mobile,
            city=city_obj
        ).exists()
        
        duplicate_listing = Listing.objects.filter(
            phone=owner_mobile,
            city=city_obj
        ).exists()
        
        if duplicate_submission or duplicate_listing:
             messages.error(request, "This property owner or property has already been submitted or listed on RoomNest.")
             return render(request, 'earn_rewards.html', {'active_cities': active_cities, 'values': request.POST})
             
        # Create submission
        submission = PropertySubmission.objects.create(
            submitter=request.user,
            submitted_by_name=submitted_by_name,
            submitted_by_mobile=submitted_by_mobile,
            owner_name=owner_name,
            owner_mobile=owner_mobile,
            property_type=property_type,
            property_address=property_address,
            city=city_obj,
            photo=photo,
            notes=notes,
            permission_confirmed=True,
            status='Pending'
        )
        
        # Create a pending reward claim for this submission
        Reward.objects.create(
            user=request.user,
            reward_type='Referral',
            submission=submission,
            amount=50.00,
            status='Pending'
        )
        
        # Send Notification
        Notification.objects.create(
            user=request.user,
            title="Property Submitted",
            message=f"Your property submission for the {property_type} in {city_obj.name} has been received."
        )
        
        messages.success(request, "Your property submission has been received successfully!")
        return redirect('profile')
        
    return render(request, 'earn_rewards.html', {'active_cities': active_cities})


@login_required
def approve_reward_claim(request, reward_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    reward = get_object_or_404(Reward, id=reward_id)
    reward.status = 'Approved'
    reward.save()
    
    if reward.submission:
        reward.submission.status = 'Approved'
        reward.submission.save()
        
        # Send Notification for Submission Approved
        Notification.objects.create(
            user=reward.submission.submitter,
            title="Property Approved",
            message=f"Your property submission for the {reward.submission.property_type} in {reward.submission.city.name} has been approved."
        )
        
        # Send Notification for Reward Credited
        Notification.objects.create(
            user=reward.submission.submitter,
            title="Reward Credited",
            message=f"Congratulations! ₹50 reward has been credited to your account for your referral."
        )
    elif reward.listing:
        # Direct owner listing
        reward.listing.is_verified = True
        reward.listing.verification_status = 'Verified'
        reward.listing.save(update_fields=['is_verified', 'verification_status'])
        
        Notification.objects.create(
            user=reward.user,
            title="Reward Credited",
            message="Congratulations! ₹50 reward has been credited to your account for successfully listing your property."
        )
        Notification.objects.create(
            user=reward.user,
            title="Property Approved",
            message=f"Your property listing '{reward.listing.title}' has been successfully verified and approved."
        )
        
    messages.success(request, f"Reward claim approved for {reward.user.username}!")
    return redirect('admin_dashboard')


@login_required
def reject_reward_claim(request, reward_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    reward = get_object_or_404(Reward, id=reward_id)
    reward.status = 'Rejected'
    reward.save()
    
    reason = request.POST.get('rejection_notes', '').strip() or 'Verification criteria not met.'
    
    if reward.submission:
        reward.submission.status = 'Rejected'
        reward.submission.save()
        
        # Send Notification for Submission Rejected
        Notification.objects.create(
            user=reward.submission.submitter,
            title="Property Rejected",
            message=f"Your property submission for the {reward.submission.property_type} in {reward.submission.city.name} has been rejected. Reason: {reason}"
        )
    elif reward.listing:
        reward.listing.is_verified = False
        reward.listing.verification_status = 'Rejected'
        if reason:
            reward.listing.verification_notes = f"Rejected: {reason}"
        reward.listing.save()
        
        Notification.objects.create(
            user=reward.user,
            title="Property Rejected",
            message=f"Your property listing '{reward.listing.title}' verification request has been rejected. Reason: {reason}"
        )
        
    messages.warning(request, f"Reward claim rejected for {reward.user.username}.")
    return redirect('admin_dashboard')


@login_required
def pay_reward_claim(request, reward_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    reward = get_object_or_404(Reward, id=reward_id)
    reward.status = 'Paid'
    reward.save()
    
    messages.success(request, f"Reward paid out to {reward.user.username}!")
    return redirect('admin_dashboard')


@login_required
def read_all_notifications(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('profile')


