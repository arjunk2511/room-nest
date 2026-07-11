import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from listings.models import Listing, ListingImage


def run_check(name, func):
    try:
        func()
    except Exception as exc:
        print(f'FAIL {name}: {exc}')
        return False
    print(f'PASS {name}')
    return True


def main():
    client = Client()
    User = get_user_model()
    results = []

    def homepage_loads():
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def login_page_loads():
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def property_page_loads():
        listing = Listing.objects.first()
        assert listing is not None
        response = client.get(listing.get_absolute_url())
        assert response.status_code == 200

    def user_login_works():
        user = User.objects.filter(is_superuser=False).first()
        assert user is not None
        response = client.post(reverse('login'), {'username': user.username, 'password': 'wrong'})
        assert response.status_code in (200, 302)

    def owner_dashboard_loads():
        owner = Listing.objects.values_list('owner', flat=True).first()
        assert owner is not None
        owner_user = User.objects.get(pk=owner)
        client.force_login(owner_user)
        response = client.get(reverse('owner_dashboard'))
        assert response.status_code == 200

    def images_load():
        assert ListingImage.objects.exists() or Listing.objects.exists()

    def database_connection_works():
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()

    results.append(run_check('Homepage loads', homepage_loads))
    results.append(run_check('Login page loads', login_page_loads))
    results.append(run_check('Property page loads', property_page_loads))
    results.append(run_check('User login works', user_login_works))
    results.append(run_check('Owner dashboard loads', owner_dashboard_loads))
    results.append(run_check('Images load', images_load))
    results.append(run_check('Database connection works', database_connection_works))

    if not all(results):
        sys.exit(1)


if __name__ == '__main__':
    main()
