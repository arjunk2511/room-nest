from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Listing, ListingImage, Wishlist, Message, Review, Lead, City, Area, PropertySubmission, Reward, Notification, RewardWallet, RewardTransaction, WithdrawalRequest, RewardHistory, PaymentHistory, AdminRewardLog
from .utils import check_duplicate_property
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
import math
import json
import urllib.request
import urllib.parse

def get_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def home(request):
    featured_listings = cache.get('home_featured_listings')
    if not featured_listings:
        featured_listings = list(Listing.objects.filter(is_sold=False).select_related('owner__userprofile', 'city', 'area').prefetch_related('images').order_by('-created_at')[:6])
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
        user_listings = list(Listing.objects.filter(owner=request.user).select_related('city', 'area').prefetch_related('images')[:3])
    
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
    listings = Listing.objects.filter(is_sold=False).select_related('owner__userprofile', 'city', 'area').prefetch_related('images').order_by('-created_at')
    
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
    title_parts = []
    desc_parts = []
    
    prop_type = request.GET.get('type', '')
    gender = request.GET.get('target_gender', '')
    
    type_str = ''
    if prop_type:
        if 'pg' in prop_type.lower():
            if 'men' in prop_type.lower() or gender == 'Boys Only':
                type_str = 'PG for Boys'
            elif 'women' in prop_type.lower() or gender == 'Girls Only':
                type_str = 'PG for Girls'
            else:
                type_str = 'PG'
        elif '1bhk' in prop_type.lower():
            type_str = '1 BHK Flat for Rent'
        elif '2bhk' in prop_type.lower():
            type_str = '2 BHK Flat for Rent'
        elif '3bhk' in prop_type.lower():
            type_str = '3 BHK Flat for Rent'
        elif 'single room' in prop_type.lower():
            type_str = 'Single Room for Rent'
        elif 'flatmate' in prop_type.lower():
            type_str = 'Shared Flatmate Stay'
        elif 'co-living' in prop_type.lower():
            type_str = 'Co-living Stay'
        else:
            type_str = f"{prop_type} for Rent"
        title_parts.append(type_str)
    else:
        type_str = "Rooms, PGs & Rental Properties"
        title_parts.append(type_str)
        
    if current_city and current_area:
        title_parts.append(f"in {current_area.name}, {current_city.name}")
        desc_parts.append(f"Discover verified {type_str.lower()} in {current_area.name}, {current_city.name}.")
    elif current_city:
        title_parts.append(f"in {current_city.name}")
        desc_parts.append(f"Discover verified {type_str.lower()} across {current_city.name}.")
    else:
        title_parts.append("in Mysore, Bengaluru & Hyderabad")
        desc_parts.append(f"Discover verified {type_str.lower()} across Mysore, Bengaluru, and Hyderabad.")
        
    title_parts.append("| RoomNest")
    seo_title = " ".join(title_parts)
    
    desc_parts.append("Contact owners directly with zero brokerage, verified listings, and budget-friendly accommodation only on RoomNest.")
    seo_description = " ".join(desc_parts)
    
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

    # Redirect old /listing/<id>/ routes to SEO-friendly /<city>/<slug>/ routes
    canonical_url = listing.get_absolute_url()
    if request.path.startswith('/listing/') and canonical_url != request.path:
        return redirect(canonical_url, permanent=True)

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

    # Dynamic SEO titles & descriptions based on listing details
    city_name = listing.city.name if listing.city else 'Mysore'
    area_name = listing.area.name if listing.area else listing.location
    
    type_lower = listing.type.lower()
    if 'pg (men)' in type_lower:
        type_clean = 'PG for Boys'
    elif 'pg (women)' in type_lower:
        type_clean = 'PG for Girls'
    elif '1bhk' in type_lower:
        type_clean = '1 BHK Flat for Rent'
    elif '2bhk' in type_lower:
        type_clean = '2 BHK Flat for Rent'
    elif '3bhk' in type_lower:
        type_clean = '3 BHK Flat for Rent'
    elif 'single room' in type_lower:
        type_clean = 'Single Room for Rent'
    elif 'co-living' in type_lower:
        type_clean = 'Co-living Room for Rent'
    elif 'flatmate' in type_lower:
        type_clean = 'Shared Flatmate Stay'
    else:
        type_clean = f"{listing.type} for Rent"
        
    seo_title = f"{type_clean} in {area_name}, {city_name} | RoomNest"
    seo_description = f"Find verified {listing.type.lower()} for rent in {area_name}, {city_name}. Rent: ₹{listing.price:.0f}, security deposit: ₹{listing.deposit:.0f}, available: {listing.available_from}. Direct owner contact, zero brokerage only on RoomNest."

    context = {
        'listing': listing,
        'has_subscription': has_subscription,
        'is_wishlisted': is_wishlisted,
        'similar_listings': similar_listings,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'seo_title': seo_title,
        'seo_description': seo_description,
    }
    return render(request, 'details.html', context)

