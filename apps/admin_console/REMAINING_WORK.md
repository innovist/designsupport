# Admin Console - Remaining Implementation Work

## Priority 1: Core Infrastructure (MUST HAVE)

### 1. Repository Implementations
**File**: `infrastructure/repositories.py`

Implement all port interfaces:
- `ModelCatalogRepository` - Access model_catalog app data
- `PolicyRepository` - Access policy data with versioning
- `AuditLogRepository` - Access audit_logs app data
- `MetricsRepository` - Aggregate model invocation metrics
- `UserManagementRepository` - Access user/tenant data
- `JobQueueRepository` - Access generation job queue
- `PolicyChangeLogRepository` - Log all policy changes

**Key Patterns**:
```python
class PolicyRepository:
    def __init__(self, db_session):
        self.db = db_session

    async def list_feature_policies(self, session: AdminSession) -> Result[list[dict]]:
        # Query FeaturePolicyORM, convert to dict
        # Apply tenant filtering if not super_admin
        # Return Result.success(data) or Result.failure(error)
```

### 2. Database Migration
**File**: `infrastructure/orm/migrations/001_create_admin_tables.py`

Create Alembic migration for:
- admin_sessions
- policy_change_log
- admin_metrics (cached summaries)
- feature_policies
- prompt_policies
- admin_tenants
- user_tenant_roles

**Command**:
```bash
alembic revision -m "Create admin console tables"
alembic upgrade head
```

### 3. Django Views
**File**: `presentation/views.py`

Implement async views for all 9 screens:
- `DashboardView` - Aggregate and display dashboard data
- `ProvidersListView` - List/create/update/deactivate providers
- `ModelsListView` - List/create/update/deactivate models
- `PoliciesListView` - List/edit/rollback feature policies
- `PromptPoliciesListView` - List/edit/rollback prompt policies
- `MetricsView` - Display metrics with filters
- `AuditLogsView` - Search and display audit logs
- `JobQueueView` - Display job queue with retry action
- `UsersListView` - User management (super_admin only)

**Key Patterns**:
```python
class DashboardView(View):
    async def get(self, request):
        session = self._get_admin_session(request)
        use_case = GetAdminDashboard(
            metrics_port=self.metrics_repo,
            policy_port=self.policy_repo,
            # ...
        )
        result = await use_case.execute(session)

        if result.is_failure:
            return self._handle_error(result.error)

        return render(request, 'admin/dashboard.html', {
            'dashboard': result.value,
            'skeleton': True,  # Enable skeleton loading
        })
```

### 4. URL Configuration
**File**: `presentation/urls.py`

```python
app_name = 'admin'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('providers/', ProvidersListView.as_view(), name='providers'),
    path('providers/<uuid:provider_id>/', ProviderDetailView.as_view(), name='provider_detail'),
    path('models/', ModelsListView.as_view(), name='models'),
    path('policies/', PoliciesListView.as_view(), name='policies'),
    path('policies/<str:feature_key>/', PolicyDetailView.as_view(), name='policy_detail'),
    path('prompt-policies/', PromptPoliciesListView.as_view(), name='prompt_policies'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('audit-logs/', AuditLogsView.as_view(), name='audit_logs'),
    path('job-queue/', JobQueueView.as_view(), name='job_queue'),
    path('users/', UsersListView.as_view(), name='users'),
    path('tenants/', TenantsListView.as_view(), name='tenants'),
]
```

### 5. Main Project URL Integration
**File**: `config/urls.py`

```python
urlpatterns = [
    # ...
    path('admin/', include('apps.admin_console.presentation.urls')),
]
```

## Priority 2: Templates & UI (MUST HAVE)

### 6. Dashboard Template
**File**: `presentation/templates/admin/dashboard.html`

Features:
- Skeleton loading state
- Metrics cards (cost today, tokens today, failure rate)
- Recent policy changes widget
- Active jobs count
- Pending actions count

### 7. Policies Template
**File**: `presentation/templates/admin/policies.html`

Features:
- 9 feature key cards with current policy info
- Click to expand → policy detail with version history
- Edit form with validation
- Diff preview before save
- Fallback chain editor with drag-reorder

### 8. Metrics Template
**File**: `presentation/templates/admin/metrics.html`

Features:
- Time range selector (daily/weekly/monthly)
- Per-feature-key breakdown table
- Cost chart area (placeholder for Chart.js)
- Skeleton loading during data fetch

### 9. Audit Logs Template
**File**: `presentation/templates/admin/audit_logs.html`

Features:
- Filterable by actor, target, action type, date range
- Paginated list with expandable detail
- Search box
- Empty state

### 10. Job Queue Template
**File**: `presentation/templates/admin/job_queue.html`

Features:
- Pending/running/failed tabs
- Retry button for failed jobs
- Real-time status indicators
- Skeleton loading

