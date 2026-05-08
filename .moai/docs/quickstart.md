# DesignSupport Quick Start Guide

## Prerequisites

- Python 3.13+
- PostgreSQL 16+ (or use SQLite for development)
- Redis 7+ (for Celery and caching)
- Django 5.2

## Installation

### 1. Clone and Setup Environment

```bash
cd /path/to/DesignSupport
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Services

**Option A: Development (SQLite + sync Celery)**

```bash
# Start user workspace server (port 14000)
python manage.py runserver 14000

# In another terminal, start admin console (port 14001)
python manage.py runserver 14001
```

**Option B: Production (PostgreSQL + Redis + Celery)**

```bash
# Start Redis (ports 14010 for broker/cache)
redis-server --port 14010

# Start PostgreSQL (port 14020)
# Use your preferred PostgreSQL setup

# Start Celery worker
celery -A config.celery_app worker -l INFO

# Start Celery beat (for scheduled tasks)
celery -A config.celery_app beat -l INFO

# Start user workspace server (port 14000)
python manage.py runserver 14000

# In another terminal, start admin console (port 14001)
python manage.py runserver 14001
```

## Project Structure

```
DesignSupport/
├── config/                 # Django configuration
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── dev.py         # Development overrides
│   │   └── prod.py        # Production overrides
│   ├── urls_user.py       # User workspace URLs (port 14000)
│   ├── urls_admin.py      # Admin console URLs (port 14001)
│   └── celery_app.py      # Celery configuration
│
├── apps/                   # Domain applications (15 modules)
│   ├── accounts/          # User authentication
│   ├── workspaces/        # Tenant/workspace management
│   ├── design_projects/   # Project organization
│   ├── design_sessions/   # 17-step design pipeline
│   ├── conversations/     # Chat conversations
│   ├── user_assets/       # Sketch uploads
│   ├── trend_knowledge/   # Trend research
│   ├── references/        # Reference search
│   ├── concepts/          # Concept generation
│   ├── abstraction/       # Design abstraction
│   ├── generation/        # Sketch generation
│   ├── specs/             # Spec documentation
│   ├── model_catalog/     # AI model management
│   ├── admin_console/     # Admin interface
│   └── audit_logs/        # Audit trail
│
├── shared/                 # Shared infrastructure
│   ├── domain/            # Domain layer
│   │   ├── exceptions.py  # Domain exceptions
│   │   └── value_objects/ # Value objects
│   ├── application/       # Application layer
│   │   ├── ports.py       # Port interfaces
│   │   └── result.py      # Result monad
│   ├── infrastructure/    # Infrastructure layer
│   │   ├── orm/           # Base models
│   │   ├── tenant_middleware/  # Multi-tenancy
│   │   ├── observability/      # Logging
│   │   └── ssrf_guard/         # SSRF protection
│   └── presentation/      # Presentation layer
│       ├── base_views.py  # Base API views
│       ├── error_handlers.py  # Error handling
│       └── pagination.py  # Pagination
│
├── static/                 # Static files
├── templates/              # Django templates
├── locale/                 # i18n translations
├── media/                  # User uploads
└── manage.py              # Django management script
```

## Clean Architecture Layers

Each app follows the 4-layer Clean Architecture pattern:

```
apps/{app_name}/
├── domain/                # Business logic (pure Python)
│   ├── entities.py       # Domain entities
│   ├── value_objects.py  # Value objects
│   ├── services.py       # Domain services
│   └── exceptions.py     # Domain exceptions
│
├── application/          # Use cases (orchestration)
│   ├── ports.py          # Repository interfaces
│   ├── use_cases/        # Use case implementations
│   └── orchestrator/     # Workflow orchestration
│
├── infrastructure/       # External concerns
│   ├── orm/             # Django models
│   ├── repositories/    # Repository implementations
│   ├── adapters/        # External service adapters
│   └── tasks/           # Celery tasks
│
└── presentation/         # API layer
    ├── urls.py          # URL routing
    ├── views.py         # API views
    └── serializers.py   # DRF serializers
```

## API Endpoints

### User Workspace (port 14000)

```
GET  /                               # Home page
POST /api/auth/login/               # User login
POST /api/auth/logout/              # User logout
GET  /api/workspaces/               # List workspaces
POST /api/workspaces/               # Create workspace
GET  /api/projects/                 # List projects
POST /api/projects/                 # Create project
GET  /api/sessions/                 # List design sessions
POST /api/sessions/                 # Create design session
GET  /api/conversations/            # List conversations
POST /api/conversations/            # Create conversation
GET  /api/assets/                   # List user assets
POST /api/assets/                   # Upload asset
```

### Admin Console (port 14001)

```
GET  /admin/                        # Django admin
GET  /api/admin/settings/           # Admin settings
GET  /api/admin/catalog/            # Model catalog
GET  /api/admin/audit/              # Audit logs
```

## State Machine

Design sessions follow a 17-step pipeline with state transitions:

```
QUEUED (1)
  ↓
RESEARCHING (5) → CONCEPTING (6) → REFERENCING (9) →
ABSTRACTING (11) → GENERATING (13) → DOCUMENTING (16) →
REVIEW_READY (17) [TERMINAL]

Any state → FAILED [can retry from QUEUED]
```

**Modes**:
- **Guided**: Waits for user decisions between steps
- **Auto**: Automatically progresses through all steps

## Testing

```bash
# Run all tests
pytest --cov=apps --cov=shared --cov-report=html

# Run specific app tests
pytest apps/design_sessions/tests/

# Run with coverage
pytest --cov=apps.design_sessions --cov-report=html
```

Target: 85%+ coverage

## Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .
black .
isort .

# Type checking
mypy apps/ shared/
```

## Troubleshooting

### Django Not Found

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify Django is installed
pip show django
```

### Database Connection Errors

```bash
# Check PostgreSQL is running on port 14020
psql -U postgres -h localhost -p 14020

# Or use SQLite for development
# Edit .env: remove DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
```

### Redis Connection Errors

```bash
# Check Redis is running on port 14010
redis-cli -p 14010 ping

# Should return: PONG
```

### Celery Tasks Not Executing

```bash
# Check Celery worker is running
celery -A config.celery_app inspect active

# Check Celery logs for errors
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:/path/to/DesignSupport"

# Or use python -m module
python -m manage runserver 14000
```

## Environment Variables

Key variables in `.env`:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=designsupport
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=14020

# Redis
CELERY_BROKER_URL=redis://localhost:14010/0
CELERY_RESULT_BACKEND=redis://localhost:14010/1

# Object Storage (MinIO/S3)
USE_S3=False
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=designsupport-media
AWS_S3_ENDPOINT_URL=http://localhost:14030
```

## Production Deployment

For production deployment, refer to:
- `.moai/docs/deployment-manual.md`
- `.moai/docs/architecture-guide.md`
- `.moai/docs/api-documentation.md`

## Support

For issues or questions:
1. Check `.moai/docs/faq.md`
2. Review `.moai/docs/` for detailed documentation
3. Check db_reference.md for database schema

## License

Proprietary - All rights reserved

---

**Last Updated**: 2026-05-08
**Version**: 1.0.0
**Status**: Foundation Complete ✅
