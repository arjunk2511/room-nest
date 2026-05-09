from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Listing

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
