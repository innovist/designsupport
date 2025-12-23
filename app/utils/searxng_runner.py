"""
SearXNG local runner helpers
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional, TextIO


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def start_searxng(
    repo_dir: Path,
    settings_dir: Path,
    log_file: Path,
    host: str,
    port: int,
    logger
) -> Optional[subprocess.Popen]:
    if is_port_open(host, port):
        logger.info(f"SearXNG already running at {host}:{port}")
        return None
    if not repo_dir.exists():
        logger.warning(f"SearXNG repo not found: {repo_dir}")
        return None
    if not settings_dir.exists():
        logger.warning(f"SearXNG settings dir not found: {settings_dir}")
        return None

    env = os.environ.copy()
    env["SEARXNG_SETTINGS_PATH"] = str(settings_dir)
    env["SEARXNG_PORT"] = str(port)
    env["SEARXNG_BIND_ADDRESS"] = host
    env.setdefault("SEARXNG_DEBUG", "0")
    env["PYTHONPATH"] = f"{repo_dir}:{env.get('PYTHONPATH', '')}"

    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle: TextIO = open(log_file, "a", encoding="utf-8")
    cmd = [sys.executable, "-m", "searx.webapp"]
    process = subprocess.Popen(
        cmd,
        cwd=str(repo_dir),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=log_handle
    )
    log_handle.close()
    logger.info(f"SearXNG started (pid={process.pid})")
    return process


def stop_searxng(process: Optional[subprocess.Popen], logger) -> None:
    if not process:
        return
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
        logger.info("SearXNG stopped")
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning("SearXNG force killed")
