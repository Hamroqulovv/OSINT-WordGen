#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wordgen/utils.py — filesystem, logging and JSON helpers.

Visuals live in wordgen/ui.py; this module stays dependency-light so it can be
imported anywhere without pulling in the rich/pyfiglet stack.
"""
from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

APP_ROOT = Path.home() / ".osint_wordgen"
LOG_ROOT = APP_ROOT / "logs"


def _ensure_dirs() -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)


def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def make_session_log() -> Path:
    _ensure_dirs()
    return LOG_ROOT / f"session-{now_ts()}.log"


def setup_logger(logfile: Optional[Path]) -> logging.Logger:
    """
    File-only logger. Console feedback is handled by wordgen.ui so that the
    themed output never fights with plain log lines. Pass logfile=None to
    disable file logging entirely (--no-log).
    """
    logger = logging.getLogger("osint_wordgen")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logfile is not None:
        fh = logging.FileHandler(str(logfile), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
    else:
        logger.addHandler(logging.NullHandler())
    return logger


def save_last_wordlist(path: str) -> None:
    try:
        APP_ROOT.mkdir(parents=True, exist_ok=True)
        (APP_ROOT / "last_wordlist.txt").write_text(path + "\n", encoding="utf-8")
    except Exception:
        pass


def load_input_json(path: str) -> Dict[str, Any]:
    """Load an OSINT input profile from a JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be a top-level object (key/value pairs).")
    return data


def save_input_json(path: str, data: Dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
