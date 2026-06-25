import time
from django.db import connection
from django.conf import settings

class PerformanceMiddleware:
    """
    Lightweight middleware to track request response time and database query counts in development.
    Appends custom headers to the response: X-Response-Time-Ms and X-Query-Count.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only profile if in DEBUG mode to avoid any production overhead
        if not getattr(settings, 'DEBUG', False):
            return self.get_response(request)

        start_time = time.perf_counter()
        response = self.get_response(request)
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        query_count = len(connection.queries)

        response['X-Response-Time-Ms'] = f"{duration_ms:.2f}"
        response['X-Query-Count'] = str(query_count)

        return response
