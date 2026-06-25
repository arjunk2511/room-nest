from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Listing, City, Area

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'search', 'about_us', 'privacy_policy', 'terms_conditions', 'contact_us', 'login', 'register']

    def location(self, item):
        return reverse(item)

    def get_domain(self, site=None):
        return 'roomnest.online'


class ListingSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        # We index active properties
        return Listing.objects.filter(is_sold=False).order_by('-created_at')

    def location(self, item):
        return reverse('details', args=[item.id])

    def lastmod(self, item):
        return item.created_at

    def get_domain(self, site=None):
        return 'roomnest.online'


class CitySitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return City.objects.filter(is_active=True).order_by('name')

    def location(self, item):
        return reverse('city_page', args=[item.slug])

    def get_domain(self, site=None):
        return 'roomnest.online'


class AreaSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return Area.objects.filter(is_active=True, city__is_active=True).select_related('city').order_by('city__name', 'name')

    def location(self, item):
        return reverse('area_page', args=[item.city.slug, item.slug])

    def get_domain(self, site=None):
        return 'roomnest.online'

