"""Admin console URL configuration for port 14001."""
from django.contrib import admin
from django.urls import include, path
from django.views import static as static_views

urlpatterns = [
    # Admin home
    path('admin/', admin.site.urls),

    # Admin console endpoints
    path('api/admin/settings/', include('apps.admin_console.presentation.urls')),
    path('api/admin/catalog/', include('apps.model_catalog.presentation.urls')),
    path('api/admin/audit/', include('apps.audit_logs.presentation.urls')),

    # Media and static (for admin assets)
    path('media/', static_views.serve, {'document_root': '/media'}),
    path('static/', static_views.serve, {'document_root': '/static'}),
]
