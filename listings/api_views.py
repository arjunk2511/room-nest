import os
import json
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from django.utils import timezone
from accounts.models import UserProfile
from listings.models import (
    Listing, ListingImage, Wishlist, Message, Review, Lead,
    ListingReport, PropertySubmission, Reward, Notification,
    RewardWallet, RewardTransaction, WithdrawalRequest, RewardHistory,
    PaymentHistory, AdminRewardLog, SearchTrend, BlogCategory, BlogPost, City, Area
)

def api_require_login(view_func):
    """Decorator to ensure requests are authenticated via Supabase middleware."""
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required. Please login."}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

def api_require_staff(view_func):
    """Decorator to ensure requests are authenticated as staff/superuser."""
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required. Please login."}, status=401)
        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({"error": "Unauthorized. Staff/Superuser privilege required."}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def serialize_listing(request, listing):
    image_url = request.build_absolute_uri(listing.image.url) if listing.image else ""
    return {
        "id": listing.id,
        "title": listing.title,
        "location": listing.location,
        "price": float(listing.price),
        "deposit": float(listing.deposit),
        "type": listing.type,
        "available_from": listing.available_from,
        "food_preference": listing.food_preference,
        "curfew": listing.curfew,
        "visitors": listing.visitors,
        "landmark": listing.landmark,
        "nearby_food_options": listing.nearby_food_options,
        "description": listing.description,
        "facilities": [f.strip() for f in listing.facilities.split(",") if f.strip()],
        "image": image_url,
        "address": listing.address,
        "exact_location": listing.exact_location,
        "latitude": float(listing.latitude) if listing.latitude else None,
        "longitude": float(listing.longitude) if listing.longitude else None,
        "google_place_id": listing.google_place_id,
        "phone": listing.phone,
        "is_sold": listing.is_sold,
        "is_verified": listing.is_verified,
        "verification_status": listing.verification_status,
        "views_count": listing.views_count,
        "whatsapp_clicks_count": listing.whatsapp_clicks_count,
        "call_clicks_count": listing.call_clicks_count,
        "owner": {
            "id": listing.owner.id,
            "username": listing.owner.username,
            "first_name": listing.owner.first_name,
            "last_name": listing.owner.last_name,
            "phone": getattr(listing.owner.userprofile, 'phone_number', '') if hasattr(listing.owner, 'userprofile') else ''
        },
        "city": {"id": listing.city.id, "name": listing.city.name, "slug": listing.city.slug} if listing.city else None,
        "area": {"id": listing.area.id, "name": listing.area.name, "slug": listing.area.slug} if listing.area else None,
        "slug": listing.slug,
        "created_at": listing.created_at.isoformat()
    }

def serialize_review(review):
    return {
        "id": review.id,
        "user": {
            "id": review.user.id,
            "username": review.user.username,
            "first_name": review.user.first_name
        },
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat()
    }

@csrf_exempt
def get_cities_areas(request):
    cities = City.objects.filter(is_active=True).prefetch_related('areas')
    data = []
    for city in cities:
        data.append({
            "id": city.id,
            "name": city.name,
            "slug": city.slug,
            "state": city.state,
            "areas": [{"id": a.id, "name": a.name, "slug": a.slug} for a in city.areas.filter(is_active=True)]
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def get_listings(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        city_slug = request.GET.get('city', '')
        area_slug = request.GET.get('area', '')
        type_val = request.GET.get('type', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        gender = request.GET.get('gender', '')
        furnishing = request.GET.get('furnishing', '')
        
        listings = Listing.objects.filter(is_sold=False).select_related('city', 'area', 'owner', 'owner__userprofile')
        
        if query:
            listings = listings.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )
            # Track trends
            trend, created = SearchTrend.objects.get_or_create(query=query.lower(), city_slug=city_slug or None)
            if not created:
                trend.count += 1
                trend.save()
                
        if city_slug:
            listings = listings.filter(city__slug=city_slug)
        if area_slug:
            listings = listings.filter(area__slug=area_slug)
        if type_val:
            listings = listings.filter(type=type_val)
        if min_price:
            listings = listings.filter(price__gte=Decimal(min_price))
        if max_price:
            listings = listings.filter(price__lte=Decimal(max_price))
        if gender:
            listings = listings.filter(target_gender=gender)
        if furnishing:
            listings = listings.filter(furnishing=furnishing)
            
        listings = listings.order_by('-created_at')
        
        return JsonResponse([serialize_listing(request, l) for l in listings], safe=False)

    elif request.method == 'POST':
        # Post Property (Requires auth)
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({"error": "Auth required"}, status=401)
            
        try:
            # Handle both JSON and multipart form data
            if request.content_type == 'application/json':
                body = json.loads(request.body)
            else:
                body = request.POST
                
            city_id = body.get('city')
            area_id = body.get('area')
            city_obj = City.objects.filter(id=city_id).first() if city_id else None
            area_obj = Area.objects.filter(id=area_id).first() if area_id else None
            
            listing = Listing.objects.create(
                title=body.get('title'),
                location=body.get('location', 'Vijayanagar'),
                price=Decimal(str(body.get('price'))),
                deposit=Decimal(str(body.get('deposit', 0))),
                type=body.get('type'),
                available_from=body.get('available_from', 'Immediately'),
                food_preference=body.get('food_preference', 'Any'),
                curfew=body.get('curfew', 'No Curfew'),
                visitors=body.get('visitors', 'Allowed'),
                landmark=body.get('landmark', ''),
                nearby_food_options=body.get('nearby_food_options', ''),
                description=body.get('description', ''),
                facilities=body.get('facilities', 'WiFi'),
                address=body.get('address', ''),
                exact_location=body.get('exact_location', ''),
                latitude=Decimal(str(body.get('latitude'))) if body.get('latitude') else None,
                longitude=Decimal(str(body.get('longitude'))) if body.get('longitude') else None,
                phone=body.get('phone', ''),
                owner=request.user,
                city=city_obj,
                area=area_obj,
                image=request.FILES.get('image') if 'image' in request.FILES else None
            )
            
            # Save extra gallery images if any
            if 'images' in request.FILES:
                for img in request.FILES.getlist('images'):
                    ListingImage.objects.create(listing=listing, image=img)
                    
            return JsonResponse({"success": True, "id": listing.id, "slug": listing.slug})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_listing_detail(request, listing_id):
    listing = get_object_or_404(Listing.objects.select_related('city', 'area', 'owner', 'owner__userprofile'), id=listing_id)
    
    # Increment views
    Listing.objects.filter(id=listing_id).update(views_count=listing.views_count + 1)
    
    # Gather gallery
    gallery = [request.build_absolute_uri(img.image.url) for img in listing.images.all()]
    # Gather reviews
    reviews = [serialize_review(r) for r in listing.reviews.all().select_related('user')]
    
    data = serialize_listing(request, listing)
    data["gallery"] = gallery
    data["reviews"] = reviews
    
    return JsonResponse(data)

@csrf_exempt
@api_require_login
def toggle_wishlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        wishlist_item.delete()
        saved = False
    else:
        saved = True
    return JsonResponse({"status": "success", "saved": saved})

@csrf_exempt
@api_require_login
def get_wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__city', 'listing__area', 'listing__owner')
    listings = [serialize_listing(request, item.listing) for item in items]
    return JsonResponse(listings, safe=False)

@csrf_exempt
@api_require_login
def get_profile(request):
    user = request.user
    profile = getattr(user, 'userprofile', None)
    wallet = RewardWallet.get_or_create_wallet(user)
    
    if request.method == 'GET':
        submissions = PropertySubmission.objects.filter(submitter=user).select_related('city')
        notifications = Notification.objects.filter(user=user)
        reward_history = RewardHistory.objects.filter(user=user).order_by('-created_date')
        withdrawal_history = WithdrawalRequest.objects.filter(user=user).order_by('-requested_date')
        
        subs_data = []
        for s in submissions:
            subs_data.append({
                "id": s.id,
                "owner_name": s.owner_name,
                "owner_mobile": s.owner_mobile,
                "property_type": s.property_type,
                "property_address": s.property_address,
                "city": s.city.name if s.city else "Unknown",
                "status": s.status,
                "created_at": s.created_at.isoformat()
            })
            
        notifs_data = []
        for n in notifications:
            notifs_data.append({
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            })
            
        rewards_data = []
        for r in reward_history:
            rewards_data.append({
                "id": r.id,
                "property_title": r.property_title,
                "reward_amount": float(r.reward_amount),
                "status": r.status,
                "created_date": r.created_date.isoformat()
            })
            
        withdraws_data = []
        for w in withdrawal_history:
            withdraws_data.append({
                "id": w.id,
                "amount": float(w.amount),
                "upi_id": w.upi_id,
                "status": w.status,
                "requested_date": w.requested_date.isoformat(),
                "paid_date": w.paid_date.isoformat() if w.paid_date else None,
                "transaction_id": w.transaction_id,
                "admin_notes": w.admin_notes
            })
            
        return JsonResponse({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": profile.phone_number if profile else "",
            "wallet": {
                "available_balance": float(wallet.available_balance),
                "total_earned": float(wallet.total_earned),
                "withdrawn_amount": float(wallet.withdrawn_amount),
                "upi_id": wallet.upi_id
            },
            "submissions": subs_data,
            "notifications": notifs_data,
            "rewards": rewards_data,
            "withdrawals": withdraws_data
        })
        
    elif request.method == 'POST':
        # Update Profile
        try:
            body = json.loads(request.body)
            user.first_name = body.get('first_name', user.first_name)
            user.last_name = body.get('last_name', user.last_name)
            user.save()
            
            phone = body.get('phone', '').strip() or None
            if phone and profile:
                # Unique constraint check
                dup = UserProfile.objects.filter(phone_number=phone).exclude(user=user).first()
                if dup:
                    return JsonResponse({"error": "Phone number is already registered to another account."}, status=400)
                profile.phone_number = phone
                profile.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@api_require_login
def request_withdrawal(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            amount_val = body.get('amount')
            upi_id = body.get('upi_id', '').strip()
            
            if not amount_val or not upi_id:
                return JsonResponse({"error": "Amount and UPI ID are required."}, status=400)
                
            amount = Decimal(str(amount_val))
            if amount <= 0:
                return JsonResponse({"error": "Invalid withdrawal amount."}, status=400)
                
            wallet = RewardWallet.get_or_create_wallet(request.user)
            available_balance = Decimal(str(wallet.available_balance))
            
            if available_balance < amount:
                return JsonResponse({"error": "Insufficient wallet balance."}, status=400)
                
            # Perform debit
            wallet.available_balance = available_balance - amount
            wallet.upi_id = upi_id
            wallet.save()
            
            req = WithdrawalRequest.objects.create(
                user=request.user,
                amount=amount,
                upi_id=upi_id,
                status='Pending'
            )
            
            RewardTransaction.objects.create(
                wallet=wallet,
                transaction_type='Debit',
                amount=amount,
                description=f"Withdrawal request (Req ID: {req.id})"
            )
            
            Notification.objects.create(
                user=request.user,
                title="Withdrawal Requested",
                message=f"Request of ₹{amount} to UPI {upi_id} has been submitted successfully."
            )
            
            return JsonResponse({"success": True, "id": req.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@api_require_login
def refer_property(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                body = json.loads(request.body)
            else:
                body = request.POST
                
            city_id = body.get('city')
            city_obj = City.objects.filter(id=city_id).first() if city_id else None
            
            photo = request.FILES.get('photo') if 'photo' in request.FILES else None
            
            submission = PropertySubmission.objects.create(
                submitter=request.user,
                submitted_by_name=body.get('submitted_by_name'),
                submitted_by_mobile=body.get('submitted_by_mobile'),
                owner_name=body.get('owner_name'),
                owner_mobile=body.get('owner_mobile'),
                property_type=body.get('property_type'),
                property_address=body.get('property_address'),
                city=city_obj,
                photo=photo,
                notes=body.get('notes', ''),
                permission_confirmed=bool(body.get('permission_confirmed', False))
            )
            
            return JsonResponse({"success": True, "id": submission.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@api_require_login
def report_listing(request, listing_id):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            reason = body.get('reason')
            details = body.get('details', '')
            
            listing = get_object_or_404(Listing, id=listing_id)
            if listing.owner == request.user:
                return JsonResponse({"error": "Cannot report your own listing."}, status=400)
                
            report, created = ListingReport.objects.get_or_create(
                listing=listing,
                reporter=request.user,
                defaults={"reason": reason, "details": details}
            )
            
            if not created:
                return JsonResponse({"error": "You have already reported this listing."}, status=400)
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def track_click(request, listing_id):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            lead_type = body.get('type') # Call or WhatsApp
            
            listing = get_object_or_404(Listing, id=listing_id)
            
            if lead_type == 'WhatsApp':
                Listing.objects.filter(id=listing_id).update(whatsapp_clicks_count=listing.whatsapp_clicks_count + 1)
            elif lead_type == 'Call':
                Listing.objects.filter(id=listing_id).update(call_clicks_count=listing.call_clicks_count + 1)
            else:
                return JsonResponse({"error": "Invalid lead type."}, status=400)
                
            # Log Lead if authenticated
            if request.user and request.user.is_authenticated:
                Lead.objects.create(
                    listing=listing,
                    tenant=request.user,
                    name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    email=request.user.email,
                    phone=getattr(request.user.userprofile, 'phone_number', '') if hasattr(request.user, 'userprofile') else '',
                    lead_type=lead_type
                )
            else:
                # Anonymous lead entry
                Lead.objects.create(
                    listing=listing,
                    name=body.get('name', 'Anonymous Finder'),
                    email=body.get('email', 'anon@roomnest.online'),
                    phone=body.get('phone', ''),
                    lead_type=lead_type
                )
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@api_require_login
def get_owner_dashboard(request):
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    
    total_views = listings.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_whatsapp = listings.aggregate(Sum('whatsapp_clicks_count'))['whatsapp_clicks_count__sum'] or 0
    total_calls = listings.aggregate(Sum('call_clicks_count'))['call_clicks_count__sum'] or 0
    
    leads = Lead.objects.filter(listing__owner=request.user).select_related('listing').order_by('-created_at')
    
    leads_data = []
    for l in leads:
        leads_data.append({
            "id": l.id,
            "listing_title": l.listing.title,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "lead_type": l.lead_type,
            "created_at": l.created_at.isoformat()
        })
        
    return JsonResponse({
        "stats": {
            "properties_count": listings.count(),
            "total_views": total_views,
            "total_whatsapp": total_whatsapp,
            "total_calls": total_calls
        },
        "listings": [serialize_listing(request, l) for l in listings],
        "leads": leads_data
    })

@csrf_exempt
@api_require_login
def toggle_sold_status(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    listing.is_sold = not listing.is_sold
    listing.save()
    return JsonResponse({"success": True, "is_sold": listing.is_sold})

@csrf_exempt
@api_require_staff
def get_admin_dashboard(request):
    users_count = User.objects.count()
    listings_count = Listing.objects.count()
    
    submissions = PropertySubmission.objects.filter(status__in=['Pending', 'Under Verification']).select_related('submitter', 'city')
    withdrawals = WithdrawalRequest.objects.filter(status='Pending').select_related('user')
    
    subs_data = []
    for s in submissions:
        photo_url = request.build_absolute_uri(s.photo.url) if s.photo else ""
        subs_data.append({
            "id": s.id,
            "submitter": s.submitter.username,
            "submitted_by_name": s.submitted_by_name,
            "owner_name": s.owner_name,
            "owner_mobile": s.owner_mobile,
            "property_type": s.property_type,
            "property_address": s.property_address,
            "city": s.city.name if s.city else "Unknown",
            "photo": photo_url,
            "notes": s.notes,
            "created_at": s.created_at.isoformat()
        })
        
    withdraws_data = []
    for w in withdrawals:
        withdraws_data.append({
            "id": w.id,
            "username": w.user.username,
            "amount": float(w.amount),
            "upi_id": w.upi_id,
            "requested_date": w.requested_date.isoformat()
        })
        
    return JsonResponse({
        "stats": {
            "users_count": users_count,
            "listings_count": listings_count,
            "pending_referrals": len(subs_data),
            "pending_withdrawals": len(withdraws_data)
        },
        "submissions": subs_data,
        "withdrawals": withdraws_data
    })

@csrf_exempt
@api_require_staff
def verify_property(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            sub_id = body.get('submission_id')
            action = body.get('action') # Approve, Reject, Publish
            notes = body.get('notes', '')
            
            submission = get_object_or_404(PropertySubmission, id=sub_id)
            
            if action == 'Approve':
                submission.status = 'Approved'
                submission.notes = f"{submission.notes}\nApproved Notes: {notes}".strip()
                submission.save()
                
                Notification.objects.create(
                    user=submission.submitter,
                    title="Property Referral Approved",
                    message=f"Referral for {submission.property_type} in {submission.city.name if submission.city else 'Unknown'} has been approved."
                )
                
            elif action == 'Reject':
                submission.status = 'Rejected'
                submission.notes = f"{submission.notes}\nRejected: {notes}".strip()
                submission.save()
                
                Notification.objects.create(
                    user=submission.submitter,
                    title="Property Referral Rejected",
                    message=f"Your property referral has been rejected: {notes}"
                )
                
            elif action == 'Publish':
                if submission.status != 'Approved':
                    return JsonResponse({"error": "Referral must be Approved before publishing"}, status=400)
                    
                # Create Listing
                owner_profile = UserProfile.objects.filter(phone_number=submission.owner_mobile).first()
                owner_user = owner_profile.user if owner_profile else submission.submitter
                
                area_obj = submission.city.areas.filter(is_active=True).first() if submission.city else None
                
                listing = Listing.objects.create(
                    title=f"{submission.property_type} in {submission.city.name if submission.city else 'Mysore'}",
                    location=area_obj.name[:50] if area_obj else "Vijayanagar",
                    city=submission.city,
                    area=area_obj,
                    price=12000.00,
                    type="Single Room" if "room" in submission.property_type.lower() else "2BHK",
                    description=f"Verified property. Referred by {submission.submitted_by_name}. Contact: {submission.owner_name}",
                    facilities="WiFi, Parking",
                    address=submission.property_address,
                    phone=submission.owner_mobile,
                    owner=owner_user,
                    image=submission.photo,
                    is_verified=True,
                    verification_status='Verified'
                )
                
                submission.status = 'Published'
                submission.save()
                
                # Reward Referrer ₹50
                RewardHistory.objects.create(
                    user=submission.submitter,
                    listing=listing,
                    property_submission=submission,
                    property_title=listing.title,
                    city=submission.city.name if submission.city else "Mysore",
                    reward_amount=Decimal('50.00'),
                    status='Available',
                    approval_date=timezone.now()
                )
                
                wallet = RewardWallet.get_or_create_wallet(submission.submitter)
                wallet.available_balance = Decimal(str(wallet.available_balance)) + Decimal('50.00')
                wallet.total_earned = Decimal(str(wallet.total_earned)) + Decimal('50.00')
                wallet.save()
                
                RewardTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='Credit',
                    amount=Decimal('50.00'),
                    description=f"Reward for referral #{submission.id} published."
                )
                
                Notification.objects.create(
                    user=submission.submitter,
                    title="Reward Added",
                    message="₹50 reward has been added to your wallet available balance for published referral."
                )
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@api_require_staff
def verify_withdrawal(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            req_id = body.get('withdrawal_id')
            action = body.get('action') # Pay, Reject
            notes = body.get('notes', '')
            utr = body.get('utr', '') # Required if Pay
            
            req = get_object_or_404(WithdrawalRequest, id=req_id)
            if req.status in ['Paid', 'Rejected']:
                return JsonResponse({"error": "Request already finalized"}, status=400)
                
            if action == 'Pay':
                if not utr:
                    return JsonResponse({"error": "UTR Transaction Ref is required for Payment"}, status=400)
                    
                req.status = 'Paid'
                req.paid_date = timezone.now()
                req.transaction_id = utr
                req.admin_notes = notes
                req.save()
                
                wallet = RewardWallet.get_or_create_wallet(req.user)
                wallet.withdrawn_amount = Decimal(str(wallet.withdrawn_amount)) + req.amount
                wallet.save()
                
                # Payment History
                PaymentHistory.objects.create(
                    withdrawal_request=req,
                    user=req.user,
                    amount=req.amount,
                    upi_id=req.upi_id,
                    payment_method='UPI',
                    transaction_reference=utr,
                    paid_date=timezone.now(),
                    admin_notes=notes
                )
                
                # Update individual rewards status
                amount_to_cover = req.amount
                rewards = RewardHistory.objects.filter(user=req.user, status='Available').order_by('created_date')
                for r in rewards:
                    if amount_to_cover <= 0:
                        break
                    r.status = 'Paid'
                    r.payment_date = timezone.now()
                    r.save()
                    amount_to_cover -= r.reward_amount
                    
                Notification.objects.create(
                    user=req.user,
                    title="Payment Completed",
                    message=f"Withdrawal of ₹{req.amount} has been paid. UTR: {utr}"
                )
                
            elif action == 'Reject':
                req.status = 'Rejected'
                req.admin_notes = f"Rejected: {notes}"
                req.save()
                
                # Refund wallet balance
                wallet = RewardWallet.get_or_create_wallet(req.user)
                wallet.available_balance = Decimal(str(wallet.available_balance)) + req.amount
                wallet.save()
                
                RewardTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='Credit',
                    amount=req.amount,
                    description=f"Refund for rejected withdrawal request #{req.id}"
                )
                
                Notification.objects.create(
                    user=req.user,
                    title="Withdrawal Rejected",
                    message=f"Withdrawal request of ₹{req.amount} was rejected. Amount refunded to balance."
                )
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_blogs(request):
    categories = BlogCategory.objects.all()
    posts = BlogPost.objects.filter(is_published=True).select_related('category').order_by('-created_at')
    
    cat_slug = request.GET.get('category')
    if cat_slug:
        posts = posts.filter(category__slug=cat_slug)
        
    posts_data = []
    for p in posts:
        image = request.build_absolute_uri(p.featured_image.url) if p.featured_image else ""
        posts_data.append({
            "title": p.title,
            "slug": p.slug,
            "category": p.category.name if p.category else None,
            "image": image,
            "summary": p.summary,
            "created_at": p.created_at.isoformat()
        })
        
    return JsonResponse({
        "categories": [{"name": c.name, "slug": c.slug} for c in categories],
        "posts": posts_data
    })

@csrf_exempt
def get_blog_detail(request, slug):
    post = get_object_or_404(BlogPost.objects.select_related('category').prefetch_related('related_listings__city', 'related_listings__area'), slug=slug, is_published=True)
    
    image = request.build_absolute_uri(post.featured_image.url) if post.featured_image else ""
    
    related_posts = BlogPost.objects.filter(is_published=True, category=post.category).exclude(id=post.id).order_by('-created_at')[:3]
    related_posts_data = []
    for rp in related_posts:
        rp_image = request.build_absolute_uri(rp.featured_image.url) if rp.featured_image else ""
        related_posts_data.append({
            "title": rp.title,
            "slug": rp.slug,
            "image": rp_image,
            "summary": rp.summary
        })
        
    return JsonResponse({
        "title": post.title,
        "slug": post.slug,
        "category": post.category.name if post.category else None,
        "image": image,
        "content": post.content,
        "summary": post.summary,
        "seo_title": post.seo_title or post.title,
        "seo_description": post.seo_description or post.summary,
        "created_at": post.created_at.isoformat(),
        "related_listings": [serialize_listing(request, l) for l in post.related_listings.filter(is_sold=False)[:3]],
        "related_posts": related_posts_data
    })