@login_required
def add_property(request):
    import logging
    logger = logging.getLogger(__name__)
    try:
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

            # Check duplicate property details
            lat_val = None
            lng_val = None
            if latitude:
                try:
                    lat_val = float(latitude)
                except ValueError:
                    pass
            if longitude:
                try:
                    lng_val = float(longitude)
                except ValueError:
                    pass

            is_dup, dup_type, dup_reason = check_duplicate_property(
                phone=phone,
                address=address,
                latitude=lat_val,
                longitude=lng_val
            )

            if is_dup:
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
                    built_up_area=built_up_area,
                    is_verified=False,
                    verification_status='Rejected',
                    verification_notes=f"Auto-rejected: Duplicate detected ({dup_reason})"
                )
                
                # Save extra images in parallel to optimize Cloudinary upload times
                if len(images) > 1:
                    import concurrent.futures
                    from django.db import connection

                    def upload_and_create_gallery_image(img_file):
                        try:
                            ListingImage.objects.create(listing=listing, image=img_file)
                        finally:
                            connection.close()

                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                        executor.map(upload_and_create_gallery_image, images[1:])

                # Log Admin Action
                system_user = User.objects.filter(is_superuser=True).first() or request.user
                AdminRewardLog.objects.create(
                    admin_user=system_user,
                    action_type="Auto-Reject Duplicate",
                    target_type="Listing",
                    target_id=listing.id,
                    log_message=f"System auto-rejected verification for listing '{listing.title}' (ID: {listing.id}) as a duplicate. Reason: {dup_reason}."
                )

                # Notify admins
                admins = User.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        title="Duplicate Listing Flagged",
                        message=f"Listing '{listing.title}' (ID: {listing.id}) submitted by {request.user.username} was auto-rejected as a duplicate."
                    )

                # Notify landlord
                Notification.objects.create(
                    user=request.user,
                    title="Property Rejected",
                    message=f"Your property listing '{listing.title}' verification request has been rejected. Reason: Duplicate details detected."
                )

                messages.warning(request, "Property listed, but verification failed: Duplicate details detected.")
                return redirect('owner_dashboard')

            # Create standard listing
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
                built_up_area=built_up_area,
                is_verified=False,
                verification_status='Pending'
            )
            
            # Save extra images in parallel to optimize Cloudinary upload times
            if len(images) > 1:
                import concurrent.futures
                from django.db import connection

                def upload_and_create_gallery_image(img_file):
                    try:
                        ListingImage.objects.create(listing=listing, image=img_file)
                    finally:
                        connection.close()

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    executor.map(upload_and_create_gallery_image, images[1:])
                
            # Send a notification that listing is submitted
            Notification.objects.create(
                user=request.user,
                title="Property Submitted",
                message=f"Your property listing '{listing.title}' has been submitted and is pending verification. You will earn ₹50 once verified and published."
            )
            
            messages.success(request, "Your property listing has been submitted and is pending verification.")
            return redirect('owner_dashboard')
    
        return render(request, 'add_property.html')
    except Exception:
        logger.exception("ADD PROPERTY FAILED")
        raise

@login_required
def toggle_wishlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        wishlist_item.delete()
        saved = False
    else:
        saved = True
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'status': 'success', 'saved': saved})
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('details', listing_id=listing.id)

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__owner').prefetch_related('listing__reviews', 'listing__images')
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
            
            # Delete existing extra gallery images and save new ones in parallel to optimize Cloudinary upload times
            listing.images.all().delete()
            import concurrent.futures
            from django.db import connection

            def upload_and_create_gallery_image(img_file):
                try:
                    ListingImage.objects.create(listing=listing, image=img_file)
                finally:
                    connection.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(upload_and_create_gallery_image, images[1:])
        
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
    from django.db.models import Sum
    
    # Referrals/Submissions status filter
    pending_referrals = PropertySubmission.objects.filter(status__in=['Pending', 'Under Verification']).select_related('submitter', 'city')
    approved_referrals = PropertySubmission.objects.filter(status='Approved').select_related('submitter', 'city')
    published_referrals = PropertySubmission.objects.filter(status='Published').select_related('submitter', 'city')
    rejected_referrals = PropertySubmission.objects.filter(status='Rejected').select_related('submitter', 'city')
    
    # Withdrawal Requests
    pending_withdrawals = WithdrawalRequest.objects.filter(status='Pending').select_related('user')
    paid_withdrawals = WithdrawalRequest.objects.filter(status='Paid').select_related('user')
    rejected_withdrawals = WithdrawalRequest.objects.filter(status='Rejected').select_related('user')
    
    # Financial indicators
    total_rewards_paid = PaymentHistory.objects.aggregate(total=Sum('amount'))['total'] or 0.00
    
    # Counters
    pending_rewards_count = pending_referrals.count()
    approved_rewards_count = RewardHistory.objects.filter(status='Available').count()
    rejected_rewards_count = RewardHistory.objects.filter(status='Rejected').count()
    awaiting_payout_amount = approved_rewards_count * 50.00
    
    # Top Contributors (Leaderboard)
    top_contributors = User.objects.annotate(
        approved_count=Count('property_submissions', filter=Q(property_submissions__status__in=['Approved', 'Published']))
    ).filter(approved_count__gt=0).order_by('-approved_count')[:10]
    
    # Most Active Cities
    most_active_cities = City.objects.annotate(
        sub_count=Count('propertysubmission')
    ).filter(sub_count__gt=0).order_by('-sub_count')[:5]
    
    # Logs
    admin_logs = AdminRewardLog.objects.all().select_related('admin_user')[:25]
    
    return render(request, 'admin_dashboard.html', {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'pending_subscriptions_count': pending_subscriptions_count,
        'total_revenue': total_revenue,
        'pending_verifications': pending_verifications,
        'pending_subscriptions': pending_subscriptions,
        
        # Referral reward & wallet stats
        'pending_referrals': pending_referrals,
        'approved_referrals': approved_referrals,
        'published_referrals': published_referrals,
        'rejected_referrals': rejected_referrals,
        'pending_withdrawals': pending_withdrawals,
        'paid_withdrawals': paid_withdrawals,
        'rejected_withdrawals': rejected_withdrawals,
        'total_rewards_paid': total_rewards_paid,
        'pending_rewards_count': pending_rewards_count,
        'approved_rewards_count': approved_rewards_count,
        'rejected_rewards_count': rejected_rewards_count,
        'awaiting_payout_amount': awaiting_payout_amount,
        'top_contributors': top_contributors,
        'most_active_cities': most_active_cities,
        'admin_logs': admin_logs,
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
    
    # Automatically create a reward (₹50 Available) for direct owner listing (Owner Bonus System)
    # Ensure reward history doesn't already exist for this listing
    if not RewardHistory.objects.filter(listing=listing).exists():
        reward = RewardHistory.objects.create(
            user=listing.owner,
            listing=listing,
            property_title=listing.title,
            city=listing.city.name if listing.city else listing.location,
            reward_amount=50.00,
            status='Available',
            approval_date=timezone.now()
        )
        
        # Credit owner wallet
        wallet = RewardWallet.get_or_create_wallet(listing.owner)
        wallet.available_balance += 50.00
        wallet.total_earned += 50.00
        wallet.save()
        
        # Log Transaction
        RewardTransaction.objects.create(
            wallet=wallet,
            transaction_type='Credit',
            amount=50.00,
            description=f"Reward for direct owner listing '{listing.title}' approved and verified."
        )
        
        # Send Notification for Reward Credited
        Notification.objects.create(
            user=listing.owner,
            title="Reward Credited",
            message="Congratulations! ₹50 reward has been credited to your available wallet balance for successfully listing and verifying your property."
        )

    # Log Admin Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Approve Verification",
        target_type="Listing",
        target_id=listing.id,
        log_message=f"Admin approved verification for listing '{listing.title}' (ID: {listing.id})."
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
    
    # Log Admin Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Reject Verification",
        target_type="Listing",
        target_id=listing.id,
        log_message=f"Admin rejected verification for listing '{listing.title}' (ID: {listing.id}). Reason: {notes or 'No reason provided.'}"
    )
        
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
        ).select_related('owner__userprofile', 'city', 'area').prefetch_related('images').order_by('-created_at')[:6])
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
        
    seo_title = f"Rooms, PGs & Rental Properties in {page_data['city'].name} | RoomNest"
    seo_description = f"Find verified rooms, PGs, flats and rental properties in {page_data['city'].name} with zero brokerage. Contact owners directly on RoomNest."

    return render(request, 'city_page.html', {
        'city': page_data['city'],
        'listings': page_data['listings'],
        'areas': page_data['areas'],
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids,
        'seo_title': seo_title,
        'seo_description': seo_description
    })


