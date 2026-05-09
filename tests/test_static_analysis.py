"""Static validation for the current FastAPI architecture."""

import importlib
import py_compile
from pathlib import Path


def test_python_sources_compile():
    roots = [Path("app"), Path("main.py")]
    failures = []
    for root in roots:
        paths = [root] if root.is_file() else root.rglob("*.py")
        for path in paths:
            if "__pycache__" in path.parts:
                continue
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{path}: {exc.msg}")
    assert failures == []


def test_app_modules_import():
    failures = []
    for path in Path("app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        module_name = ".".join(path.with_suffix("").parts)
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    assert failures == []
