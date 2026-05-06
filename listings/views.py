from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Listing, ListingImage, Wishlist, Message, Review
from django.db.models import Q, Avg
from django.contrib.auth.models import User
from subscriptions.models import Subscription
from django.utils import timezone

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'welcome.html')
    featured_listings = Listing.objects.filter(is_sold=False).order_by('-created_at')[:6]
    return render(request, 'index.html', {'listings': featured_listings})

def search(request):
    listings = Listing.objects.filter(is_sold=False)
    
    location = request.GET.get('location')
    max_price = request.GET.get('price')
    listing_type = request.GET.get('type')
    
    if location:
        listings = listings.filter(location__icontains=location)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    if listing_type:
        listings = listings.filter(type__iexact=listing_type)
        
    context = {
        'listings': listings,
        'values': request.GET
    }
    return render(request, 'search.html', context)

def details(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    has_subscription = False
    is_wishlisted = False
    
    if request.user.is_authenticated:
        # Check active subscription
        sub = Subscription.objects.filter(user=request.user, is_active=True, end_date__gte=timezone.now()).first()
        if sub or request.user == listing.owner:
            has_subscription = True
        
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
        
        images = request.FILES.getlist('images')
        main_image = images[0] if images else None
        
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
            owner=request.user
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
    wishlist_items = Wishlist.objects.filter(user=request.user)
    listings = [item.listing for item in wishlist_items]
    return render(request, 'wishlist.html', {'listings': listings})

@login_required
def owner_dashboard(request):
    listings = Listing.objects.filter(owner=request.user)
    return render(request, 'owner_dashboard.html', {'listings': listings})

@login_required
def toggle_sold_status(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    listing.is_sold = not listing.is_sold
    listing.save()
    return redirect('owner_dashboard')

import re

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        listing_id = request.POST.get('listing_id')
        listing = Listing.objects.filter(id=listing_id).first() if listing_id else None
        
        if content:
            # Mask phone numbers in the chat message to prevent bypassing the subscription!
            # Matches 10 digit numbers, or numbers with spaces/dashes that look like phone numbers
            masked_content = re.sub(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', '[PHONE NUMBER HIDDEN]', content)
            # Also catch sequences of 10 digits
            masked_content = re.sub(r'\b\d{10}\b', '[PHONE NUMBER HIDDEN]', masked_content)
            
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
