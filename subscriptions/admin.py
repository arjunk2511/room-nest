from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_id', 'payment_status', 'is_active', 'start_date', 'end_date')
    list_filter = ('payment_status', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email', 'transaction_id')
    list_editable = ('payment_status', 'is_active')
