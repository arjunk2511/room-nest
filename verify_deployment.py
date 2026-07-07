import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
try:
    django.setup()
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Django: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.conf import settings
from listings.models import Listing, ListingImage, City, Area

def main():
    print("====================================================")
    print("🚀 Running Post-Deployment Verification Protocol")
    print("====================================================\n")
    
    User = get_user_model()
    client = Client()
    
    is_prod = getattr(settings, 'IS_PRODUCTION', False)
    temp_owner = None
    temp_listing = None
    temp_city = None
    temp_area = None

    # 1. Verify User Count
    user_count = User.objects.count()
    print(f"👥 Total Users in database: {user_count}")
    if user_count == 0:
        print("❌ Verification Failed: 0 users found in database.")
        sys.exit(1)

    # 2. Check if properties exist. If not in dev, seed a temp one.
    property_count = Listing.objects.count()
    if property_count == 0:
        if is_prod:
            print("❌ Verification Failed: 0 properties found in production database (unexpected empty state).")
            sys.exit(1)
        else:
            print("ℹ️ Development Environment: Seeding temporary property and owner for local verification...")
            # Create a temporary owner
            temp_owner = User.objects.create_user(
                username="temp_owner_verifier",
                email="temp_owner@roomnest.online",
                password="TempPassword123!"
            )
            # Fetch/create temp City & Area
            temp_city, _ = City.objects.get_or_create(name="Mysore", slug="mysore", is_active=True)
            temp_area, _ = Area.objects.get_or_create(city=temp_city, name="Gokulam", slug="gokulam", is_active=True)
            
            # Create a temp Listing
            temp_listing = Listing.objects.create(
                title="Temporary Verification Listing",
                location="Gokulam",
                city=temp_city,
                area=temp_area,
                price=10000.00,
                deposit=20000.00,
                type="1BHK",
                owner=temp_owner,
                listing_purpose="Rent",
                phone="9876543210"
            )
            print("✅ Seeding complete.")
            property_count = 1

    # 3. Verify Owner Count
    owner_count = Listing.objects.values('owner').distinct().count()
    print(f"🏡 Total Property Owners: {owner_count}")

    # 4. Verify Property Count
    print(f"🏢 Total Property Listings: {property_count}")

    # 5. Verify Images structure/fields
    image_count = ListingImage.objects.count()
    print(f"🖼️ Total Gallery Images: {image_count}")
    for listing in Listing.objects.all()[:10]:
        if listing.image:
            if not listing.image.name:
                print(f"⚠️ Warning: Listing {listing.id} ('{listing.title}') has main image field but name is empty.")
        else:
            print(f"ℹ️ Listing {listing.id} has no main image.")

    try:
        # 6. Verify Login Flow
        print("\n🔐 Testing Login Form Flow...")
        test_username = "deploy_verifier_temp"
        test_password = "TemporaryVerifierPassword123!"
        test_email = "verifier@roomnest.online"
        
        # Remove existing temp verifier if any
        User.objects.filter(username=test_username).delete()
        test_user = User.objects.create_user(username=test_username, email=test_email, password=test_password)
        
        try:
            login_url = reverse('login')
            response = client.get(login_url)
            if response.status_code != 200:
                print(f"❌ Verification Failed: Login page returned HTTP {response.status_code}")
                sys.exit(1)
                
            response = client.post(login_url, {'username': test_username, 'password': test_password})
            if response.status_code not in [200, 302]:
                print(f"❌ Verification Failed: Login POST returned HTTP {response.status_code}")
                sys.exit(1)
            print("✅ Login form flow verified successfully.")
        finally:
            test_user.delete()

        # 7. Verify Owner Dashboard
        print("\n📊 Testing Owner Dashboard...")
        first_owner_listing = Listing.objects.first()
        if first_owner_listing:
            owner_user = first_owner_listing.owner
            client.force_login(owner_user)
            dashboard_url = reverse('owner_dashboard')
            response = client.get(dashboard_url)
            if response.status_code != 200:
                print(f"❌ Verification Failed: Owner Dashboard returned HTTP {response.status_code} for user {owner_user.username}")
                sys.exit(1)
            print(f"✅ Owner Dashboard loads successfully (User: {owner_user.username}).")
        else:
            print("⚠️ No listing owners found. Skipping Owner Dashboard verification.")

        # 8. Verify Admin Dashboard
        print("\n🛡️ Testing Admin Dashboard...")
        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
        if admin_user:
            client.force_login(admin_user)
            admin_dashboard_url = reverse('admin_dashboard')
            response = client.get(admin_dashboard_url)
            if response.status_code != 200:
                print(f"❌ Verification Failed: Admin Dashboard returned HTTP {response.status_code} for admin {admin_user.username}")
                sys.exit(1)
            if b"Operations" not in response.content and b"operations" not in response.content.lower() and b"Dashboard" not in response.content:
                print("❌ Verification Failed: Admin Dashboard content check failed.")
                sys.exit(1)
            print(f"✅ Admin Dashboard loads and renders successfully (Admin: {admin_user.username}).")
        else:
            print("❌ Verification Failed: No superuser or staff admin found in database.")
            sys.exit(1)

    finally:
        # Cleanup seeded database entities in development
        if temp_listing:
            print("\n🔄 Cleaning up temporary seeded listing and owner...")
            temp_listing.delete()
        if temp_owner:
            temp_owner.delete()

    print("\n🎉 Post-deployment verification complete. All checks passed successfully!")
    sys.exit(0)

if __name__ == '__main__':
    main()
