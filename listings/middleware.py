import time
from django.core.cache import cache
from django.http import HttpResponse
from django.template import loader

class IPRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass rate limiting for static/media resources and admin dashboard
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        # Retrieve client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Keep a list of timestamps in Django cache
        cache_key = f"rate_limit_{ip}"
        now = int(time.time())
        requests_history = cache.get(cache_key, [])

        # Filter out timestamps older than 60 seconds
        requests_history = [t for t in requests_history if now - t < 60]

        # Rate limit to 100 requests per minute
        if len(requests_history) >= 100:
            # Render a premium, branded 429 Too Many Requests page
            template = loader.get_template('429.html')
            content = template.render({}, request)
            return HttpResponse(content, status=429, content_type='text/html')

        # Append new timestamp and save to cache
        requests_history.append(now)
        cache.set(cache_key, requests_history, 60)

        return self.get_response(request)
