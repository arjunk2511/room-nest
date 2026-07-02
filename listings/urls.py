from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('listing/<int:listing_id>/', views.details, name='details'),
    path('add-property/', views.add_property, name='add_property'),
    path('wishlist/toggle/<int:listing_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/toggle-sold/<int:listing_id>/', views.toggle_sold_status, name='toggle_sold_status'),
    
    # Dashboards
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Property Verifications
    path('listing/request-verification/<int:listing_id>/', views.request_verification, name='request_verification'),
    path('listing/approve-verification/<int:listing_id>/', views.approve_verification, name='approve_verification'),
    path('listing/reject-verification/<int:listing_id>/', views.reject_verification, name='reject_verification'),
    
    # Subscription Verification approvals
    path('subscription/approve/<int:subscription_id>/', views.approve_subscription, name='approve_subscription'),
    path('subscription/reject/<int:subscription_id>/', views.reject_subscription, name='reject_subscription'),
    
    # Leads Export
    path('leads/export-csv/', views.export_leads_csv, name='export_leads_csv'),
    
    path('edit-property/<int:listing_id>/', views.edit_property, name='edit_property'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('listing/<int:listing_id>/review/', views.add_review, name='add_review'),
    path('listing/<int:listing_id>/track-whatsapp/', views.track_whatsapp_click, name='track_whatsapp'),
    path('about/', views.about_us, name='about_us'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_conditions, name='terms_conditions'),
    path('contact/', views.contact_us, name='contact_us'),
    path('owner/delete/<int:listing_id>/', views.delete_property, name='delete_property'),
    
    # Rewards and referrals
    path('rewards/', views.earn_rewards, name='earn_rewards'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/listing/<int:listing_id>/landmarks/', views.listing_landmarks_api, name='listing_landmarks_api'),
    path('api/listing/landmarks/', views.listing_landmarks_api, name='area_landmarks_api'),
    path('rewards-admin/approve/<int:reward_id>/', views.approve_reward_claim, name='approve_reward_claim'),
    path('rewards-admin/reject/<int:reward_id>/', views.reject_reward_claim, name='reject_reward_claim'),
    path('rewards-admin/pay/<int:reward_id>/', views.pay_reward_claim, name='pay_reward_claim'),
    path('notifications/read-all/', views.read_all_notifications, name='read_all_notifications'),
    
    # Dynamic city and area landing pages (placed at the end to avoid conflicts)
    path('<slug:city_slug>/', views.city_page, name='city_page'),
    path('<slug:city_slug>/<slug:area_slug>/', views.area_page, name='area_page'),
]
