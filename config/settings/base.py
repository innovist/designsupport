"""
Base Django settings for Design Support SaaS.

All environment-specific settings are overridden in dev.py, prod.py, and test.py.
Port assignments:
- 14000: Django Web (user workspace)
- 14001: Django Admin (admin console)
- 14010: Redis (broker/cache)
- 14020: PostgreSQL (development exposed)
- 14030: MinIO (object storage)
"""
import os
from pathlib import Path
from typing import List

import structlog
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv()

# Security: REQUIRED keys must be present
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required")

# -----------------------------------------------------------------------------
# Core Django Settings
# -----------------------------------------------------------------------------
DEBUG = False
ALLOWED_HOSTS: List[str] = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'django_extensions',

    # Domain modules (16 modules)
    'apps.accounts',
    'apps.workspaces',
    'apps.design_projects',
    'apps.design_sessions',
    'apps.conversations',
    'apps.user_assets',
    'apps.trend_knowledge',
    'apps.references',
    'apps.concepts',
    'apps.abstraction',
    'apps.generation',
    'apps.specs',
    'apps.model_catalog',
    'apps.admin_console',
    'apps.audit_logs',
]

MIGRATION_MODULES = {
    'abstraction': 'apps.abstraction.infrastructure.orm.migrations',
    'accounts': 'apps.accounts.infrastructure.orm.migrations',
    'admin_console': 'apps.admin_console.infrastructure.orm.migrations',
    'audit_logs': 'apps.audit_logs.infrastructure.orm.migrations',
    'concepts': 'apps.concepts.infrastructure.orm.migrations',
    'conversations': 'apps.conversations.infrastructure.orm.migrations',
    'design_projects': 'apps.design_projects.infrastructure.orm.migrations',
    'design_sessions': 'apps.design_sessions.infrastructure.orm.migrations',
    'generation': 'apps.generation.infrastructure.orm.migrations',
    'model_catalog': 'apps.model_catalog.infrastructure.orm.migrations',
    'references': 'apps.references.infrastructure.orm.migrations',
    'specs': 'apps.specs.infrastructure.orm.migrations',
    'trend_knowledge': 'apps.trend_knowledge.infrastructure.orm.migrations',
    'user_assets': 'apps.user_assets.infrastructure.orm.migrations',
    'workspaces': 'apps.workspaces.infrastructure.orm.migrations',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'shared.infrastructure.tenant_middleware.middleware.TenantMiddleware',
    'shared.infrastructure.csp_middleware.CSPMiddleware',
]
# @MX:NOTE: Middleware order matters: TenantMiddleware after AuthenticationMiddleware
# @MX:REASON: Tenant isolation requires request.user to be populated first

# @MX:NOTE: CSP headers restrict resource loading to trusted origins
# @MX:REASON: Prevents XSS via injected scripts from untrusted CDNs
CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "blob:", "*.pexels.com", "*.unsplash.com", "*.pixabay.com", "*.wikimedia.org", "*.flickr.com"],
    'font-src': ["'self'"],
    'connect-src': ["'self'"],
    'frame-ancestors': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
}

ROOT_URLCONF = 'config.urls_user'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# -----------------------------------------------------------------------------
# Database (PostgreSQL via DATABASE_URL)
# -----------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'designsupport'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '14020'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# -----------------------------------------------------------------------------
# Celery Configuration
# -----------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:14010/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:14010/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# -----------------------------------------------------------------------------
# Object Storage (MinIO/S3 compatible)
# -----------------------------------------------------------------------------
USE_S3 = os.environ.get('USE_S3', 'False').lower() == 'true'

if USE_S3:
    # boto3-based storage for production
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'designsupport-media')
    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', 'http://localhost:14030')
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False  # Immutable uploads
else:
    # Local file storage for development
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'apps.accounts.infrastructure.adapters.token_authentication.SignedTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'shared.presentation.pagination.CursorPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'EXCEPTION_HANDLER': 'shared.presentation.error_handlers.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# -----------------------------------------------------------------------------
# CORS Settings
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:14000",
    "http://127.0.0.1:14000",
]
CORS_ALLOW_CREDENTIALS = True

# -----------------------------------------------------------------------------
# Internationalization (i18n)
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'ko'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('ko', 'Korean'),
    ('en', 'English'),
    ('zh-cn', 'Simplified Chinese'),
    ('zh-tw', 'Traditional Chinese'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# -----------------------------------------------------------------------------
# Password Validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------------
# Security Settings
# -----------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Password hashing with Argon2 (preferred) or bcrypt
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# -----------------------------------------------------------------------------
# Logging (Structured JSON)
# -----------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
        'celery': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'apps': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# -----------------------------------------------------------------------------
# Cache Configuration
# -----------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': os.environ.get(
            'DJANGO_CACHE_BACKEND',
            'django.core.cache.backends.locmem.LocMemCache',
        ),
        'LOCATION': os.environ.get('DJANGO_CACHE_LOCATION', 'designsupport-local-cache'),
        'KEY_PREFIX': 'designsupport',
        'TIMEOUT': 300,
    }
}

# Session backend
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# -----------------------------------------------------------------------------
# File Upload Validation
# ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Allowed file types for user uploads
ALLOWED_UPLOAD_EXTENSIONS = [
    '.png', '.jpg', '.jpeg', '.gif', '.webp',  # Images
    '.pdf', '.doc', '.docx',  # Documents
]

# -----------------------------------------------------------------------------
# Audit Log Configuration
# -----------------------------------------------------------------------------
AUDIT_LOG_ENABLED = True
AUDIT_LOG_ASYNC = True  # Use Celery for async logging
