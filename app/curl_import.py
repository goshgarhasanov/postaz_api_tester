"""Parse a `curl ...` command-line into a RequestRecord.

Handles the common flags used by the wild: -X, -H, -d/--data,
--data-raw, --data-urlencode, -u (basic auth), -b/--cookie, plus quoted args.
"""
from __future__ import annotations

import json
import shlex
from urllib.parse import parse_qsl, urlparse, urlunparse

from .database import RequestRecord


def parse_curl(command: str) -> RequestRecord:
    """Best-effort cURL → RequestRecord. Unknown flags are ignored."""
    cmd = command.strip()
    if not cmd:
        raise ValueError("Empty input")

    # Normalize: collapse line continuations
    cmd = cmd.replace("\r\n", "\n").replace("\\\n", " ").replace("\n", " ")

    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError as e:
        raise ValueError(f"Could not parse: {e}") from e

    if not tokens or tokens[0].lower() != "curl":
        if tokens and tokens[0].lower().endswith("curl"):
            pass
        else:
            raise ValueError("Expected the command to start with 'curl'.")

    tokens = tokens[1:]
    method: str | None = None
    url: str | None = None
    headers: list[dict] = []
    params: list[dict] = []
    body_parts: list[str] = []
    body_type = "none"
    auth_type = "none"
    auth_data: dict[str, str] = {}

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        low = tok.lower()

        if low in ("-x", "--request"):
            method = nxt.upper()
            i += 2
        elif low in ("-h", "--header"):
            if ":" in nxt:
                k, _, v = nxt.partition(":")
                headers.append({"enabled": True, "key": k.strip(), "value": v.strip(), "description": ""})
            i += 2
        elif low in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii"):
            body_parts.append(nxt)
            if method is None:
                method = "POST"
            i += 2
        elif low == "--data-urlencode":
            body_parts.append(nxt)
            body_type = "urlencoded"
            if method is None:
                method = "POST"
            i += 2
        elif low in ("-u", "--user"):
            user, _, pw = nxt.partition(":")
            auth_type = "basic"
            auth_data = {"username": user, "password": pw}
            i += 2
        elif low in ("-b", "--cookie"):
            headers.append({"enabled": True, "key": "Cookie", "value": nxt, "description": ""})
            i += 2
        elif low in ("--url",):
            url = nxt
            i += 2
        elif low.startswith("--compressed") or low in ("-k", "--insecure", "-L", "--location", "-s", "--silent", "-v"):
            i += 1
        elif low in ("-A", "--user-agent"):
            headers.append({"enabled": True, "key": "User-Agent", "value": nxt, "description": ""})
            i += 2
        elif low in ("-e", "--referer"):
            headers.append({"enabled": True, "key": "Referer", "value": nxt, "description": ""})
            i += 2
        elif tok.startswith("-"):
            # unknown flag — skip with its value if it looks like it takes one
            if nxt and not nxt.startswith("-"):
                i += 2
            else:
                i += 1
        else:
            if url is None:
                url = tok
            i += 1

    if not url:
        raise ValueError("No URL found in cURL command.")

    # Strip surrounding $'…' or quotes that shlex may have already removed
    url = url.strip().strip("'\"")

    # Promote query string into params table
    parsed = urlparse(url)
    if parsed.query:
        for k, v in parse_qsl(parsed.query, keep_blank_values=True):
            params.append({"enabled": True, "key": k, "value": v, "description": ""})
        url = urlunparse(parsed._replace(query=""))

    # Body inference
    body = "&".join(body_parts) if body_parts else ""
    if body and body_type == "none":
        sample = body.lstrip()
        if sample.startswith("{") or sample.startswith("["):
            body_type = "json"
            try:
                body = json.dumps(json.loads(body), indent=2, ensure_ascii=False)
            except Exception:
                pass
        else:
            body_type = "raw"

    return RequestRecord(
        name="Imported request",
        method=(method or "GET").upper(),
        url=url,
        headers=headers,
        params=params,
        body=body,
        body_type=body_type,
        auth_type=auth_type,
        auth_data=auth_data,
    )