def area_page(request, city_slug, area_slug):
    # Check if this slug matches a Listing first
    listing = Listing.objects.filter(city__slug=city_slug, slug=area_slug).first()
    if listing:
        return details(request, listing_id=listing.id)

    # Otherwise, it is an Area Landing Page
    city = get_object_or_404(City, slug=city_slug, is_active=True)
    area = get_object_or_404(Area, city=city, slug=area_slug, is_active=True)
    
    # Fetch all active listings in this area
    listings = Listing.objects.filter(
        city=city,
        area=area,
        is_sold=False
    ).select_related('owner__userprofile', 'city', 'area').prefetch_related('images').order_by('-created_at')
    
    # Calculate Average Monthly Rent in Area
    avg_rent = listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0.0
    
    # Calculate average coordinates of properties in area
    coords = listings.filter(latitude__isnull=False, longitude__isnull=False)
    if coords.exists():
        avg_lat = float(coords.aggregate(avg_lat=Avg('latitude'))['avg_lat'])
        avg_lng = float(coords.aggregate(avg_lng=Avg('longitude'))['avg_lng'])
    else:
        # Fallback coordinates based on City slug
        if city.slug == "bengaluru":
            avg_lat, avg_lng = 12.9716, 77.5946
        elif city.slug == "hyderabad":
            avg_lat, avg_lng = 17.3850, 78.4867
        else: # mysore default
            avg_lat, avg_lng = 12.2958, 76.6394
            
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
        
    seo_title = f"Rooms, PGs & Rental Properties in {area.name}, {city.name} | RoomNest"
    seo_description = f"Explore flats, PGs, rooms and co-living spaces for rent in {area.name}, {city.name} with direct owner contacts. Interactive Area Map and proximity indicators included."
    
    return render(request, 'area_page.html', {
        'city': city,
        'area': area,
        'listings': listings,
        'total_count': listings.count(),
        'avg_rent': int(round(avg_rent)),
        'latitude': avg_lat,
        'longitude': avg_lng,
        'has_subscription': has_subscription,
        'wishlist_ids': wishlist_ids,
        'seo_title': seo_title,
        'seo_description': seo_description
    })


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
        
        # Anti-spam protection & duplicate checks using check_duplicate_property
        is_dup, dup_type, dup_reason = check_duplicate_property(
            phone=owner_mobile,
            address=property_address
        )
        
        if is_dup:
            # Create a rejected submission to keep records of duplicate attempts
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
                notes=f"{notes}\n\nAuto-rejected: Duplicate property details detected ({dup_reason}).".strip(),
                permission_confirmed=True,
                status='Rejected'
            )
            
            # Log in AdminRewardLog
            system_user = User.objects.filter(is_superuser=True).first() or request.user
            AdminRewardLog.objects.create(
                admin_user=system_user,
                action_type="Auto-Reject Duplicate",
                target_type="PropertySubmission",
                target_id=submission.id,
                log_message=f"System automatically rejected property submission #{submission.id} by {request.user.username} as a duplicate. Reason: {dup_reason}."
            )

            # Notify user
            Notification.objects.create(
                user=request.user,
                title="Property Rejected",
                message=f"Your property submission for the {property_type} in {city_obj.name} has been rejected. Reason: Duplicate details detected."
            )
            
            # Notify admins
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title="Duplicate Referral Flagged",
                    message=f"Property submission #{submission.id} by {request.user.username} was auto-rejected as a duplicate."
                )
                
            messages.warning(request, "Your submission was flagged and rejected as a duplicate. The property is already listed or submitted on RoomNest.")
            return redirect('profile')
             
        # Create standard pending submission
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
        
        # Send Notification
        Notification.objects.create(
            user=request.user,
            title="Property Submitted",
            message=f"Your property submission for the {property_type} in {city_obj.name} has been received. You will receive ₹50 once verified and published."
        )
        
        messages.success(request, "Your property submission has been received successfully!")
        return redirect('profile')
        
    return render(request, 'earn_rewards.html', {'active_cities': active_cities})


