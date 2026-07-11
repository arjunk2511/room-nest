from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from listings.sitemaps import StaticViewSitemap, ListingSitemap, CitySitemap, AreaSitemap, BlogSitemap
from roomnest.views import system_health_view

sitemaps = {
    'static': StaticViewSitemap,
    'listings': ListingSitemap,
    'cities': CitySitemap,
    'areas': AreaSitemap,
    'blog': BlogSitemap,
}

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: https://roomnest.online/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('admin/system-health/', system_health_view, name='system_health'),
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('accounts/', include('accounts.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('webpush/', include('webpush.urls')),
    path('', include('listings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
