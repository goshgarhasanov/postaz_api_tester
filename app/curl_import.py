"""Parse a `curl ...` command-line into a RequestRecord.

Handles the common flags used by the wild: -X, -H, -d/--data,
--data-raw, --data-urlencode, -u (basic auth), -b/--cookie, plus quoted args.
"""
from __future__ import annotations

import json
import shlex
from urllib.parse import parse_qsl, urlparse, urlunparse

from .database import RequestRecord
from .logger import get_logger

log = get_logger(__name__)


def parse_curl(command: str) -> RequestRecord:
    """Best-effort cURL → RequestRecord. Unknown flags are ignored.

    Normalises several flavours of cURL output:
      * Unix / macOS  — `\\<newline>` line continuations, single-quoted args
      * Chrome Windows — `^<newline>` continuations, `^"` escaped quotes,
                          `^^` literal carets. We strip these so shlex can
                          parse the result with normal POSIX rules.
      * PowerShell    — backtick line continuations are *not* expected here
                          (PowerShell wraps native curl differently).
    """
    cmd = command.strip()
    log.debug("cURL import: %d chars in", len(cmd))
    if not cmd:
        raise ValueError("Empty input")

    # 1. Normalise newlines.
    cmd = cmd.replace("\r\n", "\n")
    # 2. Unix backslash line continuation: `\<newline>` → space.
    cmd = cmd.replace("\\\n", " ")
    # 3. Chrome (Windows) caret continuation: `^<newline>` or `^<space><newline>` → space.
    cmd = cmd.replace("^\n", " ").replace("^ \n", " ")
    # 4. Chrome (Windows) caret-escaped quotes: `^"` → `"` so shlex sees real quotes.
    #    Do this AFTER stripping line continuations, otherwise the `^` that
    #    actually escapes a quote on the next line gets misread.
    cmd = cmd.replace('^"', '"')
    # 5. Double caret means a literal caret — collapse to a single one.
    cmd = cmd.replace("^^", "^")
    # 6. Any remaining lone carets (e.g. wrapping the entire body) are noise.
    cmd = cmd.replace(" ^ ", " ").replace("\t^\t", "\t")
    # 7. Collapse all remaining newlines into spaces.
    cmd = cmd.replace("\n", " ")
    # 8. Collapse runs of whitespace.
    cmd = " ".join(cmd.split())

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

    rec = RequestRecord(
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
    log.info("cURL parsed: %s %s (%d headers, %d params, body_type=%s, auth=%s)",
             rec.method, rec.url, len(rec.headers), len(rec.params), rec.body_type, rec.auth_type)
    return rec
