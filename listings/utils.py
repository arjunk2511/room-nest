import re

def clean_phone(phone_str):
    if not phone_str:
        return ""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_str)
    # Strip leading 91 or 0 if it's an Indian mobile number prefix
    if len(digits) == 12 and digits.startswith('91'):
        return digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        return digits[1:]
    return digits

def clean_address(address_str):
    if not address_str:
        return ""
    # Lowercase, remove all non-alphanumeric characters, and strip spaces
    return re.sub(r'[^a-z0-9]', '', address_str.lower())

def are_coordinates_close(lat1, lon1, lat2, lon2, tolerance=0.0001):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return False
    try:
        return abs(float(lat1) - float(lat2)) < tolerance and abs(float(lon1) - float(lon2)) < tolerance
    except (ValueError, TypeError):
        return False

def check_duplicate_property(phone, address, latitude=None, longitude=None, exclude_listing_id=None, exclude_submission_id=None):
    from .models import Listing, PropertySubmission
    
    cleaned_phone = clean_phone(phone)
    cleaned_addr = clean_address(address)
    
    # 1. Compare against Listings
    listings = Listing.objects.all()
    if exclude_listing_id:
        listings = listings.exclude(id=exclude_listing_id)
        
    for item in listings:
        if cleaned_phone and clean_phone(item.phone) == cleaned_phone:
            return True, "duplicate_phone", f"Duplicate phone number matched with active listing '{item.title}' (ID: {item.id})"
        
        if cleaned_addr and clean_address(item.address) == cleaned_addr:
            return True, "duplicate_address", f"Duplicate address matched with active listing '{item.title}' (ID: {item.id})"
            
        if are_coordinates_close(latitude, longitude, item.latitude, item.longitude):
            return True, "duplicate_coordinates", f"Duplicate GPS coordinates matched with active listing '{item.title}' (ID: {item.id})"

    # 2. Compare against active PropertySubmissions (Referrals)
    submissions = PropertySubmission.objects.all()
    if exclude_submission_id:
        submissions = submissions.exclude(id=exclude_submission_id)
        
    for item in submissions:
        # Ignore rejected referrals
        if item.status == 'Rejected':
            continue
            
        if cleaned_phone and clean_phone(item.owner_mobile) == cleaned_phone:
            return True, "duplicate_phone", f"Duplicate owner phone matched with pending/approved referral submission (ID: {item.id})"
        
        if cleaned_addr and clean_address(item.property_address) == cleaned_addr:
            return True, "duplicate_address", f"Duplicate address matched with pending/approved referral submission (ID: {item.id})"
            
    return False, None, None