### 11. Other Templates
- `providers.html` - Provider management
- `models.html` - Model catalog
- `prompt_policies.html` - Prompt template management
- `users.html` - User management (super_admin only)
- `tenants.html` - Tenant management (super_admin only)

## Priority 3: Static Assets (SHOULD HAVE)

### 12. Admin CSS
**File**: `static/css/admin.css`

Styles for:
- Layout (sidebar, main content)
- Navigation (active states, hover effects)
- Cards and widgets
- Tables with sorting indicators
- Forms with validation styling
- Skeleton loading animations
- Modal dialogs
- WCAG 2.1 AA compliance (focus indicators, color contrast)

### 13. Admin JavaScript
**Files**:
- `static/js/admin/main.js` - Initialization, sidebar toggle, i18n
- `static/js/admin/metrics.js` - Metrics dashboard interactions
- `static/js/admin/policy_editor.js` - Policy form validation, diff preview
- `static/js/admin/skeleton.js` - Skeleton loading utilities

**Key Features**:
```javascript
// Skeleton loading
function showSkeleton(container) {
    container.innerHTML = `
        <div class="skeleton-card">
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
        </div>
    `;
}

// Policy diff preview
function showPolicyDiff(oldPolicy, newPolicy) {
    const diff = computeDiff(oldPolicy, newPolicy);
    renderDiffModal(diff);
}
```

## Priority 4: i18n Integration (SHOULD HAVE)

### 14. Add Admin Keys to i18n Files
**Files**:
- `static/i18n/en.json` - Add admin.* keys
- `static/i18n/ko.json` - Korean translations
- `static/i18n/zh-CN.json` - Simplified Chinese
- `static/i18n/zh-TW.json` - Traditional Chinese

**Key Sections**:
```json
{
  "admin": {
    "nav": {
      "dashboard": "Dashboard",
      "providers": "Providers",
      "models": "Models",
      "policies": "Feature Policies",
      "prompt_policies": "Prompt Policies",
      "metrics": "Metrics",
      "audit_logs": "Audit Logs",
      "job_queue": "Job Queue",
      "users": "Users",
      "tenants": "Tenants"
    },
    "dashboard": {
      "title": "Dashboard",
      "metrics_today": "Today's Metrics",
      "cost": "Cost",
      "tokens": "Tokens",
      "failure_rate": "Failure Rate",
      "recent_changes": "Recent Policy Changes",
      "active_jobs": "Active Jobs",
      "pending_actions": "Pending Actions"
    },
    "policies": {
      "title": "Feature Policies",
      "edit_policy": "Edit Policy",
      "rollback": "Rollback",
      "version_history": "Version History",
      "fallback_chain": "Fallback Chain"
    }
  }
}
```

## Priority 5: Configuration & Testing (NICE TO HAVE)

### 15. Django Settings for Port 14001
**File**: `config/settings_admin.py`

```python
from .settings import *

# Admin console runs on separate port
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ADMIN_PORT = 14001

# Admin-specific middleware
MIDDLEWARE += [
    'apps.admin_console.infrastructure.middleware.AdminAuthMiddleware',
    'apps.admin_console.infrastructure.middleware.TenantIsolationMiddleware',
]

# Admin console URLs
ROOT_URLCONF = 'config.urls_admin'
```

### 16. Runserver Command
**File**: `apps/admin_console/management/commands/runadmin.py`

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        from django.core.management import call_command
        call_command('runserver', '14001')
```

### 17. Tests
**Files**:
- `tests/domain/test_entities.py`
- `tests/domain/test_services.py`
- `tests/application/test_use_cases.py`
- `tests/infrastructure/test_repositories.py`
- `tests/presentation/test_views.py`

**Coverage Target**: 85%+

## Implementation Order

1. ✅ Domain layer (entities, value objects, services)
2. ✅ Application layer (ports, use cases)
3. ✅ Infrastructure ORM models
4. ⏳ Repository implementations
5. ⏳ Database migration
6. ⏳ Django views
7. ⏳ URL configuration
8. ⏳ Templates (dashboard, policies, metrics, audit_logs, job_queue)
9. ⏳ Static CSS and JS
10. ⏳ i18n integration
11. ⏳ Configuration and testing

## Estimated Effort

- Core Infrastructure: 8-12 hours
- Templates & UI: 12-16 hours
- Static Assets: 6-8 hours
- i18n Integration: 4-6 hours
- Configuration & Testing: 8-10 hours

**Total**: 38-52 hours

## Dependencies

This implementation depends on:
- ✅ `shared/domain/exceptions.py` - Already exists
- ✅ `shared/application/result.py` - Already exists
- ✅ `shared/infrastructure/orm/base_model.py` - Already exists
- ⏳ `apps/model_catalog/` - Need to verify port compatibility
- ⏳ `apps/audit_logs/` - Need to verify port compatibility
- ⏳ `apps/generation/` - Need job queue port compatibility
