import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from listings.models import (
    Listing, ListingImage, Wishlist, Message, Review, Lead,
    ListingReport, PropertySubmission, Reward, Notification,
    RewardWallet, RewardTransaction, WithdrawalRequest, RewardHistory,
    PaymentHistory, AdminRewardLog
)
from subscriptions.models import Subscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Safely removes validation/test listings and users from the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation.',
        )

    def handle(self, *args, **options):
        # 1. Query validation listings
        val_listings = Listing.objects.filter(
            title__startswith="Validation Listing",
            owner__username__startswith="validation_user_"
        )
        val_listings_count = val_listings.count()

        # 2. Query validation users
        val_users = User.objects.filter(username__startswith="validation_user_")
        val_users_count = val_users.count()

        # 3. Separate users to delete vs keep (in case they own other listings)
        users_to_delete = []
        users_to_keep = []
        val_listings_ids = set(val_listings.values_list('id', flat=True))

        for u in val_users:
            other_listings = Listing.objects.filter(owner=u).exclude(id__in=val_listings_ids)
            if other_listings.exists():
                users_to_keep.append(u)
            else:
                users_to_delete.append(u)

        users_to_delete_usernames = [u.username for u in users_to_delete]
        users_to_keep_usernames = [u.username for u in users_to_keep]

        self.stdout.write(self.style.WARNING(f"Found {val_listings_count} validation listings to delete."))
        self.stdout.write(self.style.WARNING(f"Found {val_users_count} validation users total in database:"))
        self.stdout.write(f"  - Users that will be deleted: {len(users_to_delete)} {users_to_delete_usernames}")
        self.stdout.write(f"  - Users that will be kept (own other real listings): {len(users_to_keep)} {users_to_keep_usernames}")

        if val_listings_count == 0 and len(users_to_delete) == 0:
            self.stdout.write(self.style.SUCCESS("No validation data found to clean up."))
            return

        # 4. Confirmation
        if not options['noinput']:
            confirm = input("Type 'yes' to proceed with deletion of validation data: ")
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.ERROR("Deletion cancelled by user."))
                return

        # 5. Perform deletions in a transaction
        with transaction.atomic():
            # Delete related models for validation listings explicitly (in case of custom logic / signals)
            # Related images
            images_deleted, _ = ListingImage.objects.filter(listing__in=val_listings).delete()
            # Favourites/Saved listings
            wishlist_deleted, _ = Wishlist.objects.filter(listing__in=val_listings).delete()
            # Leads
            leads_deleted, _ = Lead.objects.filter(listing__in=val_listings).delete()
            # Reports
            reports_deleted, _ = ListingReport.objects.filter(listing__in=val_listings).delete()
            # Reviews
            reviews_deleted, _ = Review.objects.filter(listing__in=val_listings).delete()
            # Messages linked to listings
            messages_deleted, _ = Message.objects.filter(listing__in=val_listings).delete()
            # Rewards linked to listings
            rewards_deleted_list, _ = Reward.objects.filter(listing__in=val_listings).delete()
            # Reward histories linked to listings
            reward_hist_deleted_list, _ = RewardHistory.objects.filter(listing__in=val_listings).delete()

            # Now delete validation listings
            listings_deleted_count, _ = val_listings.delete()

            # Delete validation users' records
            if users_to_delete:
                user_ids = [u.id for u in users_to_delete]
                
                # Favourites/Saved by these users
                Wishlist.objects.filter(user_id__in=user_ids).delete()
                # Leads by these users
                Lead.objects.filter(tenant_id__in=user_ids).delete()
                # Messages sent/received by these users
                Message.objects.filter(sender_id__in=user_ids).delete()
                Message.objects.filter(receiver_id__in=user_ids).delete()
                # Reports by these users
                ListingReport.objects.filter(reporter_id__in=user_ids).delete()
                # Reviews by these users
                Review.objects.filter(user_id__in=user_ids).delete()
                # Property submissions
                PropertySubmission.objects.filter(submitter_id__in=user_ids).delete()
                # Subscriptions
                Subscription.objects.filter(user_id__in=user_ids).delete()
                # Notifications
                Notification.objects.filter(user_id__in=user_ids).delete()
                # Rewards
                Reward.objects.filter(user_id__in=user_ids).delete()
                # Reward histories
                RewardHistory.objects.filter(user_id__in=user_ids).delete()
                # Payments
                PaymentHistory.objects.filter(user_id__in=user_ids).delete()
                # Withdrawal requests
                WithdrawalRequest.objects.filter(user_id__in=user_ids).delete()
                # Wallets
                wallets = RewardWallet.objects.filter(user_id__in=user_ids)
                RewardTransaction.objects.filter(wallet__in=wallets).delete()
                wallets.delete()
                # Admin logs
                AdminRewardLog.objects.filter(admin_user_id__in=user_ids).delete()

                # Finally delete users (cascades UserProfile, etc.)
                User.objects.filter(id__in=user_ids).delete()
                users_deleted_count = len(user_ids)
            else:
                users_deleted_count = 0

        self.stdout.write(self.style.SUCCESS("-------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("🎉 SUCCESS SUMMARY:"))
        self.stdout.write(self.style.SUCCESS(f"  - Validation listings deleted: {val_listings_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Validation users deleted: {users_deleted_count}"))
        self.stdout.write(self.style.SUCCESS("-------------------------------------------"))
