from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Listing, Lead, City, Area
from subscriptions.models import Subscription
import datetime

class RoomNestTestCase(TestCase):
    def setUp(self):
        # Create Owner
        self.owner = User.objects.create_user(username='owner', password='ownerpassword', email='owner@roomnest.online')
        
        # Create Tenant
        self.tenant = User.objects.create_user(username='tenant', password='tenantpassword', email='tenant@roomnest.online')
        
        # Create Staff Admin
        self.admin = User.objects.create_superuser(username='admin', password='adminpassword', email='admin@roomnest.online')
        
        # Create standard Listing
        self.listing = Listing.objects.create(
            title="Premium 2BHK in Gokulam",
            location="Gokulam",
            price=12000.00,
            deposit=20000.00,
            type="2BHK",
            available_from="Immediately",
            food_preference="Any",
            curfew="No Curfew",
            visitors="Allowed",
            landmark="Near Gokulam Park",
            nearby_food_options="Gokulam mess",
            description="Beautiful spacious 2BHK flat.",
            facilities="WiFi, AC, Parking",
            address="123 Gokulam Main Rd, Mysore",
            exact_location="https://maps.google.com/test",
            phone="9876543210",
            owner=self.owner,
            listing_purpose="Rent",
            furnishing="Semi-Furnished",
            target_gender="Any"
        )
        
        self.client = Client()

    def test_search_filters_and_sorting(self):
        # Test basic search query
        response = self.client.get(reverse('search'), {'location': 'Gokulam'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium 2BHK in Gokulam")
        
        # Test price filter
        response = self.client.get(reverse('search'), {'min_price': 10000, 'price': 15000})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium 2BHK in Gokulam")
        
        # Test pricing filters excluding the listing
        response = self.client.get(reverse('search'), {'price': 5000})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Premium 2BHK in Gokulam")
        
        # Test sort options
        response = self.client.get(reverse('search'), {'sort_by': 'price_asc'})
        self.assertEqual(response.status_code, 200)

    def test_lead_generation_on_whatsapp_click(self):
        # Login as tenant
        self.client.login(username='tenant', password='tenantpassword')
        
        # Track WhatsApp click POST request
        response = self.client.post(reverse('track_whatsapp', args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        
        # Verify Lead object is created
        lead_exists = Lead.objects.filter(listing=self.listing, tenant=self.tenant, lead_type='WhatsApp').exists()
        self.assertTrue(lead_exists)
        
    def test_lead_masking_access_controls(self):
        # Create a WhatsApp lead
        Lead.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            name="Tenant Seeker",
            email="tenant@roomnest.online",
            phone="9988776655",
            lead_type="WhatsApp"
        )
        
        # Login as owner (unsubscribed)
        self.client.login(username='owner', password='ownerpassword')
        
        response = self.client.get(reverse('owner_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Verify contact details are masked
        self.assertContains(response, "masked-text")
        
        # Upgrade owner to active subscription
        Subscription.objects.create(
            user=self.owner,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=90),
            transaction_id="UTR1234567890",
            payment_status="Approved",
            plan_name="90 Days Premium"
        )
        
        # Access owner dashboard again
        response = self.client.get(reverse('owner_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Verify contact details are now unmasked and visible
        self.assertContains(response, "9988776655")

    def test_property_verification_flow(self):
        self.client.login(username='owner', password='ownerpassword')
        
        # Verify listing starts as unverified
        self.assertFalse(self.listing.is_verified)
        self.assertEqual(self.listing.verification_status, 'Not Requested')
        
        # Submit verification request
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf")
        temp_file.write(b"Test validation document contents.")
        temp_file.seek(0)
        
        doc = SimpleUploadedFile(
            "doc.pdf",
            temp_file.read(),
            content_type="application/pdf"
        )
        
        response = self.client.post(
            reverse('request_verification', args=[self.listing.id]),
            {'verification_notes': 'Electricity bill document', 'verification_document': doc}
        )
        
        # Retrieve listing and check state
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.verification_status, 'Pending')
        
        # Login as Admin and approve
        self.client.login(username='admin', password='adminpassword')
        
        response = self.client.get(reverse('approve_verification', args=[self.listing.id]))
        self.assertEqual(response.status_code, 302) # Redirects back
        
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_verified)
        self.assertEqual(self.listing.verification_status, 'Verified')


class MultiCityTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='ownerpassword', email='owner@roomnest.online')
        self.client = Client()
        
        # Fetch pre-populated City and Area from migrations
        self.city = City.objects.get(slug="bengaluru")
        self.area = Area.objects.get(city=self.city, slug="whitefield")
        
        # Create Listing
        self.listing = Listing.objects.create(
            title="Premium Flat in Whitefield",
            location="Whitefield",
            city=self.city,
            area=self.area,
            price=15000.00,
            deposit=30000.00,
            type="2BHK",
            available_from="Immediately",
            owner=self.owner,
            listing_purpose="Rent"
        )

    def test_city_page_view(self):
        # Visit Bengaluru city landing page
        response = self.client.get(reverse('city_page', args=[self.city.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find Rooms, PGs & Flats in Bengaluru")
        self.assertContains(response, "Whitefield")
        self.assertContains(response, "Premium Flat in Whitefield")

    def test_area_page_view(self):
        # Visit Bengaluru/Whitefield area landing page
        response = self.client.get(reverse('area_page', args=[self.city.slug, self.area.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Flat in Whitefield")

    def test_search_view_city_area_filters(self):
        # Test filtering by city slug
        response = self.client.get(reverse('search'), {'city': self.city.slug})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Flat in Whitefield")
        
        # Test filtering by area slug
        response = self.client.get(reverse('search'), {'city': self.city.slug, 'area': self.area.slug})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Flat in Whitefield")

