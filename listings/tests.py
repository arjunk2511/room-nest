from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Listing, Lead, City, Area, PropertySubmission, RewardWallet, RewardHistory, WithdrawalRequest, RewardTransaction, PaymentHistory, AdminRewardLog, Notification
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


class ReferralsAndRewardsTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='reward_owner', password='ownerpassword', email='reward_owner@roomnest.online')
        self.submitter = User.objects.create_user(username='reward_submitter', password='submitterpassword', email='reward_submitter@roomnest.online')
        self.admin = User.objects.create_superuser(username='reward_admin', password='adminpassword', email='reward_admin@roomnest.online')
        
        # Ensure City exists
        self.city, _ = City.objects.get_or_create(name="Bengaluru", slug="bengaluru", is_active=True)
        self.area, _ = Area.objects.get_or_create(city=self.city, name="Banashankari", slug="banashankari", is_active=True)
        
        self.client = Client()

    def test_referral_submission_success(self):
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        response = self.client.post(reverse('earn_rewards'), {
            'submitted_by_name': 'Reward Submitter',
            'submitted_by_mobile': '9876543210',
            'owner_name': 'John Doe',
            'owner_mobile': '9000000001',
            'property_type': 'Flat',
            'property_address': 'Flat 302, Outer Ring Road, Bengaluru',
            'city': self.city.id,
            'permission_confirmed': 'on',
            'notes': 'Spotted tolet board near office.'
        })
        # Verify it redirects to profile upon success
        self.assertEqual(response.status_code, 302)
        
        # Verify submission object is created in Pending status
        submission = PropertySubmission.objects.get(owner_mobile='9000000001')
        self.assertEqual(submission.property_type, 'Flat')
        self.assertEqual(submission.status, 'Pending')
        
        # Verify NO reward is created initially (must be approved and published first)
        self.assertFalse(RewardHistory.objects.filter(property_submission=submission).exists())
        
        # Verify notification is sent
        notification = Notification.objects.filter(user=self.submitter, title="Property Submitted").first()
        self.assertIsNotNone(notification)

    def test_referral_anti_spam_duplicate_prevention(self):
        # Create an existing submission
        PropertySubmission.objects.create(
            submitter=self.submitter,
            submitted_by_name='Reward Submitter',
            submitted_by_mobile='9876543210',
            owner_name='John Doe',
            owner_mobile='+919000000002',
            property_type='Flat',
            property_address='Flat 302, Outer Ring Road, Bengaluru',
            city=self.city,
            status='Pending'
        )
        
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        # Try submitting same owner_mobile & city
        response = self.client.post(reverse('earn_rewards'), {
            'submitted_by_name': 'Reward Submitter',
            'submitted_by_mobile': '9876543210',
            'owner_name': 'John Doe',
            'owner_mobile': '9000000002',
            'property_type': 'Flat',
            'property_address': 'Flat 302, Outer Ring Road, Bengaluru',
            'city': self.city.id,
            'permission_confirmed': 'on'
        })
        
        # Under new system, duplicate submissions are immediately saved as Rejected
        submission = PropertySubmission.objects.filter(owner_mobile='9000000002').latest('created_at')
        self.assertEqual(submission.status, 'Rejected')
        self.assertTrue("Auto-rejected: Duplicate property details detected" in submission.notes)

    def test_direct_owner_listing_reward_approval_flow(self):
        # Create a listing for self.owner
        listing = Listing.objects.create(
            title="Spacious Room in Banashankari",
            location="Banashankari",
            city=self.city,
            area=self.area,
            price=8000.00,
            deposit=15000.00,
            type="Single Room",
            owner=self.owner,
            listing_purpose="Rent",
            phone="9000000003",
            verification_status="Pending"
        )
        
        # Login as staff admin and approve verification
        self.client.login(username='reward_admin', password='adminpassword')
        response = self.client.post(reverse('approve_verification', args=[listing.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify listing and reward are approved
        listing.refresh_from_db()
        self.assertTrue(listing.is_verified)
        self.assertEqual(listing.verification_status, 'Verified')
        
        # Verify RewardHistory is created
        reward = RewardHistory.objects.get(listing=listing)
        self.assertEqual(reward.user, self.owner)
        self.assertEqual(reward.reward_amount, 50.00)
        self.assertEqual(reward.status, 'Available')
        
        # Verify wallet credited
        wallet = RewardWallet.objects.get(user=self.owner)
        self.assertEqual(wallet.available_balance, 50.00)
        self.assertEqual(wallet.total_earned, 50.00)
        
        # Verify notification is sent
        notifications = Notification.objects.filter(user=self.owner)
        self.assertTrue(notifications.filter(title="Reward Credited").exists())

    def test_admin_publish_referral_flow(self):
        # Create submission
        submission = PropertySubmission.objects.create(
            submitter=self.submitter,
            submitted_by_name='Reward Submitter',
            submitted_by_mobile='9876543210',
            owner_name='John Doe',
            owner_mobile='+919000000004',
            property_type='Flat',
            property_address='Flat 302, Outer Ring Road, Bengaluru',
            city=self.city,
            status='Pending'
        )
        
        self.client.login(username='reward_admin', password='adminpassword')
        
        # 1. Approve referral submission
        response = self.client.post(reverse('admin_approve_submission', args=[submission.id]))
        self.assertEqual(response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'Approved')
        
        # 2. Publish referral submission (should create listing, reward, and credit wallet)
        response = self.client.post(reverse('admin_publish_submission', args=[submission.id]))
        self.assertEqual(response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'Published')
        
        # Check listing creation
        listing = Listing.objects.get(phone='+919000000004')
        self.assertEqual(listing.verification_status, 'Verified')
        
        # Check reward and wallet
        reward = RewardHistory.objects.get(property_submission=submission)
        self.assertEqual(reward.status, 'Available')
        wallet = RewardWallet.objects.get(user=self.submitter)
        self.assertEqual(wallet.available_balance, 50.00)

    def test_withdrawal_request_success_and_payout_flow(self):
        # Prepopulate wallet
        wallet = RewardWallet.get_or_create_wallet(self.submitter)
        wallet.available_balance = 250.00
        wallet.total_earned = 250.00
        wallet.save()
        
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        # Request withdrawal
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '200.00',
            'upi_id': 'submitter@oksbi'
        })
        self.assertEqual(response.status_code, 302)
        
        # Wallet balance should immediately decrease to ₹50 to prevent double spending
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, 50.00)
        self.assertEqual(wallet.upi_id, 'submitter@oksbi')
        
        # Check request created
        req = WithdrawalRequest.objects.get(user=self.submitter)
        self.assertEqual(req.amount, 200.00)
        self.assertEqual(req.status, 'Pending')
        
        # Login as Admin to disburse payout
        self.client.login(username='reward_admin', password='adminpassword')
        response = self.client.post(reverse('admin_pay_withdrawal', args=[req.id]), {
            'payment_method': 'UPI',
            'transaction_ref': 'UTR12345678',
            'notes': 'Paid via admin dashboard panel'
        })
        self.assertEqual(response.status_code, 302)
        
        # Check request status updated
        req.refresh_from_db()
        self.assertEqual(req.status, 'Paid')
        self.assertEqual(req.transaction_id, 'UTR12345678')
        
        # Check wallet withdrawn amount updated
        wallet.refresh_from_db()
        self.assertEqual(wallet.withdrawn_amount, 200.00)
        
        # Check payment history logged
        payment = PaymentHistory.objects.get(withdrawal_request=req)
        self.assertEqual(payment.amount, 200.00)
        self.assertEqual(payment.transaction_reference, 'UTR12345678')

    def test_withdrawal_request_insufficient_balance(self):
        wallet = RewardWallet.get_or_create_wallet(self.submitter)
        wallet.available_balance = 150.00
        wallet.save()
        
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        # Try withdrawing ₹200 (minimum is ₹200 but wallet has ₹150)
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '200.00',
            'upi_id': 'submitter@oksbi'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify no request is created and balance is unchanged
        self.assertFalse(WithdrawalRequest.objects.filter(user=self.submitter).exists())
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, 150.00)

    def test_withdrawal_request_invalid_upi(self):
        wallet = RewardWallet.get_or_create_wallet(self.submitter)
        wallet.available_balance = 250.00
        wallet.save()
        
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        # Post invalid UPI format
        response = self.client.post(reverse('request_withdrawal'), {
            'amount': '200.00',
            'upi_id': 'invalid-upi-id-format'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WithdrawalRequest.objects.filter(user=self.submitter).exists())

    def test_withdrawal_rejection_refund_flow(self):
        # Prepopulate wallet
        wallet = RewardWallet.get_or_create_wallet(self.submitter)
        wallet.available_balance = 250.00
        wallet.save()
        
        # Create request (directly or via post)
        self.client.login(username='reward_submitter', password='submitterpassword')
        self.client.post(reverse('request_withdrawal'), {
            'amount': '200.00',
            'upi_id': 'submitter@oksbi'
        })
        
        # Balance is ₹50
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, 50.00)
        
        req = WithdrawalRequest.objects.get(user=self.submitter)
        
        # Admin rejects withdrawal request
        self.client.login(username='reward_admin', password='adminpassword')
        response = self.client.post(reverse('admin_reject_withdrawal', args=[req.id]), {
            'rejection_notes': 'Verification failed on UPI details'
        })
        self.assertEqual(response.status_code, 302)
        
        # Check status and refund
        req.refresh_from_db()
        self.assertEqual(req.status, 'Rejected')
        
        # Wallet available balance should be refunded to ₹250
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, 250.00)

    def test_unauthorized_access_to_reward_actions(self):
        # Create submission
        submission = PropertySubmission.objects.create(
            submitter=self.submitter,
            submitted_by_name='Reward Submitter',
            submitted_by_mobile='9876543210',
            owner_name='John Doe',
            owner_mobile='+919000000005',
            property_type='Flat',
            property_address='Flat 302, Outer Ring Road, Bengaluru',
            city=self.city,
            status='Pending'
        )
        
        # Attempt access as standard logged in user
        self.client.login(username='reward_submitter', password='submitterpassword')
        
        # Try to approve submission
        response = self.client.post(reverse('admin_approve_submission', args=[submission.id]))
        self.assertEqual(response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'Pending') # Remains pending

    def test_search_suggestions_api(self):
        # Query Suggestions with empty q (returns popular searches)
        response = self.client.get(reverse('search_suggestions'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['popular']) > 0)
        
        # Query Suggestions with prefix "Ban" (to match Bengaluru and Banashankari)
        response = self.client.get(reverse('search_suggestions'), {'q': 'Ban'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify Bengaluru is matched in cities (due to custom prefix handler)
        cities = [c['name'] for c in data['cities']]
        self.assertIn("Bengaluru", cities)
        
        # Verify Banashankari is matched in areas
        areas = [a['name'] for a in data['areas']]
        self.assertIn("Banashankari", areas)


class SeoAndFriendlyUrlsTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='seo_owner', password='ownerpassword', email='seo_owner@roomnest.online')
        self.client = Client()
        
        # Ensure City and Area exist
        self.city, _ = City.objects.get_or_create(name="Bengaluru", slug="bengaluru", is_active=True)
        self.area, _ = Area.objects.get_or_create(city=self.city, name="HSR Layout", slug="hsr-layout", is_active=True)
        
    def test_listing_slug_generation_and_seo_alt(self):
        listing = Listing.objects.create(
            title="Premium Room in HSR Layout",
            location="HSR Layout",
            city=self.city,
            area=self.area,
            price=12000.00,
            deposit=24000.00,
            type="PG (Men)",
            owner=self.owner,
            listing_purpose="Rent"
        )
        # Verify slug is generated automatically on save
        self.assertTrue(listing.slug)
        self.assertIn('pg-for-boys', listing.slug)
        
        # Verify alt text generation
        alt_text = listing.get_seo_alt_text()
        self.assertIn("Boys PG in Bengaluru", alt_text)
        
        # Verify absolute URL
        absolute_url = listing.get_absolute_url()
        self.assertEqual(absolute_url, f"/bengaluru/{listing.slug}/")

    def test_old_url_redirect_to_friendly_url(self):
        listing = Listing.objects.create(
            title="Premium Room in HSR Layout",
            location="HSR Layout",
            city=self.city,
            area=self.area,
            price=12000.00,
            deposit=24000.00,
            type="PG (Men)",
            owner=self.owner,
            listing_purpose="Rent"
        )
        old_url = reverse('details', args=[listing.id])
        response = self.client.get(old_url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, listing.get_absolute_url())

    def test_friendly_url_routing_resolution(self):
        listing = Listing.objects.create(
            title="Premium Flat in HSR Layout",
            location="HSR Layout",
            city=self.city,
            area=self.area,
            price=12000.00,
            deposit=24000.00,
            type="2BHK",
            owner=self.owner,
            listing_purpose="Rent"
        )
        # Request detail page via friendly URL
        friendly_url = listing.get_absolute_url()
        response = self.client.get(friendly_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Flat in HSR Layout")
        self.assertContains(response, "2 BHK Flat for Rent in HSR Layout, Bengaluru")

    def test_dynamic_seo_headers(self):
        # Test search SEO tags for city search
        response = self.client.get(reverse('search'), {'city': self.city.slug})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Rooms, PGs &amp; Rental Properties in Bengaluru | RoomNest</title>")
        
        # Test city landing page SEO tags
        response = self.client.get(reverse('city_page', args=[self.city.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Rooms, PGs &amp; Rental Properties in Bengaluru | RoomNest</title>")


class ProfilePageTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testprofileuser', password='testpassword', email='profileuser@roomnest.online')
        self.client = Client()

    def test_anonymous_profile_redirect(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_authenticated_profile_view(self):
        self.client.login(username='testprofileuser', password='testpassword')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)


class SmartLocationTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='locowner', password='password', email='loc@roomnest.online')
        self.city, _ = City.objects.get_or_create(slug="mysore", defaults={"name": "Mysore", "is_active": True})
        self.area, _ = Area.objects.get_or_create(slug="gokulam", city=self.city, defaults={"name": "Gokulam", "is_active": True})
        
        self.listing = Listing.objects.create(
            title="Premium 2BHK in Gokulam Center",
            location="Gokulam",
            city=self.city,
            area=self.area,
            price=15000.00,
            deposit=30000.00,
            type="2BHK",
            latitude=12.3211,
            longitude=76.6433,
            owner=self.owner,
            listing_purpose="Rent"
        )
        self.client = Client()

    def test_landmarks_api_success(self):
        url = reverse('listing_landmarks_api', args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("schools", data)
        self.assertIn("hospitals", data)
        self.assertIn("transit", data)
        self.assertIn("shopping", data)
        
        listing2 = Listing.objects.create(
            title="Coordsless Property",
            location="Saraswathipuram",
            city=self.city,
            area=self.area,
            price=12000.00,
            owner=self.owner,
            listing_purpose="Rent"
        )
        url2 = reverse('listing_landmarks_api', args=[listing2.id])
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 200)

    def test_area_page_renders_successfully(self):
        url = reverse('area_page', args=[self.city.slug, self.area.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'area_page.html')
        self.assertContains(response, "Properties for Rent in Gokulam")
        self.assertContains(response, "₹15,000")