@login_required
def request_withdrawal(request):
    if request.method != 'POST':
        return redirect('profile')
        
    amount_str = request.POST.get('amount', '').strip()
    upi_id = request.POST.get('upi_id', '').strip()
    
    # Validation
    import re
    UPI_REGEX = r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$'
    
    if not amount_str or not upi_id:
        messages.error(request, "Please enter both amount and UPI ID.")
        return redirect('profile')
        
    if not re.match(UPI_REGEX, upi_id):
        messages.error(request, "Invalid UPI ID format. Please use format like username@ybl.")
        return redirect('profile')
        
    try:
        from decimal import Decimal
        amount = Decimal(amount_str)
    except Exception:
        messages.error(request, "Invalid amount format.")
        return redirect('profile')
        
    if amount < 200:
        messages.error(request, "Minimum withdrawal amount is ₹200.")
        return redirect('profile')
        
    # Get user wallet
    wallet = RewardWallet.get_or_create_wallet(request.user)
    
    if wallet.available_balance < amount:
        messages.error(request, "Insufficient balance in your wallet.")
        return redirect('profile')
        
    # Update balance immediately to prevent double spending
    wallet.available_balance -= amount
    wallet.upi_id = upi_id
    wallet.save()
    
    # Create withdrawal request
    req = WithdrawalRequest.objects.create(
        user=request.user,
        amount=amount,
        upi_id=upi_id,
        status='Pending'
    )
    
    # Create RewardTransaction
    RewardTransaction.objects.create(
        wallet=wallet,
        transaction_type='Debit',
        amount=amount,
        description=f"Withdrawal requested to {upi_id} (Req ID: {req.id})"
    )
    
    # Send Notification
    Notification.objects.create(
        user=request.user,
        title="Withdrawal Requested",
        message=f"Your request for withdrawal of ₹{amount} to UPI ID {upi_id} has been received and is pending verification."
    )
    
    messages.success(request, f"Withdrawal request of ₹{amount} submitted successfully!")
    return redirect('profile')


@login_required
def admin_approve_submission(request, submission_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    submission = get_object_or_404(PropertySubmission, id=submission_id)
    submission.status = 'Approved'
    submission.save()
    
    # Log Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Approve Submission",
        target_type="PropertySubmission",
        target_id=submission.id,
        log_message=f"Admin approved referral property submission #{submission.id}."
    )
    
    # Send Notification to referrer
    Notification.objects.create(
        user=submission.submitter,
        title="Property Referral Approved",
        message=f"Your property referral for the {submission.property_type} in {submission.city.name if submission.city else 'Unknown'} has been verified and approved. Once published, your ₹50 reward will be added."
    )
    
    messages.success(request, f"Property submission #{submission.id} approved successfully!")
    return redirect('admin_dashboard')


@login_required
def admin_reject_submission(request, submission_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    submission = get_object_or_404(PropertySubmission, id=submission_id)
    
    reason = request.POST.get('rejection_notes', '').strip() or "Verification criteria not met."
    
    submission.status = 'Rejected'
    submission.notes = f"{submission.notes}\n\nRejected: {reason}".strip()
    submission.save()
    
    # Log Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Reject Submission",
        target_type="PropertySubmission",
        target_id=submission.id,
        log_message=f"Admin rejected referral property submission #{submission.id}. Reason: {reason}"
    )
    
    # Send Notification to referrer
    Notification.objects.create(
        user=submission.submitter,
        title="Property Referral Rejected",
        message=f"Your property referral has been rejected. Reason: {reason}"
    )
    
    messages.warning(request, f"Property submission #{submission.id} rejected.")
    return redirect('admin_dashboard')


