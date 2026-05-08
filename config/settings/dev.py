"""Development settings for Design Support SaaS."""
import os

from config.settings.base import *  # noqa: F401, F403

# Development mode
DEBUG = True
ALLOWED_HOSTS = ['*']  # Allow all hosts in development

# Database: SQLite fallback for development (if PostgreSQL not available)
if not os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Email backend (console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery: Always eager (synchronous) for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable SSL requirements in development
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Debug toolbar
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS.append('debug_toolbar')  # type: ignore[name-defined]
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # type: ignore[name-defined]
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# Logging: More verbose in development
LOGGING['root']['level'] = 'DEBUG'  # type: ignore[name-defined]
LOGGING['loggers']['django']['level'] = 'DEBUG'  # type: ignore[name-defined]
LOGGING['loggers']['apps']['level'] = 'DEBUG'  # type: ignore[name-defined]

# CORS: Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
