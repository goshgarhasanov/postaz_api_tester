"""Variable substitution: {{var}} → environment value."""
from __future__ import annotations

import re

_VAR_PATTERN = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")


def resolve(text: str, variables: dict[str, str]) -> str:
    """Replace {{key}} occurrences with values from `variables`.
    Unknown placeholders are left untouched so users see them in the URL bar."""
    if not text or not variables:
        return text or ""

    def repl(match: re.Match) -> str:
        key = match.group(1)
        return str(variables.get(key, match.group(0)))

    return _VAR_PATTERN.sub(repl, text)


def resolve_all(data, variables: dict[str, str]):
    """Recursively resolve strings inside dict/list/scalar structures."""
    if isinstance(data, str):
        return resolve(data, variables)
    if isinstance(data, dict):
        return {k: resolve_all(v, variables) for k, v in data.items()}
    if isinstance(data, list):
        return [resolve_all(v, variables) for v in data]
    return data
