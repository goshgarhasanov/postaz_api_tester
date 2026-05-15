"""HTTP execution layer — pure, threadable.

Converts a `RequestRecord` (the persistent shape of a saved request) plus the
active environment's variable map into a real `requests` call, then packages
the answer in a `ResponseData` dataclass that the UI can render synchronously.

Nothing in this module touches Qt — that's deliberate so workers can run
on any thread and we can unit-test the call assembly in isolation."""
from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests
from requests.exceptions import RequestException

from .database import RequestRecord
from .env_resolver import resolve, resolve_all
from .logger import get_logger

log = get_logger(__name__)


@dataclass
class ResponseData:
    ok: bool = True
    error: Optional[str] = None
    status_code: int = 0
    reason: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body_text: str = ""
    body_bytes: bytes = b""
    content_type: str = ""
    duration_ms: int = 0
    size_bytes: int = 0
    final_url: str = ""

    @property
    def is_json(self) -> bool:
        return "application/json" in self.content_type.lower()


def _build_kwargs(rec: RequestRecord, variables: dict[str, str]) -> tuple[str, dict[str, Any]]:
    """Resolve `{{vars}}` and translate the saved record into `requests.request` kwargs.

    Returns `(url, kwargs)` ready to be unpacked. Auth presets are folded into
    the `headers` dict here, not handed to `requests.auth=`, so the user can
    inspect the exact Authorization header that goes on the wire."""
    url = resolve(rec.url, variables).strip()
    if not url:
        raise ValueError("URL is empty")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        resolve(h.get("key", ""), variables): resolve(h.get("value", ""), variables)
        for h in rec.headers
        if h.get("enabled", True) and h.get("key")
    }
    params = [
        (resolve(p.get("key", ""), variables), resolve(p.get("value", ""), variables))
        for p in rec.params
        if p.get("enabled", True) and p.get("key")
    ]

    kwargs: dict[str, Any] = {
        "headers": headers,
        "params": params or None,
        "timeout": 60,
        "allow_redirects": True,
    }

    # Auth
    if rec.auth_type == "bearer":
        token = resolve(rec.auth_data.get("token", ""), variables)
        if token:
            headers.setdefault("Authorization", f"Bearer {token}")
    elif rec.auth_type == "basic":
        user = resolve(rec.auth_data.get("username", ""), variables)
        pw = resolve(rec.auth_data.get("password", ""), variables)
        if user or pw:
            token = base64.b64encode(f"{user}:{pw}".encode()).decode()
            headers.setdefault("Authorization", f"Basic {token}")
    elif rec.auth_type == "apikey":
        key = resolve(rec.auth_data.get("key", ""), variables)
        value = resolve(rec.auth_data.get("value", ""), variables)
        if key:
            headers.setdefault(key, value)

    # Body
    method_upper = rec.method.upper()
    if method_upper not in {"GET", "HEAD", "OPTIONS"} and rec.body_type != "none":
        body_resolved = resolve(rec.body, variables)
        if rec.body_type == "json":
            headers.setdefault("Content-Type", "application/json")
            kwargs["data"] = body_resolved.encode("utf-8")
        elif rec.body_type == "urlencoded":
            # Accept either `key=val&key2=val2` (the common form) or a JSON
            # array of {key, value} objects (for programmatic edits).
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            stripped = body_resolved.strip()
            if stripped.startswith("["):
                try:
                    pairs = json.loads(stripped)
                    kwargs["data"] = [(p.get("key", ""), p.get("value", "")) for p in pairs]
                except Exception:
                    kwargs["data"] = body_resolved.encode("utf-8")
            else:
                kwargs["data"] = body_resolved.encode("utf-8")
        elif rec.body_type == "raw":
            kwargs["data"] = body_resolved.encode("utf-8")
        else:
            kwargs["data"] = body_resolved.encode("utf-8")

    return url, kwargs


def execute(rec: RequestRecord, variables: dict[str, str]) -> ResponseData:
    """Synchronously run a request and capture everything we want to display.

    Intended to be called from a Qt worker thread (see `app.workers`). Any
    network / parsing exception is converted into a `ResponseData(ok=False)`
    so the UI never has to deal with bare `Exception` objects."""
    try:
        url, kwargs = _build_kwargs(rec, variables)
    except ValueError as e:
        log.warning("rejected request: %s", e)
        return ResponseData(ok=False, error=str(e))

    log.info("→ %s %s", rec.method.upper(), url)
    log.debug("headers=%s params=%s body_type=%s auth=%s",
              {k: v for k, v in kwargs.get("headers", {}).items()},
              kwargs.get("params"), rec.body_type, rec.auth_type)
    start = time.perf_counter()
    try:
        resp = requests.request(rec.method.upper(), url, **kwargs)
    except RequestException as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        log.error("✗ network error after %d ms: %s", elapsed, e)
        return ResponseData(ok=False, error=f"{type(e).__name__}: {e}", duration_ms=elapsed)
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        log.exception("✗ unexpected error after %d ms", elapsed)
        return ResponseData(ok=False, error=f"Unexpected: {e}", duration_ms=elapsed)

    elapsed = int((time.perf_counter() - start) * 1000)
    log.info("← %s %s  →  %d %s  (%d ms, %d bytes)",
             rec.method.upper(), url, resp.status_code, resp.reason or "",
             elapsed, len(resp.content or b""))
    body_bytes = resp.content or b""
    try:
        body_text = body_bytes.decode(resp.encoding or "utf-8", errors="replace")
    except Exception:
        body_text = ""

    return ResponseData(
        ok=True,
        status_code=resp.status_code,
        reason=resp.reason or "",
        headers=dict(resp.headers),
        body_text=body_text,
        body_bytes=body_bytes,
        content_type=resp.headers.get("Content-Type", ""),
        duration_ms=elapsed,
        size_bytes=len(body_bytes),
        final_url=resp.url,
    )
