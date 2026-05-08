#!/bin/bash

# List of all 15 modules
MODULES="workspaces design_projects design_sessions conversations user_assets trend_knowledge references concepts abstraction generation specs model_catalog admin_console audit_logs"

# Base template for apps.py
cat > apps_template.py << 'APPS_PY'
from django.apps import AppConfig


class {CLASS_NAME}Config(AppConfig):
    """{verbose_name} module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{module_name}'
    verbose_name = '{verbose_name}'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.{module_name}.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
APPS_PY

# Create each module
for module in $MODULES; do
    # Create directory structure
    mkdir -p "apps/$module/domain"
    mkdir -p "apps/$module/application"
    mkdir -p "apps/$module/infrastructure/orm/migrations"
    mkdir -p "apps/$module/presentation"
    mkdir -p "apps/$module/tests"

    # Create __init__.py files with descriptions
    echo "# $module module" > "apps/$module/__init__.py"
    echo "# Domain layer" > "apps/$module/domain/__init__.py"
    echo "# Application layer" > "apps/$module/application/__init__.py"
    echo "# Infrastructure layer" > "apps/$module/infrastructure/__init__.py"
    echo "# ORM models" > "apps/$module/infrastructure/orm/__init__.py"
    echo "# Database migrations" > "apps/$module/infrastructure/orm/migrations/__init__.py"
    echo "# Presentation layer" > "apps/$module/presentation/__init__.py"
    echo "# Tests" > "apps/$module/tests/__init__.py"

    # Create apps.py
    class_name=$(echo "$module" | sed -r 's/(^|_)(\w)/\U\2/g')  # PascalCase
    verbose_name=$(echo "$module" | sed 's/_/ /g' | sed 's/\b\w/\u&/g')  # Title Case

    sed -e "s/{CLASS_NAME}/$class_name/g" \
        -e "s/{module_name}/$module/g" \
        -e "s/{verbose_name}/$verbose_name/g" \
        apps_template.py > "apps/$module/apps.py"

    # Create conftest.py
    cat > "apps/$module/tests/conftest.py" << CONFTEST
"""Pytest fixtures for $module module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for $module tests."""
    return {"test": "data"}
CONFTEST

    # Create empty signals.py
    touch "apps/$module/infrastructure/signals.py"

    echo "Created module: $module"
done

echo "All modules created successfully!"
