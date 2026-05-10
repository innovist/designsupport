"""Static validation for the current FastAPI architecture."""

import importlib
import py_compile
import shutil
import subprocess
from pathlib import Path

import pytest


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


def test_static_javascript_syntax():
    node = shutil.which("node")
    if not node:
        pytest.skip("node executable is required for JavaScript syntax validation")

    failures = []
    for path in Path("static/js").rglob("*.js"):
        result = subprocess.run(
            [node, "--check", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"{path}: {result.stderr.strip()}")

    assert failures == []
