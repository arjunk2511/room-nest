import os
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.test import Client
from listings.models import Listing, Reward
from subscriptions.models import Subscription
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Automatically runs a read-only post-deployment safety check to verify database and app integrity.'

    def handle(self, *args, **options):
        self.stdout.write("====================================================")
        self.stdout.write("🔍 RoomNest Post-Deployment Verification Checklist")
        self.stdout.write("====================================================\n")

        # Determine if running in staging or production
        is_prod = getattr(settings, 'DJANGO_ENV', 'development') in ['production', 'staging']

        checklist = {
            "User Accounts": False,
            "Owner Accounts": False,
            "Property Listings": False,
            "Property Images": False,
            "Rewards": False,
            "Subscriptions": False,
            "Search": False,
            "Login": False,
            "Maps": False,
            "Dashboards": False,
        }

        details = []

        # 1. User Accounts Check
        try:
            user_count = User.objects.filter(is_active=True).count()
            if user_count > 0:
                checklist["User Accounts"] = True
                details.append(f"✓ User Accounts: Found {user_count} active user(s) in database.")
            else:
                checklist["User Accounts"] = True
                details.append("✓ User Accounts: No active users found in database (acceptable for an initial empty deployment).")
        except Exception as e:
            details.append(f"✗ User Accounts error: {e}")

        # 2. Owner Accounts Check
        try:
            profile_count = UserProfile.objects.count()
            if profile_count > 0:
                checklist["Owner Accounts"] = True
                details.append(f"✓ Owner Accounts: Found {profile_count} user profile(s) registered.")
            else:
                checklist["Owner Accounts"] = True
                details.append("✓ Owner Accounts: No user profiles found in database (acceptable for an initial deployment).")
        except Exception as e:
            details.append(f"✗ Owner Accounts error: {e}")

        # 3. Property Listings Check
        try:
            listing_count = Listing.objects.count()
            if listing_count > 0:
                checklist["Property Listings"] = True
                details.append(f"✓ Property Listings: Found {listing_count} total property listings.")
            else:
                checklist["Property Listings"] = True
                details.append("✓ Property Listings: No property listings found in database (acceptable for an initial deployment).")
        except Exception as e:
            details.append(f"✗ Property Listings error: {e}")

        # 4. Property Images Check
        try:
            listings_with_img = Listing.objects.exclude(image='')
            if listings_with_img.exists():
                broken_count = 0
                total_checked = 0
                for listing in listings_with_img[:5]:  # Check first 5 to keep it fast
                    total_checked += 1
                    img_url = listing.image.url
                    if img_url.startswith('http'):
                        try:
                            r = requests.head(img_url, timeout=5)
                            if r.status_code >= 400:
                                broken_count += 1
                        except Exception:
                            broken_count += 1
                    else:
                        # Local file system check
                        media_path = img_url
                        if media_path.startswith(settings.MEDIA_URL):
                            media_path = media_path[len(settings.MEDIA_URL):]
                        full_path = os.path.join(settings.MEDIA_ROOT, media_path)
                        if not os.path.exists(full_path):
                            broken_count += 1
                
                if broken_count == 0:
                    checklist["Property Images"] = True
                    details.append(f"✓ Property Images: Checked {total_checked} listing images. All resolved successfully.")
                else:
                    details.append(f"✗ Property Images: Found {broken_count} broken image URLs out of {total_checked} checked.")
            else:
                checklist["Property Images"] = True  # Pass if no listings with images exist yet
                details.append("✓ Property Images: No property listings with uploaded images exist to check.")
        except Exception as e:
            details.append(f"✗ Property Images error: {e}")

        # 5. Rewards Check
        try:
            reward_count = Reward.objects.count()
            checklist["Rewards"] = True
            details.append(f"✓ Rewards: Reward database table is queryable. Found {reward_count} reward(s).")
        except Exception as e:
            details.append(f"✗ Rewards table error: {e}")

        # 6. Subscriptions Check
        try:
            sub_count = Subscription.objects.count()
            checklist["Subscriptions"] = True
            details.append(f"✓ Subscriptions: Subscription database table is queryable. Found {sub_count} subscription(s).")
        except Exception as e:
            details.append(f"✗ Subscriptions table error: {e}")

        # 7. Search Functionality Check
        try:
            client = Client()
            response = client.get('/search/', {'price': '20000'})
            if response.status_code == 200:
                checklist["Search"] = True
                details.append("✓ Search: Search endpoint returned HTTP 200 successfully.")
            else:
                details.append(f"✗ Search: Search endpoint returned HTTP {response.status_code}.")
        except Exception as e:
            details.append(f"✗ Search view error: {e}")

        # 8. Login Endpoint Check
        try:
            client = Client()
            response = client.get('/accounts/login/')
            if response.status_code == 200:
                checklist["Login"] = True
                details.append("✓ Login: Login page loaded with HTTP 200 successfully.")
            else:
                details.append(f"✗ Login: Login page loaded with HTTP {response.status_code}.")
        except Exception as e:
            details.append(f"✗ Login view error: {e}")

        # 9. Maps Proximity Proximity Check
        try:
            listing = Listing.objects.first()
            if listing:
                client = Client()
                response = client.get(f'/api/listing/{listing.id}/landmarks/')
                if response.status_code == 200:
                    checklist["Maps"] = True
                    details.append("✓ Maps: Landmarks/Proximity API returned HTTP 200 successfully.")
                else:
                    details.append(f"✗ Maps: Proximity API returned HTTP {response.status_code}.")
            else:
                checklist["Maps"] = True  # Pass if no listings exist yet
                details.append("✓ Maps: No property listings exist. Proximity maps validation skipped.")
        except Exception as e:
            details.append(f"✗ Maps API error: {e}")

        # 10. Dashboards Check
        try:
            test_user = User.objects.first()
            if test_user:
                client = Client()
                client.force_login(test_user)
                
                # Check owner dashboard
                owner_response = client.get('/owner/dashboard/')
                # Check tenant dashboard
                tenant_response = client.get('/tenant/dashboard/')
                
                # Check admin dashboard if staff/superuser
                admin_response_ok = True
                if test_user.is_superuser or test_user.is_staff:
                    admin_response = client.get('/admin-dashboard/')
                    if admin_response.status_code != 200:
                        admin_response_ok = False
                
                if owner_response.status_code == 200 and tenant_response.status_code == 200 and admin_response_ok:
                    checklist["Dashboards"] = True
                    details.append("✓ Dashboards: Dashboard views rendered with HTTP 200 successfully.")
                else:
                    details.append(f"✗ Dashboards: Owner status {owner_response.status_code}, Tenant status {tenant_response.status_code}, Admin pass {admin_response_ok}.")
            else:
                checklist["Dashboards"] = True  # Pass if no users exist yet
                details.append("✓ Dashboards: No users exist in database. Dashboard validation skipped.")
        except Exception as e:
            details.append(f"✗ Dashboards view error: {e}")

        # Output results
        self.stdout.write("\n----------------- Detail Logs -----------------")
        for log in details:
            if log.startswith("✓"):
                self.stdout.write(self.style.SUCCESS(log))
            else:
                self.stdout.write(self.style.ERROR(log))

        self.stdout.write("\n----------------- Summary Checklist -----------------")
        all_passed = True
        for name, passed in checklist.items():
            if passed:
                self.stdout.write(self.style.SUCCESS(f"[PASS] {name}"))
            else:
                all_passed = False
                self.stdout.write(self.style.ERROR(f"[FAIL] {name}"))

        self.stdout.write("\n====================================================")
        if all_passed:
            self.stdout.write(self.style.SUCCESS("🎉 All post-deployment verification checks passed successfully!"))
        else:
            self.stdout.write(self.style.ERROR("❌ One or more verification checks failed. Review details above."))
            raise SystemExit(1)
        self.stdout.write("====================================================")
