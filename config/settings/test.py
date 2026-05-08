"""Test settings for Design Support SaaS."""
from config.settings.base import *  # noqa: F401, F403

# Test mode
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Database: In-memory SQLite for fast tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password hashing: Use faster hashers for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email: Use memory backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery: Always eager for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable logging in tests (reduce noise)
LOGGING['handlers']['console']['class'] = 'logging.NullHandler'  # type: ignore

# Disable audit logging in tests (avoid Celery dependency)
AUDIT_LOG_ASYNC = False

# Media: Use temp directory for tests
MEDIA_ROOT = '/tmp/django-test-media'

# Static: Use temp directory
STATIC_ROOT = '/tmp/django-test-static'

# Security: Disable for tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Test-specific settings
TEST_RUNNER = 'pytest.django.runner.PytestRunner'
