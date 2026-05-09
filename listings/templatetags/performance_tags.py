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