@login_required
def admin_publish_submission(request, submission_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    submission = get_object_or_404(PropertySubmission, id=submission_id)
    
    if submission.status != 'Approved':
        messages.error(request, "Only verified/approved property submissions can be published.")
        return redirect('admin_dashboard')
        
    # Check if a reward is already generated for this submission
    if RewardHistory.objects.filter(property_submission=submission).exists():
        messages.error(request, "A reward has already been created for this submission.")
        return redirect('admin_dashboard')
        
    # Create the Listing
    # Resolve the owner: check if there's a UserProfile with owner_mobile phone_number
    from accounts.models import UserProfile
    owner_profile = UserProfile.objects.filter(phone_number=submission.owner_mobile).first()
    listing_owner = owner_profile.user if owner_profile else submission.submitter
    
    # Map property type
    mapped_type = 'Single Room'
    type_lower = submission.property_type.lower()
    if 'room' in type_lower:
        mapped_type = 'Single Room'
    elif 'pg' in type_lower:
        mapped_type = 'PG (Men)' # default
    elif 'flat' in type_lower:
        mapped_type = '2BHK' # default
    elif 'commercial' in type_lower:
        mapped_type = 'Commercial Space'
    elif 'house' in type_lower:
        mapped_type = '2BHK' # default
        
    # Get first area in city as fallback
    area_obj = submission.city.areas.filter(is_active=True).first() if submission.city else None
    location_name = area_obj.name if area_obj else "Vijayanagar"
    
    listing = Listing.objects.create(
        title=f"{submission.property_type} in {submission.city.name if submission.city else 'Mysore'}",
        location=location_name[:50],
        city=submission.city,
        area=area_obj,
        price=10000.00, # default price
        type=mapped_type,
        description=f"Verified property listing referred by {submission.submitted_by_name}. Owner contact: {submission.owner_name}.",
        facilities="WiFi, Parking", # defaults
        address=submission.property_address,
        phone=submission.owner_mobile,
        owner=listing_owner,
        image=submission.photo if submission.photo else None,
        is_verified=True,
        verification_status='Verified',
        verification_notes=f"Referred by {submission.submitter.username} and published by Admin."
    )
    
    submission.status = 'Published'
    submission.save()
    
    # Automatically create a reward (₹50 Available) for referrer
    reward = RewardHistory.objects.create(
        user=submission.submitter,
        listing=listing,
        property_submission=submission,
        property_title=listing.title,
        city=submission.city.name if submission.city else "Mysore",
        reward_amount=50.00,
        status='Available',
        approval_date=timezone.now()
    )
    
    # Credit referrer's wallet
    wallet = RewardWallet.get_or_create_wallet(submission.submitter)
    wallet.available_balance += 50.00
    wallet.total_earned += 50.00
    wallet.save()
    
    # Log transaction
    RewardTransaction.objects.create(
        wallet=wallet,
        transaction_type='Credit',
        amount=50.00,
        description=f"Reward for referral submission #{submission.id} published."
    )
    
    # Log Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Publish Submission",
        target_type="PropertySubmission",
        target_id=submission.id,
        log_message=f"Admin published referral submission #{submission.id} to Listing #{listing.id} and credited reward to {submission.submitter.username}."
    )
    
    # Send Notification to referrer
    Notification.objects.create(
        user=submission.submitter,
        title="Reward Added",
        message=f"Congratulations! ₹50 reward has been added to your wallet available balance for the published listing in {submission.city.name if submission.city else 'Mysore'}."
    )
    
    messages.success(request, f"Property submission #{submission.id} published as Listing #{listing.id} successfully!")
    return redirect('admin_dashboard')


