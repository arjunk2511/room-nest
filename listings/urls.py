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
    path('edit-property/<int:listing_id>/', views.edit_property, name='edit_property'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('listing/<int:listing_id>/review/', views.add_review, name='add_review'),
    path('listing/<int:listing_id>/track-whatsapp/', views.track_whatsapp_click, name='track_whatsapp'),
    path('about/', views.about_us, name='about_us'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_conditions, name='terms_conditions'),
    path('contact/', views.contact_us, name='contact_us'),
]
