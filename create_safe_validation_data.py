import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import Listing, City, Area

User = get_user_model()


def ensure_validation_data():
    city, _ = City.objects.get_or_create(name='Mysore', slug='mysore', defaults={'is_active': True})
    area, _ = Area.objects.get_or_create(city=city, name='Gokulam', slug='gokulam', defaults={'is_active': True})

    for index in range(1, 6):
        username = f'validation_user_{index}'
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@roomnest.local'})
        if created:
            user.set_password('SafePass123!')
            user.save()

    owner_usernames = [f'validation_user_{index}' for index in range(1, 6)]
    owners = list(User.objects.filter(username__in=owner_usernames))
    for owner in owners:
        Listing.objects.get_or_create(
            title=f'Validation Listing {owner.username}',
            defaults={
                'location': 'Gokulam',
                'price': 8000 + len(owner.username),
                'deposit': 1000,
                'type': '1BHK',
                'owner': owner,
                'city': city,
                'area': area,
                'description': 'Validation data for deployment safety testing.',
                'facilities': 'WiFi, Parking',
                'address': 'Validation Address',
                'phone': '9876543210',
            },
        )

    print('Validation data ensured safely.')


if __name__ == '__main__':
    ensure_validation_data()
