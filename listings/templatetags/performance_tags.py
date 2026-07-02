from django import template

register = template.Library()

@register.filter(name='optimize_image')
def optimize_image(url, arg='w_800'):
    """
    If the image is hosted on Cloudinary, automatically insert f_auto,q_auto formats
    to serve highly compressed, next-gen WebP/AVIF images instantly.
    Otherwise, returns the original URL.
    """
    if not url:
        return ''
    
    url_str = str(url)
    
    # Check if it's a Cloudinary URL
    if 'res.cloudinary.com' in url_str:
        if '/upload/' in url_str:
            # We insert quality and format settings
            # e.g., f_auto,q_auto,w_800
            transformations = f"f_auto,q_auto,{arg}"
            # Ensure we do not double-inject if already exists
            if 'f_auto' not in url_str:
                optimized_url = url_str.replace('/upload/', f'/upload/{transformations}/')
                return optimized_url
            
    return url_str

@register.filter(name='split_by_comma')
def split_by_comma(value):
    """
    Splits a comma-separated string into a list of cleaned strings.
    """
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]

@register.filter(name='format_price')
def format_price(value):
    """
    Formats decimal/int as a comma-separated currency string.
    """
    if value is None:
        return '0'
    try:
        return f"{int(float(value)):,}"
    except (ValueError, TypeError):
        return str(value)

@register.filter(name='get_listing_chips')
def get_listing_chips(listing):
    """
    Constructs a list of relevant meta chips for the listing.
    """
    chips = []
    if listing.type:
        chips.append(listing.type)
    if listing.furnishing:
        if listing.furnishing == 'Fully Furnished':
            chips.append('Furnished')
        elif listing.furnishing == 'Semi-Furnished':
            chips.append('Semi-Furn')
        else:
            chips.append(listing.furnishing)
    if listing.available_from:
        chips.append(listing.available_from)
    if listing.target_gender and listing.target_gender != 'Any':
        chips.append(listing.target_gender)
    return chips

@register.filter(name='is_new_listing')
def is_new_listing(listing):
    """
    Returns True if the listing was created in the last 3 days.
    """
    if not listing or not listing.created_at:
        return False
    from django.utils import timezone
    delta = timezone.now() - listing.created_at
    return delta.days < 3
