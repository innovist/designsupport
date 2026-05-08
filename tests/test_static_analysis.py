"""Static validation for the current Django modular architecture."""
import importlib
import os
import py_compile
from pathlib import Path

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


def test_python_sources_compile():
    django.setup()
    roots = [Path("apps"), Path("shared"), Path("config")]
    failures = []
    for root in roots:
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts or "migrations" in path.parts:
                continue
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{path}: {exc.msg}")
    assert failures == []


def test_app_modules_import():
    django.setup()
    failures = []
    for path in Path("apps").rglob("*.py"):
        if "__pycache__" in path.parts or "migrations" in path.parts or path.name == "admin.py":
            continue
        module_name = ".".join(path.with_suffix("").parts)
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    assert failures == []
