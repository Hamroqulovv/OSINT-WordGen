#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wordgen/generator.py — OSINT wordlist generation engine.

Design goals
------------
* Streaming (yield) so candidates can be written to disk progressively.
* Human-like transformations: leet, case-mixing, digit/symbol insertion,
  random separators, birth years, token permutations and targeted
  friend/company combos — not simple sequential dumps.
* Configurable caps to avoid combinatorial explosion.
* Optional reproducibility via --seed while defaulting to secrets-grade
  randomness for real, unpredictable variety.
* A thin `stream_unique()` wrapper adds global de-duplication, length
  filtering and run statistics on top of the raw stream.
"""
from __future__ import annotations

import datetime
import itertools
import random as _random
import re
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Generator, Iterable, List, Optional, Set

# -----------------------------------------------------------
# Configuration
# -----------------------------------------------------------
DEFAULT_MAX_WORDS = 200_000
MAX_LEET_PER_TOKEN = 12
MAX_COMBINATIONS = 3
MAX_ADDITIONAL_INSERTS = 3
SYMBOLS = list("!@#$%^&*()-_+=[]{};:,.<>?/\\|")
DIGITS = list("0123456789")
COMMON_SUFFIXES = [
    "123", "1234", "12345", "2020", "2021", "2022", "2023", "2024", "2025",
    "007", "!", "@", "1", "01", "69", "777", "000", "99", "12", "321",
]
COMMON_PREFIXES = ["!", "#", "@", "*", "1"]
KEYBOARD_ADJ = ["qwerty", "asdf", "zxcv", "123qwe", "qaz"]

# Probability weights (0..1)
P_INSERT_SYMBOL_BLOCK = 0.45
P_INSERT_DIGIT_BLOCK = 0.55
P_LEET_CHANGE = 0.35
P_MIX_CASE = 0.65

# De-dup safety: stop tracking seen items past this many to bound memory.
DEDUP_CAP = 5_000_000
# Over-scan factor: how many raw candidates to pull per requested unique one.
OVERSCAN = 6

LEET_MAP = {
    "a": ["4", "@"],
    "b": ["8"],
    "e": ["3"],
    "i": ["1", "!"],
    "l": ["1", "|"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7"],
    "g": ["9"],
    "z": ["2"],
}

# -----------------------------------------------------------
# Randomness (seedable, defaults to secrets)
# -----------------------------------------------------------
_RNG: Optional[_random.Random] = None


def set_seed(seed: Optional[int]) -> None:
    """Seed the engine for reproducible output, or None for secrets-grade."""
    global _RNG
    _RNG = _random.Random(seed) if seed is not None else None


def rnd_below(n: int) -> int:
    if n <= 0:
        return 0
    return _RNG.randrange(n) if _RNG is not None else secrets.randbelow(n)


def rnd_choice(seq: List[Any]) -> Any:
    return _RNG.choice(seq) if _RNG is not None else secrets.choice(seq)


def rnd_choices(seq: List[Any], k: int) -> List[Any]:
    return [rnd_choice(seq) for _ in range(k)]


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------
def slug(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", "", s)


def normalize(tok: str) -> str:
    return tok.strip()


def generate_years_from_age(age: str) -> List[str]:
    out: List[str] = []
    try:
        a = int(age)
        this = datetime.datetime.now().year
        birth = this - a
        out += [str(birth), str(birth)[-2:], str(birth - 1), str(birth + 1)]
    except Exception:
        pass
    return out


def unique_preserve_order(seq: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# -----------------------------------------------------------
# Variant generators
# -----------------------------------------------------------
def case_variants(token: str) -> Iterable[str]:
    """Common case variations: lower, upper, capitalized, alt caps."""
    if not token:
        return
    yield token.lower()
    yield token.upper()
    yield token.capitalize()
    if len(token) >= 3:
        yield token[:1].upper() + token[1:].lower()
        yield token[0:2].upper() + token[2:].lower()


def leet_variants(token: str, max_out: int = MAX_LEET_PER_TOKEN) -> Iterable[str]:
    """Leet substitutions, limited to roughly max_out variants."""
    if not token:
        return
    token_low = token.lower()
    positions = [i for i, ch in enumerate(token_low) if ch in LEET_MAP]
    yielded: Set[str] = {token}
    produced = 0
    yield token
    produced += 1

    for i in positions:
        for sub in LEET_MAP[token_low[i]]:
            arr = list(token)
            arr[i] = sub
            out = "".join(arr)
            if out not in yielded:
                yielded.add(out)
                yield out
                produced += 1
                if produced >= max_out:
                    return

    if len(positions) >= 2:
        for i1, i2 in itertools.combinations(positions, 2):
            for a in LEET_MAP[token_low[i1]]:
                for b in LEET_MAP[token_low[i2]]:
                    arr = list(token)
                    arr[i1] = a
                    arr[i2] = b
                    out = "".join(arr)
                    if out not in yielded:
                        yielded.add(out)
                        yield out
                        produced += 1
                        if produced >= max_out:
                            return


def random_case_token(token: str) -> str:
    """Randomly mix capitalization in a human-like way."""
    if not token:
        return token
    return "".join(c.upper() if rnd_below(100) < 35 else c.lower() for c in token)


def insert_symbol_block(base: str, count: int = 1) -> str:
    base = base or ""
    for _ in range(count):
        block = "".join(rnd_choices(SYMBOLS, rnd_choice([1, 2, 3])))
        pos = rnd_choice(["start", "end", "mid"])
        if pos == "start":
            base = block + base
        elif pos == "end":
            base = base + block
        else:
            mid = rnd_below(max(1, len(base)))
            base = base[:mid] + block + base[mid:]
    return base


def insert_digit_block(base: str, count: int = 1) -> str:
    base = base or ""
    for _ in range(count):
        block = "".join(rnd_choices(DIGITS, rnd_choice([1, 2, 3, 4])))
        pos = rnd_choice(["start", "end", "mid"])
        if pos == "start":
            base = block + base
        elif pos == "end":
            base = base + block
        else:
            mid = rnd_below(max(1, len(base)))
            base = base[:mid] + block + base[mid:]
    return base


def join_with_random_separator(parts: List[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    sep_choices = ["", "", "", "-", "_", ".", "", rnd_choice(SYMBOLS)]
    return rnd_choice(sep_choices).join(parts)


# -----------------------------------------------------------
# Base token extraction
# -----------------------------------------------------------
def build_base_parts(inputs: Dict[str, Any]) -> List[str]:
    """Extract and normalize tokens from OSINT inputs into a parts list."""
    parts: List[str] = []
    for k in ("first", "last", "middle", "nickname"):
        v = inputs.get(k)
        if v:
            v = normalize(str(v))
            if v:
                parts.append(slug(v))
                parts.append(v)

    p = inputs.get("phone")
    if p:
        digits = re.sub(r"\D", "", str(p))
        if digits:
            parts.append(digits)
            if len(digits) >= 4:
                parts.append(digits[-4:])
            parts.append(digits[:3])

    addr = inputs.get("address")
    if addr:
        for t in re.split(r"[,\s/\\]+", str(addr)):
            if t:
                parts.append(slug(t))

    for f in (inputs.get("friends") or []):
        if f:
            parts.append(slug(f))
            parts.append(normalize(str(f)))

    for k in ("company", "pet", "hobby"):
        v = inputs.get(k)
        if v:
            parts.append(slug(v))

    email = inputs.get("email")
    if email:
        parts.append(str(email).split("@")[0])

    domain = inputs.get("domain")
    if domain:
        parts.append(str(domain))
        if str(domain).startswith("www."):
            parts.append(str(domain)[4:])

    years: Set[str] = set()
    age = inputs.get("age")
    if age:
        for y in generate_years_from_age(str(age)):
            years.add(y)
    for k in ("birth_year", "year"):
        v = inputs.get(k)
        if v:
            years.add(str(v))
    # sorted() keeps token order deterministic across processes so that
    # --seed yields byte-identical wordlists (set iteration order is not).
    parts.extend(sorted(years))

    return unique_preserve_order(parts)


def has_usable_inputs(inputs: Dict[str, Any]) -> bool:
    return bool(build_base_parts(inputs))


# -----------------------------------------------------------
# Raw candidate stream
# -----------------------------------------------------------
def generate_wordlist_stream(
    inputs: Dict[str, Any],
    max_words: int = DEFAULT_MAX_WORDS,
    seed: Optional[int] = None,
) -> Generator[str, None, None]:
    """Stream realistic password candidates (may contain duplicates)."""
    if seed is not None:
        set_seed(seed)

    parts = build_base_parts(inputs)
    if not parts:
        return

    written = 0

    # Stage 1: single-token rich variants
    for token in parts:
        if written >= max_words:
            return
        for v in case_variants(token):
            yield v
            written += 1
            if written >= max_words:
                return
        if rnd_below(100) < int(P_MIX_CASE * 100):
            yield random_case_token(token)
            written += 1
            if written >= max_words:
                return
        if rnd_below(100) < int(P_LEET_CHANGE * 100):
            for lv in leet_variants(token, max_out=MAX_LEET_PER_TOKEN):
                yield lv
                written += 1
                if written >= max_words:
                    return
        for suf in COMMON_SUFFIXES:
            yield token + suf
            written += 1
            if written >= max_words:
                return
        for pre in COMMON_PREFIXES:
            yield pre + token
            written += 1
            if written >= max_words:
                return

    # Stage 2: permutations of tokens with mangling
    for r in range(2, min(MAX_COMBINATIONS, len(parts)) + 1):
        for combo in itertools.permutations(parts, r):
            if written >= max_words:
                return
            joined = join_with_random_separator(list(combo))
            for v in case_variants(joined):
                yield v
                written += 1
                if written >= max_words:
                    return
            if rnd_below(100) < int(P_LEET_CHANGE * 100):
                for lv in leet_variants(joined, max_out=8):
                    yield lv
                    written += 1
                    if written >= max_words:
                        return
            inserts = rnd_below(MAX_ADDITIONAL_INSERTS + 1)
            if inserts:
                cur = joined
                for _ in range(inserts):
                    if rnd_below(100) < int(P_INSERT_SYMBOL_BLOCK * 100):
                        cur = insert_symbol_block(cur, count=1)
                    else:
                        cur = insert_digit_block(cur, count=1)
                    yield cur
                    written += 1
                    if written >= max_words:
                        return
            for suf in COMMON_SUFFIXES[:3]:
                yield joined + suf
                written += 1
                if written >= max_words:
                    return
            for pre in COMMON_PREFIXES[:2]:
                yield pre + joined
                written += 1
                if written >= max_words:
                    return
            for kbd in KEYBOARD_ADJ[:2]:
                yield joined + kbd
                written += 1
                if written >= max_words:
                    return

    # Stage 3: friend/company targeted combos
    friends = inputs.get("friends") or []
    company = inputs.get("company") or ""
    for f in friends:
        if written >= max_words:
            return
        for main in (inputs.get("first") or "", inputs.get("last") or "", company):
            if not main or not f:
                continue
            combo = slug(main) + slug(f)
            for v in (combo, combo + "123", combo + "!", combo + rnd_choice(DIGITS)):
                yield v
                written += 1
                if written >= max_words:
                    return
            if rnd_below(100) < 50:
                for lv in leet_variants(combo, max_out=6):
                    yield lv
                    written += 1
                    if written >= max_words:
                        return

    # Stage 4: fallback churn — doubled, reversed, digit-appended
    for p in parts:
        if written >= max_words:
            return
        yield p + p
        written += 1
        if written >= max_words:
            return
        yield p[::-1]
        written += 1
        if written >= max_words:
            return
        yield p + rnd_choice(DIGITS)
        written += 1
        if written >= max_words:
            return


# -----------------------------------------------------------
# Unique / filtered stream with statistics
# -----------------------------------------------------------
@dataclass
class GenStats:
    raw: int = 0
    written: int = 0
    duplicates: int = 0
    too_short: int = 0
    too_long: int = 0
    min_len_seen: int = 0
    max_len_seen: int = 0
    total_chars: int = 0
    dedup_disabled: bool = False

    @property
    def avg_len(self) -> float:
        return self.total_chars / self.written if self.written else 0.0


def stream_unique(
    inputs: Dict[str, Any],
    max_words: int = DEFAULT_MAX_WORDS,
    min_len: int = 1,
    max_len: int = 128,
    dedup: bool = True,
    seed: Optional[int] = None,
    stats: Optional[GenStats] = None,
) -> Generator[str, None, None]:
    """
    Yield up to `max_words` candidates, optionally de-duplicated and length
    filtered. Populates `stats` (create one and pass it in to read results).
    """
    if stats is None:
        stats = GenStats()

    set_seed(seed)
    seen: Set[str] = set()
    dedup_active = dedup
    internal_cap = max_words if not dedup else min(max_words * OVERSCAN, max_words + 3_000_000)

    for pw in generate_wordlist_stream(inputs, max_words=internal_cap, seed=None):
        stats.raw += 1
        length = len(pw)
        if length < min_len:
            stats.too_short += 1
            continue
        if length > max_len:
            stats.too_long += 1
            continue
        if dedup_active:
            if pw in seen:
                stats.duplicates += 1
                continue
            seen.add(pw)
            if len(seen) >= DEDUP_CAP:
                dedup_active = False
                stats.dedup_disabled = True
                seen.clear()

        stats.written += 1
        stats.total_chars += length
        stats.min_len_seen = length if stats.min_len_seen == 0 else min(stats.min_len_seen, length)
        stats.max_len_seen = max(stats.max_len_seen, length)
        yield pw
        if stats.written >= max_words:
            return
