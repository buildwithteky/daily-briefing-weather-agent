"""Shared helpers: structured JSON logging, HTTP fetch, source result type."""
from __future__ import annotations

import json
import logging
import sys
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

_logger = logging.getLogger("briefing")
if not _logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_h)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log(event: str, level: str = "INFO", **fields: Any) -> None:
    """Emit one JSON line. CloudWatch Logs Insights can query these fields."""
    record = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "event": event}
    record.update(fields)
    _logger.log(getattr(logging, level, logging.INFO), json.dumps(record, default=str))


@contextmanager
def timed(event: str, **fields: Any):
    """Log <event>.start and <event>.end (with duration_ms), or <event>.error."""
    start = time.perf_counter()
    log(event + ".start", **fields)
    try:
        yield
    except Exception as exc:
        log(event + ".error", level="ERROR", error=str(exc),
            error_type=type(exc).__name__,
            duration_ms=round((time.perf_counter() - start) * 1000), **fields)
        raise
    log(event + ".end", duration_ms=round((time.perf_counter() - start) * 1000), **fields)


def http_get(url: str, timeout: int = 8) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "daily-briefing-agent/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - fixed https URLs
        return resp.read()


def http_get_json(url: str, timeout: int = 8) -> Any:
    return json.loads(http_get(url, timeout).decode("utf-8"))


@dataclass
class SourceResult:
    """Outcome of one data source. Never raises; carries its own status."""
    name: str
    status: str = "unavailable"  # ok | stale | unavailable
    data: Any = None
    error: Optional[str] = None
    note: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"source": self.name, "status": self.status, "data": self.data,
                "error": self.error, "note": self.note, "fetched_at": self.fetched_at}
