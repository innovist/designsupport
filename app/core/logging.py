"""
Logging infrastructure for the Design Ideation System.

Feature-specific log files with 3000-line rotating limit.
Old lines are deleted (not archived) when the limit is reached.
"""

from __future__ import annotations

import logging
import re
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional

# ── Constants ────────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
# @MX:NOTE: [AUTO] Log file rotation limit - old lines are deleted (not archived) when exceeded
_LOG_LINE_LIMIT = 3000
_LOG_TRIM_TO = 2700  # keep this many lines after trimming

# Feature → log file name mapping
_FEATURE_LOG_FILES: Dict[str, str] = {
    "workspace":   "workspace.log",
    "session":     "session.log",
    "sketch":      "sketch.log",
    "trend":       "trend.log",
    "concept":     "concept.log",
    "reference":   "reference.log",
    "abstraction": "abstraction.log",
    "generation":  "generation.log",
    "spec":        "spec.log",
    "pipeline":    "pipeline.log",
    "api":         "api.log",
    "error":       "error.log",
    "system":      "system.log",
}

_handler_registry: Dict[str, logging.Handler] = {}
_registry_lock = threading.Lock()


# ── Line-rotating file handler ────────────────────────────────────────────────

class LineRotatingFileHandler(logging.FileHandler):
    """
    File handler that trims the log file when it exceeds _LOG_LINE_LIMIT lines.
    Oldest lines are removed to keep the file at _LOG_TRIM_TO lines.
    Thread-safe via a per-instance lock.
    """

    def __init__(self, filename: str, limit: int = _LOG_LINE_LIMIT, trim_to: int = _LOG_TRIM_TO, **kwargs):
        super().__init__(filename, encoding="utf-8", **kwargs)
        self._limit = limit
        self._trim_to = trim_to
        self._line_count: Optional[int] = None
        self._trim_lock = threading.Lock()

    def _count_lines(self) -> int:
        try:
            with open(self.baseFilename, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
        except (OSError, IOError):
            return 0

    def _trim_file(self) -> None:
        try:
            with open(self.baseFilename, "r", encoding="utf-8", errors="replace") as f:
                lines = deque(f, maxlen=self._trim_to)
            with open(self.baseFilename, "w", encoding="utf-8") as f:
                f.writelines(lines)
            self._line_count = self._trim_to
        except (OSError, IOError):
            pass

    # @MX:WARN: [AUTO] Thread-safe log rotation with file trimming
    # @MX:REASON: File I/O + lock management - risk of log loss if exceptions occur silently

    def emit(self, record: logging.LogRecord) -> None:
        with self._trim_lock:
            if self._line_count is None:
                self._line_count = self._count_lines()
            super().emit(record)
            self._line_count += 1
            if self._line_count >= self._limit:
                self.flush()
                self._trim_file()


# ── Formatters ───────────────────────────────────────────────────────────────

_FILE_FMT = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_CONSOLE_FMT = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


# ── Sensitive data filter ─────────────────────────────────────────────────────

_SENSITIVE_RE = re.compile(
    r"(api[_\-]?key|password|secret|token|authorization|credential)[=:\s]+\S+",
    re.IGNORECASE,
)


class _SensitiveFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE_RE.sub(r"\1=***", record.msg)
        return True


# ── Public setup API ──────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with console output and a system.log file."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric)
    root.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(numeric)
    ch.setFormatter(_CONSOLE_FMT)
    ch.addFilter(_SensitiveFilter())
    root.addHandler(ch)

    # System-wide log file
    _ensure_feature_handler("system", numeric)


def _ensure_feature_handler(feature: str, level: int = logging.INFO) -> logging.Handler:
    """Return (creating if needed) the file handler for a feature area."""
    with _registry_lock:
        if feature in _handler_registry:
            return _handler_registry[feature]

        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = _LOG_DIR / _FEATURE_LOG_FILES.get(feature, f"{feature}.log")
        handler = LineRotatingFileHandler(str(log_file))
        handler.setLevel(level)
        handler.setFormatter(_FILE_FMT)
        handler.addFilter(_SensitiveFilter())
        _handler_registry[feature] = handler
        return handler


# @MX:ANCHOR: [AUTO] Feature-based logger provider used throughout the application
# @MX:REASON: High fan_in (40+ callers) - central logging entry point with feature inference

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger attached to the appropriate feature log file.

    The feature is inferred from the module name:
      app.application.use_cases.sketch.* → sketch.log
      app.api.routes.trends              → trend.log
      etc.
    """
    logger = logging.getLogger(name)

    feature = _infer_feature(name)
    if feature:
        handler = _ensure_feature_handler(feature)
        # Avoid duplicate handlers when the same logger is requested multiple times
        if not any(isinstance(h, LineRotatingFileHandler) for h in logger.handlers):
            logger.addHandler(handler)
        logger.propagate = True  # also goes to root (console + system.log)

    return logger


def _infer_feature(name: str) -> Optional[str]:
    """Map a dotted module name to a feature category."""
    _MAP = {
        "abstraction": "abstraction",
        "assets":      "sketch",
        "sketch":      "sketch",
        "concept":     "concept",
        "conversation": "session",
        "reference":   "reference",
        "generation":  "generation",
        "spec":        "spec",
        "trend":       "trend",
        "workspace":   "workspace",
        "session":     "session",
        "pipeline":    "pipeline",
    }
    lower = name.lower()
    for key, feature in _MAP.items():
        if key in lower:
            return feature
    if "api" in lower or "route" in lower:
        return "api"
    if "error" in lower:
        return "error"
    return "system"


# ── Structured log helpers (called from use cases / routes) ──────────────────

def log_pipeline_stage(session_id: str, stage: str, detail: str = "") -> None:
    """Record a pipeline stage transition to pipeline.log."""
    logger = logging.getLogger("pipeline")
    _ensure_feature_handler("pipeline")
    handler = _handler_registry.get("pipeline")
    if handler and handler not in logger.handlers:
        logger.addHandler(handler)
    logger.info("[PIPELINE] session=%s stage=%s %s", session_id, stage, detail)


def log_ai_call(feature: str, provider: str, model: str, prompt_tokens: int = 0, result: str = "ok") -> None:
    """Record an AI API call to the feature log."""
    logger = get_logger(f"ai.{feature}")
    logger.info("[AI] feature=%s provider=%s model=%s tokens=%d result=%s",
                feature, provider, model, prompt_tokens, result)


def log_api_request(method: str, path: str, status: int, duration_ms: float = 0.0) -> None:
    """Record an API request to api.log."""
    logger = logging.getLogger("api.requests")
    _ensure_feature_handler("api")
    handler = _handler_registry.get("api")
    if handler and handler not in logger.handlers:
        logger.addHandler(handler)
    level = logging.WARNING if status >= 400 else logging.INFO
    logger.log(level, "[API] %s %s → %d (%.1fms)", method, path, status, duration_ms)


def log_error(feature: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Record an error to both error.log and the feature log."""
    _ensure_feature_handler("error")
    err_logger = logging.getLogger("error")
    if _handler_registry.get("error") not in err_logger.handlers:
        err_logger.addHandler(_handler_registry["error"])
    ctx_str = " ".join(f"{k}={v}" for k, v in (context or {}).items())
    err_logger.error("[ERROR] feature=%s %s %s", feature, type(error).__name__, ctx_str, exc_info=error)

    feat_logger = get_logger(feature)
    feat_logger.error("[ERROR] %s: %s %s", type(error).__name__, error, ctx_str)
