"""Application-wide logging.

Two destinations are configured at startup:

  * Rotating file at  <data_dir>/postaz.log    (DEBUG and up, kept across runs)
  * Console (stderr)                            (INFO and up, useful for `python main.py`)

Levels we use across modules:
  DEBUG    — verbose internals (SQL params, parsed cURL tokens, payload sizes)
  INFO     — meaningful user-facing events (request sent, saved, env switched)
  WARNING  — recoverable oddities (unknown auth scheme, history truncation)
  ERROR    — failed operations (HTTP error response, parse failure)
  CRITICAL — only if the app itself can't continue

Get a module-scoped logger via `get_logger(__name__)`. Every record carries
the module path so the file is easy to grep:

    2026-05-15 14:22:08 [INFO   ] postaz.http_client  | POST https://api.example.com/x → 201 (412 ms, 1.2 KB)
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)-22s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

# ANSI codes for the console handler — looks nice in modern terminals, harmless
# everywhere else (Windows 10+ enables ANSI in the default console).
_COLORS = {
    "DEBUG":    "\033[38;5;244m",  # dim grey
    "INFO":     "\033[38;5;75m",   # blue
    "WARNING":  "\033[38;5;214m",  # orange
    "ERROR":    "\033[38;5;203m",  # red
    "CRITICAL": "\033[48;5;203m\033[38;5;231m",  # white on red
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    """Console formatter — wraps level name in ANSI colors."""

    def format(self, record: logging.LogRecord) -> str:
        original_level = record.levelname
        color = _COLORS.get(original_level, "")
        if color:
            record.levelname = f"{color}{original_level:<7}{_RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original_level


_initialized = False


def setup_logging(data_dir: Path, console_level: int = logging.INFO) -> Path:
    """Idempotently configure the `postaz` logger tree.

    Safe to call multiple times — second and later calls are no-ops so the
    log file isn't rotated open-on-open by accident."""
    global _initialized
    log_path = data_dir / "postaz.log"
    if _initialized:
        return log_path

    data_dir.mkdir(parents=True, exist_ok=True)

    # File handler — DEBUG level, rotated at 2 MB, three backups kept.
    file_handler = RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))

    # Console handler — coloured, configurable level (default INFO).
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(console_level)
    console.setFormatter(_ColorFormatter(_FORMAT, _DATEFMT))

    root = logging.getLogger("postaz")
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console)
    root.propagate = False

    _initialized = True
    root.info("==== postaz session started ====")
    return log_path


def get_logger(name: str) -> logging.Logger:
    """Module-scoped logger.

    Pass `__name__`; the helper strips the project prefix so logs read as
    `postaz.<module>` regardless of how the import path is spelled."""
    short = name.split(".")[-1] if name else "app"
    if name.startswith("app."):
        short = name[4:]                     # `app.ui.sidebar` → `ui.sidebar`
    elif name.startswith("postaz."):
        short = name[7:]
    return logging.getLogger(f"postaz.{short}")


def log_path() -> Path | None:
    """Return the active log file path, or None if logging hasn't been set up."""
    root = logging.getLogger("postaz")
    for handler in root.handlers:
        if isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename)
    return None
