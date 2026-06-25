from django.db.models import Count, Q
from .models import Message, City

def unread_messages(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}

def active_cities(request):
    cities = City.objects.filter(is_active=True).annotate(
        property_count=Count('listings', filter=Q(listings__is_sold=False))
    ).prefetch_related('areas').order_by('name')
    return {'active_cities': cities}


