#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wordgen/strength.py — lightweight password-strength estimation.

Used purely to give the operator a feel for the variety of candidates the
engine produced (length / character classes / rough entropy). It is a fast
character-pool entropy heuristic, not a substitute for zxcvbn-style analysis.
"""
from __future__ import annotations

import math
from typing import Tuple

_SYMBOLS = set("!@#$%^&*()-_+=[]{};:,.<>?/\\|~`'\"")


def estimate(pw: str) -> Tuple[int, str, float]:
    """Return (score 0-5, label, entropy_bits) for a candidate string."""
    if not pw:
        return 0, "empty", 0.0

    pool = 0
    if any(c.islower() for c in pw):
        pool += 26
    if any(c.isupper() for c in pw):
        pool += 26
    if any(c.isdigit() for c in pw):
        pool += 10
    if any(c in _SYMBOLS for c in pw):
        pool += 32
    if any(ord(c) > 127 for c in pw):
        pool += 40
    pool = max(pool, 2)

    bits = len(pw) * math.log2(pool)

    if bits < 28:
        return 1, "very weak", bits
    if bits < 40:
        return 2, "weak", bits
    if bits < 60:
        return 3, "fair", bits
    if bits < 80:
        return 4, "strong", bits
    return 5, "very strong", bits
