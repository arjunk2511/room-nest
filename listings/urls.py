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
    path('listing/<int:listing_id>/track-call/', views.track_call_click, name='track_call'),
    path('listing/<int:listing_id>/report/', views.report_listing, name='report_listing'),
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
    path('rewards-admin/submission/approve/<int:submission_id>/', views.admin_approve_submission, name='admin_approve_submission'),
    path('rewards-admin/submission/reject/<int:submission_id>/', views.admin_reject_submission, name='admin_reject_submission'),
    path('rewards-admin/submission/publish/<int:submission_id>/', views.admin_publish_submission, name='admin_publish_submission'),
    path('rewards-admin/withdrawal/approve-pay/<int:withdrawal_id>/', views.admin_pay_withdrawal, name='admin_pay_withdrawal'),
    path('rewards-admin/withdrawal/reject/<int:withdrawal_id>/', views.admin_reject_withdrawal, name='admin_reject_withdrawal'),
    path('rewards-admin/reports/export/', views.export_rewards_report, name='export_rewards_report'),
    path('wallet/withdraw/', views.request_withdrawal, name='request_withdrawal'),
    path('notifications/read-all/', views.read_all_notifications, name='read_all_notifications'),
    
    # Blog System
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    
    # Static Indexable Search Pages
    path('search/<slug:city_slug>/', views.search_by_city, name='search_by_city'),
    path('search/<slug:city_slug>/<slug:type_slug>/', views.search_by_city_and_type, name='search_by_city_and_type'),
    
    # Fallback direct string slug URL
    path('listing/<slug:listing_slug>/', views.details_by_slug, name='details_by_slug'),
    
    # Dynamic city and area landing pages (placed at the end to avoid conflicts)
    path('<slug:city_slug>/', views.city_page, name='city_page'),
    path('<slug:city_slug>/<slug:area_slug>/', views.area_page, name='area_page'),
    path('<slug:city_slug>/<slug:area_slug>/<slug:listing_slug>/', views.listing_detail_by_slug, name='listing_detail_by_slug'),
]