@login_required
def admin_pay_withdrawal(request, withdrawal_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    req = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if req.status in ['Paid', 'Rejected']:
        messages.error(request, f"Withdrawal request is already {req.status.lower()}.")
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'UPI').strip()
        transaction_ref = request.POST.get('transaction_ref', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not transaction_ref:
            messages.error(request, "Transaction Reference / UTR is required.")
            return redirect('admin_dashboard')
            
        req.status = 'Paid'
        req.paid_date = timezone.now()
        req.transaction_id = transaction_ref
        req.admin_notes = notes
        req.save()
        
        # Credit user's wallet withdrawn amount
        wallet = RewardWallet.get_or_create_wallet(req.user)
        wallet.withdrawn_amount += req.amount
        wallet.save()
        
        # Create PaymentHistory
        PaymentHistory.objects.create(
            withdrawal_request=req,
            user=req.user,
            amount=req.amount,
            upi_id=req.upi_id,
            payment_method=payment_method,
            transaction_reference=transaction_ref,
            paid_date=timezone.now(),
            admin_notes=notes
        )
        
        # Update RewardHistory records to Paid up to the amount
        amount_to_cover = req.amount
        rewards_to_update = RewardHistory.objects.filter(user=req.user, status='Available').order_by('created_date')
        for r in rewards_to_update:
            if amount_to_cover <= 0:
                break
            if r.reward_amount <= amount_to_cover:
                r.status = 'Paid'
                r.payment_date = timezone.now()
                r.save()
                amount_to_cover -= r.reward_amount
            else:
                r.status = 'Paid'
                r.payment_date = timezone.now()
                r.save()
                amount_to_cover = 0
                
        # Log Action
        AdminRewardLog.objects.create(
            admin_user=request.user,
            action_type="Pay Withdrawal",
            target_type="WithdrawalRequest",
            target_id=req.id,
            log_message=f"Admin paid withdrawal request #{req.id} of ₹{req.amount} via {payment_method}. UTR: {transaction_ref}."
        )
        
        # Notify user
        Notification.objects.create(
            user=req.user,
            title="Payment Completed",
            message=f"Your withdrawal request of ₹{req.amount} has been paid via {payment_method}. Transaction ID: {transaction_ref}."
        )
        
        messages.success(request, f"Withdrawal request #{req.id} marked as Paid successfully!")
        
    return redirect('admin_dashboard')


@login_required
def admin_reject_withdrawal(request, withdrawal_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    req = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if req.status in ['Paid', 'Rejected']:
        messages.error(request, f"Withdrawal request is already {req.status.lower()}.")
        return redirect('admin_dashboard')
        
    reason = request.POST.get('rejection_notes', '').strip() or "Criteria not met."
    
    req.status = 'Rejected'
    req.admin_notes = f"Rejected: {reason}"
    req.save()
    
    # Refund balance to user wallet
    wallet = RewardWallet.get_or_create_wallet(req.user)
    wallet.available_balance += req.amount
    wallet.save()
    
    # Log refund transaction
    RewardTransaction.objects.create(
        wallet=wallet,
        transaction_type='Credit',
        amount=req.amount,
        description=f"Refund for rejected withdrawal request #{req.id}"
    )
    
    # Log Action
    AdminRewardLog.objects.create(
        admin_user=request.user,
        action_type="Reject Withdrawal",
        target_type="WithdrawalRequest",
        target_id=req.id,
        log_message=f"Admin rejected withdrawal request #{req.id} of ₹{req.amount}. Reason: {reason}."
    )
    
    # Notify user
    Notification.objects.create(
        user=req.user,
        title="Withdrawal Rejected",
        message=f"Your withdrawal request of ₹{req.amount} has been rejected. Reason: {reason}. Amount refunded to your available balance."
    )
    
    messages.warning(request, f"Withdrawal request #{req.id} rejected. Balance refunded.")
    return redirect('admin_dashboard')


@login_required
def export_rewards_report(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect('home')
        
    report_format = request.GET.get('format', 'csv').lower()
    report_type = request.GET.get('type', 'rewards').lower()
    
    if report_type == 'payments':
        headers = ['Payment ID', 'User', 'Amount', 'UPI ID', 'Payment Method', 'Transaction UTR', 'Date Paid', 'Admin Notes']
        rows = []
        payments = PaymentHistory.objects.all().select_related('user').order_by('-paid_date')
        for p in payments:
            rows.append([
                p.id, p.user.username, p.amount, p.upi_id, p.payment_method, p.transaction_reference, p.paid_date.strftime('%Y-%m-%d %H:%M'), p.admin_notes
            ])
        filename = f"Payment_Report_{timezone.now().strftime('%Y%m%d')}"
    elif report_type == 'top_contributors':
        headers = ['Rank', 'User', 'Total Referrals Submitted', 'Approved Referrals', 'Total Earned (₹)']
        rows = []
        from django.db.models import Sum
        top_users = User.objects.annotate(
            total_referrals=Count('property_submissions'),
            approved_referrals=Count('property_submissions', filter=Q(property_submissions__status__in=['Approved', 'Published'])),
            earned=Sum('reward_histories__reward_amount')
        ).filter(total_referrals__gt=0).order_by('-approved_referrals', '-total_referrals')
        
        for idx, u in enumerate(top_users):
            rows.append([
                idx + 1, u.username, u.total_referrals, u.approved_referrals, float(u.earned or 0.00)
            ])
        filename = f"Top_Contributors_{timezone.now().strftime('%Y%m%d')}"
    elif report_type == 'pending':
        headers = ['Submission ID', 'Submitter', 'Type', 'Owner Name', 'Owner Mobile', 'Address', 'City', 'Submitted Date']
        rows = []
        subs = PropertySubmission.objects.filter(status__in=['Pending', 'Under Verification']).select_related('submitter', 'city').order_by('-created_at')
        for s in subs:
            rows.append([
                s.id, s.submitter.username, s.property_type, s.owner_name, s.owner_mobile, s.property_address, s.city.name if s.city else 'Unknown', s.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        filename = f"Pending_Referrals_{timezone.now().strftime('%Y%m%d')}"
    else:
        headers = ['Reward ID', 'User', 'Property Title', 'City', 'Amount', 'Created Date', 'Approval Date', 'Status']
        rows = []
        rewards = RewardHistory.objects.all().select_related('user').order_by('-created_date')
        for r in rewards:
            rows.append([
                r.id, r.user.username, r.property_title, r.city, r.reward_amount, r.created_date.strftime('%Y-%m-%d %H:%M'), r.approval_date.strftime('%Y-%m-%d %H:%M') if r.approval_date else 'N/A', r.status
            ])
        filename = f"Reward_Report_{timezone.now().strftime('%Y%m%d')}"
        
    if report_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return response
        
    elif report_format == 'excel':
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
        html = '<html><head><meta charset="utf-8"></head><body><table border="1"><tr>'
        for h in headers:
            html += f'<th>{h}</th>'
        html += '</tr>'
        for r in rows:
            html += '<tr>'
            for val in r:
                html += f'<td>{val}</td>'
            html += '</tr>'
        html += '</table></body></html>'
        response.write(html)
        return response
        
    elif report_format == 'pdf':
        context = {
            'headers': headers,
            'rows': rows,
            'report_title': report_type.replace('_', ' ').title(),
            'generated_at': timezone.now().strftime('%B %d, %Y - %H:%M'),
        }
        return render(request, 'reports/report_print.html', context)
        
    messages.error(request, "Invalid export format specified.")
    return redirect('admin_dashboard')


@login_required
def read_all_notifications(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('profile')


def listing_landmarks_api(request, listing_id=None):
    listing = None
    lat = None
    lng = None
    location_name = ""
    
    if listing_id:
        listing = get_object_or_404(Listing, id=listing_id)
        if listing.nearby_landmarks_cache:
            try:
                cached_data = json.loads(listing.nearby_landmarks_cache)
                if cached_data:
                    return JsonResponse(cached_data)
            except Exception:
                pass
        lat = listing.latitude
        lng = listing.longitude
        location_name = listing.location
    else:
        lat_val = request.GET.get('lat')
        lng_val = request.GET.get('lng')
        location_name = request.GET.get('location', '')
        if lat_val and lng_val:
            try:
                lat = float(lat_val)
                lng = float(lng_val)
            except ValueError:
                pass

    # Define fallback mock data based on location area
    loc = (location_name or "").lower()
    fallback_data = {
        "schools": [
            { "name": "Nirmala High School", "distance": "0.6 km", "drive_time": "3 min", "walk_time": "7 min", "icon": "🏫" },
            { "name": "Aditya First Grade College", "distance": "1.2 km", "drive_time": "5 min", "walk_time": "14 min", "icon": "🎓" }
        ],
        "hospitals": [
            { "name": "Adithya Hospital", "distance": "0.8 km", "drive_time": "4 min", "walk_time": "9 min", "icon": "🏥" },
            { "name": "Chandrakala Hospital", "distance": "1.5 km", "drive_time": "6 min", "walk_time": "18 min", "icon": "⚕️" }
        ],
        "transit": [
            { "name": "Gokulam Bus Stop", "distance": "0.2 km", "drive_time": "1 min", "walk_time": "2 min", "icon": "🚌" },
            { "name": "Mysore Junction Railway Station", "distance": "3.2 km", "drive_time": "10 min", "walk_time": "38 min", "icon": "🚆" }
        ],
        "shopping": [
            { "name": "Loyal World Supermarket", "distance": "0.4 km", "drive_time": "2 min", "walk_time": "5 min", "icon": "🛒" },
            { "name": "Corner House Ice Cream", "distance": "0.3 km", "drive_time": "1 min", "walk_time": "3 min", "icon": "🍦" }
        ]
    }
    
    if "vijayanagar" in loc:
        fallback_data = {
            "schools": [
                { "name": "National Public School", "distance": "0.8 km", "drive_time": "4 min", "walk_time": "9 min", "icon": "🏫" },
                { "name": "Amrita Vidyalayam", "distance": "1.4 km", "drive_time": "6 min", "walk_time": "16 min", "icon": "🎓" }
            ],
            "hospitals": [
                { "name": "BM Hospital", "distance": "1.1 km", "drive_time": "5 min", "walk_time": "13 min", "icon": "🏥" },
                { "name": "Columbia Asia Hospital", "distance": "4.5 km", "drive_time": "14 min", "walk_time": "54 min", "icon": "⚕️" }
            ],
            "transit": [
                { "name": "Vijayanagar Water Tank Bus Stop", "distance": "0.3 km", "drive_time": "1 min", "walk_time": "3 min", "icon": "🚌" },
                { "name": "Mysore Railway Station", "distance": "4.0 km", "drive_time": "12 min", "walk_time": "48 min", "icon": "🚆" }
            ],
            "shopping": [
                { "name": "Abhishek Circle Market", "distance": "0.5 km", "drive_time": "2 min", "walk_time": "6 min", "icon": "🛒" },
                { "name": "Empire Restaurant", "distance": "0.7 km", "drive_time": "3 min", "walk_time": "8 min", "icon": "🍔" }
            ]
        }
    elif "hebbal" in loc:
        fallback_data = {
            "schools": [
                { "name": "Kendriya Vidyalaya", "distance": "1.0 km", "drive_time": "5 min", "walk_time": "12 min", "icon": "🏫" },
                { "name": "East West International School", "distance": "1.5 km", "drive_time": "7 min", "walk_time": "18 min", "icon": "🎓" }
            ],
            "hospitals": [
                { "name": "Columbia Asia Hospital", "distance": "1.8 km", "drive_time": "7 min", "walk_time": "21 min", "icon": "🏥" },
                { "name": "Narayana Multispeciality Hospital", "distance": "3.5 km", "drive_time": "11 min", "walk_time": "42 min", "icon": "⚕️" }
            ],
            "transit": [
                { "name": "Hebbal Industrial Area Bus Stop", "distance": "0.4 km", "drive_time": "2 min", "walk_time": "4 min", "icon": "🚌" },
                { "name": "Mysore Railway Station", "distance": "6.5 km", "drive_time": "18 min", "walk_time": "78 min", "icon": "🚆" }
            ],
            "shopping": [
                { "name": "Reliance Smart Superstore", "distance": "0.9 km", "drive_time": "4 min", "walk_time": "10 min", "icon": "🛒" },
                { "name": "Hebbal Lake Park Café", "distance": "1.2 km", "drive_time": "5 min", "walk_time": "14 min", "icon": "☕" }
            ]
        }

    if not lat or not lng:
        return JsonResponse(fallback_data)
        
    try:
        lat = float(lat)
        lng = float(lng)
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""[out:json][timeout:8];
        (
          node(around:5000,{lat},{lng})[amenity~"school|college|university|hospital|clinic|bus_station|restaurant|cafe|bank|fuel|gym|park|mall|cinema|supermarket|marketplace"];
          way(around:5000,{lat},{lng})[amenity~"school|college|university|hospital|clinic|bus_station|restaurant|cafe|bank|fuel|gym|park|mall|cinema|supermarket|marketplace"];
          node(around:5000,{lat},{lng})[railway~"station|subway_entrance"];
          node(around:5000,{lat},{lng})[shop~"supermarket|mall|department_store"];
          way(around:5000,{lat},{lng})[shop~"supermarket|mall|department_store"];
          node(around:5000,{lat},{lng})[office~"it|technology"];
          way(around:5000,{lat},{lng})[office~"it|technology"];
          node(around:5000,{lat},{lng})[leisure~"park|gym|sports_centre"];
          way(around:5000,{lat},{lng})[leisure~"park|gym|sports_centre"];
          node(around:15000,{lat},{lng})[aeroway="aerodrome"];
        );
        out body center;"""
        
        req = urllib.request.Request(
            overpass_url,
            data=urllib.parse.urlencode({'data': overpass_query}).encode('utf-8'),
            headers={'User-Agent': 'RoomNestProximitySystem/1.0 (contact@roomnest.online)'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            overpass_res = json.loads(response.read().decode('utf-8'))
            
        elements = overpass_res.get('elements', [])
        
        raw_categories = {
            "schools": [], "colleges": [], "hospitals": [], "bus_stops": [],
            "metro_stations": [], "railway_stations": [], "airports": [], "supermarkets": [],
            "restaurants": [], "cafes": [], "banks": [], "petrol_pumps": [],
            "gyms": [], "parks": [], "it_parks": [], "malls": []
        }
        
        for el in elements:
            tags = el.get('tags', {})
            name = tags.get('name')
            if not name:
                continue
                
            e_lat = el.get('lat') or el.get('center', {}).get('lat')
            e_lng = el.get('lon') or el.get('center', {}).get('lon')
            if not e_lat or not e_lng:
                continue
                
            dist_straight = get_haversine_distance(lat, lng, e_lat, e_lng)
            
            amenity = tags.get('amenity', '')
            shop = tags.get('shop', '')
            railway = tags.get('railway', '')
            leisure = tags.get('leisure', '')
            office = tags.get('office', '')
            aeroway = tags.get('aeroway', '')
            highway = tags.get('highway', '')
            
            item = {"name": name, "lat": e_lat, "lng": e_lng, "dist_straight": dist_straight}
            
            if amenity == 'school' or (amenity == 'university' and 'school' in name.lower()):
                raw_categories["schools"].append((item, "🏫"))
            elif amenity == 'college' or amenity == 'university':
                raw_categories["colleges"].append((item, "🎓"))
            elif amenity in ['hospital', 'clinic']:
                raw_categories["hospitals"].append((item, "🏥"))
            elif amenity == 'bus_station' or highway == 'bus_stop' or 'bus stop' in name.lower() or 'bus stand' in name.lower():
                raw_categories["bus_stops"].append((item, "🚌"))
            elif railway == 'subway_entrance' or 'metro' in name.lower():
                raw_categories["metro_stations"].append((item, "🚇"))
            elif railway == 'station' or 'railway station' in name.lower() or 'junction' in name.lower():
                raw_categories["railway_stations"].append((item, "🚉"))
            elif aeroway == 'aerodrome' or 'airport' in name.lower():
                raw_categories["airports"].append((item, "✈️"))
            elif shop == 'supermarket' or amenity == 'supermarket':
                raw_categories["supermarkets"].append((item, "🛒"))
            elif amenity == 'restaurant':
                raw_categories["restaurants"].append((item, "🍽"))
            elif amenity == 'cafe':
                raw_categories["cafes"].append((item, "☕"))
            elif amenity == 'bank':
                raw_categories["banks"].append((item, "🏦"))
            elif amenity == 'fuel':
                raw_categories["petrol_pumps"].append((item, "⛽"))
            elif leisure == 'gym' or amenity == 'gym' or leisure == 'sports_centre':
                raw_categories["gyms"].append((item, "🏋️"))
            elif leisure == 'park' or amenity == 'park':
                raw_categories["parks"].append((item, "🌳"))
            elif office == 'it' or 'it park' in name.lower() or 'technology' in name.lower():
                raw_categories["it_parks"].append((item, "🏢"))
            elif shop == 'mall' or amenity == 'mall' or 'mall' in name.lower():
                raw_categories["malls"].append((item, "🏬"))
                
        selected_destinations = []
        category_indices = {}
        
        for cat_name, items in raw_categories.items():
            items.sort(key=lambda x: x[0]['dist_straight'])
            top_items = items[:2]
            category_indices[cat_name] = []
            for item, icon in top_items:
                dest_idx = len(selected_destinations)
                selected_destinations.append({"lat": item['lat'], "lng": item['lng'], "name": item['name'], "icon": icon})
                category_indices[cat_name].append(dest_idx)
                
        if not selected_destinations:
            return JsonResponse(fallback_data)
            
        coords = [f"{lng},{lat}"]
        for d in selected_destinations:
            coords.append(f"{d['lng']},{d['lat']}")
            
        coords_str = ";".join(coords)
        osrm_url = f"https://router.project-osrm.org/table/v1/driving/{coords_str}?sources=0&annotations=duration,distance"
        
        req_osrm = urllib.request.Request(osrm_url, headers={'User-Agent': 'RoomNestProximitySystem/1.0'})
        with urllib.request.urlopen(req_osrm, timeout=8) as response:
            osrm_res = json.loads(response.read().decode('utf-8'))
            
        distances = osrm_res.get('distances', [[]])[0]
        durations = osrm_res.get('durations', [[]])[0]
        
        for idx, dest in enumerate(selected_destinations):
            val_idx = idx + 1
            road_dist_m = distances[val_idx] if val_idx < len(distances) else None
            duration_s = durations[val_idx] if val_idx < len(durations) else None
            
            if road_dist_m is None:
                road_dist_m = selected_destinations[idx].get('dist_straight', 1.0) * 1000.0
                
            if road_dist_m < 1000:
                dist_str = f"{int(road_dist_m)} m"
            else:
                dist_str = f"{(road_dist_m / 1000.0):.1f} km"
                
            if duration_s is not None:
                drive_min = max(1, int(round(duration_s / 60.0)))
            else:
                drive_min = max(1, int(round((road_dist_m / 1000.0) * 2.0)))
                
            walk_min = max(1, int(round(road_dist_m / (1.33 * 60.0))))
            
            dest["distance"] = dist_str
            dest["drive_time"] = f"{drive_min} min drive"
            dest["walk_time"] = f"{walk_min} min walk"
            
        tab_data = {
            "schools": [],
            "hospitals": [],
            "transit": [],
            "shopping": []
        }
        
        tab_mappings = {
            "schools": ["schools", "colleges"],
            "hospitals": ["hospitals"],
            "transit": ["bus_stops", "metro_stations", "railway_stations", "airports"],
            "shopping": ["supermarkets", "restaurants", "cafes", "banks", "petrol_pumps", "gyms", "parks", "it_parks", "malls"]
        }
        
        for tab_name, sub_cats in tab_mappings.items():
            for sub_cat in sub_cats:
                indices = category_indices.get(sub_cat, [])
                for idx in indices:
                    dest = selected_destinations[idx]
                    tab_data[tab_name].append({
                        "name": dest["name"],
                        "distance": dest["distance"],
                        "drive_time": dest["drive_time"],
                        "walk_time": dest["walk_time"],
                        "icon": dest["icon"]
                    })
                    
        if listing:
            listing.nearby_landmarks_cache = json.dumps(tab_data)
            listing.save()
        
        return JsonResponse(tab_data)
        
    except Exception as e:
        print(f"Landmark discovery failed: {e}")
        return JsonResponse(fallback_data)


