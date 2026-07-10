import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dummy-key-for-roomnest-project')

# Environments: development, staging, production
import sys
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').lower()
if DJANGO_ENV not in ['development', 'staging', 'production']:
    DJANGO_ENV = 'development'

# Enforce secure defaults on staging/production, local debug on development
if 'DEBUG' in os.environ:
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
else:
    DEBUG = (DJANGO_ENV == 'development')

# Determine if running in production-like environment (staging or production)
IS_PRODUCTION = (
    DJANGO_ENV in ['staging', 'production']
    or os.environ.get('IS_PRODUCTION', 'False') == 'True'
    or 'RAILWAY_ENVIRONMENT' in os.environ
    or 'RENDER' in os.environ
)

# Retrieve ALLOWED_HOSTS from environment, default to common production domains
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = [
        "roomnest.online",
        "www.roomnest.online",
        "room-nest-production.up.railway.app",
        "room-nest.onrender.com"
    ]

# Ensure required production domains are in ALLOWED_HOSTS
for host in [
    "roomnest.online",
    "www.roomnest.online",
    "room-nest-production.up.railway.app"
]:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Retrieve CSRF_TRUSTED_ORIGINS from environment
csrf_origins_env = os.environ.get('CSRF_TRUSTED_ORIGINS')
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_env.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://roomnest.online",
        "https://www.roomnest.online",
        "https://room-nest-production.up.railway.app",
        "https://room-nest.onrender.com"
    ]

# Ensure required production domains are in CSRF_TRUSTED_ORIGINS
for origin in [
    "https://roomnest.online",
    "https://www.roomnest.online",
    "https://room-nest-production.up.railway.app"
]:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Add any environment-provided public domains to ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
for env_var in ['RAILWAY_PUBLIC_DOMAIN', 'RENDER_EXTERNAL_HOSTNAME', 'PUBLIC_DOMAIN']:
    domain = os.environ.get(env_var)
    if domain:
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)
        origin = f"https://{domain}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# Support local development when running locally or in debug mode
if not IS_PRODUCTION or os.environ.get('FORCE_DEBUG') == 'True' or DEBUG:
    # Allow local development and mobile testing
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost', '[::1]', '*'])
    
    # Dynamically resolve and trust local IP for network testing
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        ALLOWED_HOSTS.append(local_ip)
        CSRF_TRUSTED_ORIGINS.extend([
            f"http://{local_ip}:8000",
            f"https://{local_ip}:8000",
            f"http://{local_ip}",
            f"https://{local_ip}",
        ])
    except Exception:
        pass
        
    # Support local tunneling tools like ngrok
    CSRF_TRUSTED_ORIGINS.extend([
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
    ])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'cloudinary_storage',
    'cloudinary',
    
    # Custom apps
    'accounts.apps.AccountsConfig',
    'listings.apps.ListingsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'webpush',
]

SITE_ID = 1

MIDDLEWARE = [
    'roomnest.middleware.PerformanceMiddleware',  # Profile request/response query counts and times!
    'listings.middleware.IPRateLimitMiddleware',  # Rate limit requests to 100/min!
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # GZIP compress dynamic HTML content for 5x faster mobile speed!
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'roomnest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'listings.context_processors.unread_messages',
                'listings.context_processors.active_cities',
            ],
        },
    },
]

WSGI_APPLICATION = 'roomnest.wsgi.application'

import dj_database_url
import os
import sys

database_url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
if not database_url and os.environ.get("PGHOST"):
    # Construct DATABASE_URL from individual PostgreSQL variables
    pg_user = os.environ.get("PGUSER", "")
    pg_pass = os.environ.get("PGPASSWORD", "")
    pg_host = os.environ.get("PGHOST", "")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_db = os.environ.get("PGDATABASE", "")
    database_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

is_collectstatic = 'collectstatic' in sys.argv

if not database_url and is_collectstatic:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif IS_PRODUCTION:
    if not database_url:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DATABASE_URL environment variable is missing, but running in a production environment!")
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
    if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("SQLite database cannot be used in a production environment!")
else:
    if database_url:
        DATABASES = {
            "default": dj_database_url.config(
                default=database_url,
                conn_max_age=600,
                ssl_require=True,
            )
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

# Cache Configuration (Sub-millisecond local memory cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'roomnest-performance-cache',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if 'CLOUDINARY_CLOUD_NAME' in os.environ:
    STORAGES["default"]["BACKEND"] = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Prevent WhiteNoise from crashing on missing static files in CSS
WHITENOISE_MANIFEST_STRICT = False

# Enable long-lived browser caching of static resources (1 year) for maximum return load speed!
WHITENOISE_MAX_AGE = 31536000

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrPhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Reload trigger

# Cloudinary credentials (configured via environment variables)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'your_cloud_name_here'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', 'your_api_key_here'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'your_api_secret_here'),
}

# Production Security and Optimization Settings
if IS_PRODUCTION and os.environ.get('FORCE_DEBUG') != 'True' and not DEBUG:
    # Redirect all HTTP requests to HTTPS
    SECURE_SSL_REDIRECT = True
    
    # Trust the reverse proxy header for HTTPS detection
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Use headers passed by the reverse proxy to get the real host and port
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    
    # Ensure cookies are only sent over secure HTTPS connections
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Strict-Transport-Security (HSTS) settings
    if DJANGO_ENV == 'production':
        SECURE_HSTS_SECONDS = 31536000  # 1 year
    else:
        # Staging: short HSTS duration to allow easy local recovery if needed
        SECURE_HSTS_SECONDS = 3600  # 1 hour
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "BPeisOSjSEOWGcBRtzI6ZpK_aAHP8ZdAhxP0Dvm-fSNNUY75qWIW8L9kD7rjV5TWqfoQFOCN1g88BbdsGxamm4I",
    "VAPID_PRIVATE_KEY": "tI1DnvnFrB9Vism4m61VrzVaHV5rDiwa7dSc1XZpexU",
    "VAPID_ADMIN_EMAIL": "admin@roomnest.online"
}
