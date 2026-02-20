"""
🔍 JARVIS Error Handler — Structured Error Reporting
═══════════════════════════════════════════════════════
Replaces _si() silent error swallowing with:
- Structured error logging
- Error categorization
- Import error tracking
- Health check for engines
- Error rate monitoring
"""

import os
import sys
import time
import logging
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger("jarvis-errors")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  ERROR STORE
# ═══════════════════════════════════════════════════════════
_error_log: List[Dict] = []  # Last N errors
_error_counts: Dict[str, int] = defaultdict(int)  # Error counts by category
_import_errors: Dict[str, str] = {}  # Module → error message
_engine_health: Dict[str, Dict] = {}  # Engine → health status
MAX_ERROR_LOG = 500


def _trim_log():
    global _error_log
    if len(_error_log) > MAX_ERROR_LOG:
        _error_log = _error_log[-MAX_ERROR_LOG:]


# ═══════════════════════════════════════════════════════════
#  STRUCTURED ERROR LOGGING
# ═══════════════════════════════════════════════════════════
def log_error(category: str, message: str, details: Any = None,
              module: str = "", severity: str = "error") -> Dict:
    """Log a structured error."""
    error = {
        "id": len(_error_log) + 1,
        "category": category,
        "message": message,
        "details": str(details) if details else "",
        "module": module,
        "severity": severity,  # debug, info, warning, error, critical
        "timestamp": datetime.now(IST).isoformat(),
        "count": 1,
    }
    _error_log.append(error)
    _error_counts[category] += 1
    _trim_log()

    # Log to standard logger
    log_fn = getattr(logger, severity, logger.error)
    log_fn(f"[{category}] {module}: {message}")

    return error


def log_import_error(module: str, error: Exception):
    """Log a module import error (replaces silent _si failures)."""
    msg = str(error)
    _import_errors[module] = msg
    log_error("import", f"Failed to import {module}: {msg}", module=module, severity="warning")


def log_engine_status(engine_name: str, status: str, details: str = ""):
    """Track engine health status."""
    _engine_health[engine_name] = {
        "status": status,  # active, error, unavailable
        "details": details,
        "last_check": datetime.now(IST).isoformat(),
    }


# ═══════════════════════════════════════════════════════════
#  SAFE IMPORT — Replacement for _si() with error tracking
# ═══════════════════════════════════════════════════════════
def safe_import(mod_name: str, names: List[str]) -> Dict[str, Any]:
    """
    Import functions from a module safely, with error tracking.
    Replaces the _si() pattern but logs errors properly.
    """
    out = {}
    try:
        m = __import__(mod_name)
        for n in names:
            fn = getattr(m, n, None)
            if fn is None:
                log_error("import", f"Function '{n}' not found in {mod_name}",
                         module=mod_name, severity="debug")
            out[n] = fn
        log_engine_status(mod_name, "active")
    except Exception as e:
        log_import_error(mod_name, e)
        log_engine_status(mod_name, "error", str(e))
        for n in names:
            out[n] = None
    return out


# ═══════════════════════════════════════════════════════════
#  EXCEPTION HANDLER DECORATOR
# ═══════════════════════════════════════════════════════════
def handle_errors(category: str = "api", default_return=None):
    """Decorator that catches and logs exceptions."""
    def decorator(fn):
        import functools
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                log_error(category, str(e), traceback.format_exc(),
                         module=fn.__module__ or fn.__name__)
                return default_return

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                log_error(category, str(e), traceback.format_exc(),
                         module=fn.__module__ or fn.__name__)
                return default_return

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
#  ERROR REPORTING
# ═══════════════════════════════════════════════════════════
def get_error_summary() -> Dict:
    """Get a summary of all errors."""
    now = time.time()
    recent = [e for e in _error_log if e.get("timestamp", "") >= datetime.fromtimestamp(now - 3600, IST).isoformat()]
    return {
        "total_errors": len(_error_log),
        "errors_last_hour": len(recent),
        "by_category": dict(_error_counts),
        "import_errors": _import_errors.copy(),
        "engine_health": _engine_health.copy(),
        "recent_errors": _error_log[-10:],
    }


def get_engine_health() -> Dict[str, Dict]:
    """Get health status of all engines."""
    return _engine_health.copy()


def get_import_errors() -> Dict[str, str]:
    """Get all import errors."""
    return _import_errors.copy()


def get_recent_errors(limit: int = 20, category: str = None) -> List[Dict]:
    """Get recent errors, optionally filtered by category."""
    errors = _error_log
    if category:
        errors = [e for e in errors if e.get("category") == category]
    return errors[-limit:]


def clear_errors():
    """Clear error log (for admin)."""
    global _error_log
    _error_log.clear()
    _error_counts.clear()
    return True


# ═══════════════════════════════════════════════════════════
#  MULTI-LANGUAGE ERROR MESSAGES
# ═══════════════════════════════════════════════════════════
ERROR_MESSAGES = {
    "rate_limit": {
        "en": "Too many requests. Please wait and try again.",
        "hi": "बहुत ज़्यादा रिक्वेस्ट। कृपया रुकें और दोबारा कोशिश करें।",
    },
    "auth_failed": {
        "en": "Authentication failed. Please login again.",
        "hi": "प्रमाणीकरण विफल। कृपया दोबारा लॉगिन करें।",
    },
    "not_found": {
        "en": "Resource not found.",
        "hi": "डेटा नहीं मिला।",
    },
    "server_error": {
        "en": "Server error. Our team has been notified.",
        "hi": "सर्वर में समस्या। हमारी टीम को सूचित कर दिया गया है।",
    },
    "api_key_missing": {
        "en": "API key not configured for this service.",
        "hi": "इस सेवा के लिए API key कॉन्फ़िगर नहीं है।",
    },
    "engine_unavailable": {
        "en": "This engine is temporarily unavailable.",
        "hi": "यह इंजन अभी उपलब्ध नहीं है।",
    },
}


def get_error_message(error_key: str, lang: str = "en") -> str:
    """Get localized error message."""
    messages = ERROR_MESSAGES.get(error_key, {})
    return messages.get(lang, messages.get("en", "An error occurred"))


logger.info("🔍 Structured error handler loaded")
