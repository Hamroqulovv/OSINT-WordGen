#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wordgen/generator.py

Professional OSINT Wordlist generation engine.
- Streaming generator (yield) so it can write to disk progressively.
- Many realistic transformations: leet, case-mix, insert digits/symbols,
  random separators, years, permutations of tokens, targeted friend/company combos,
  and "human-like" randomness (not simple sequential dumps).
- Configurable caps to avoid combinatorial explosion.
"""

from __future__ import annotations
import re
import itertools
import datetime
import string
import secrets
from typing import Dict, List, Generator, Iterable, Set, Any, Optional

# -----------------------------------------------------------
# Configuration: tweak these for different behaviour/size
# -----------------------------------------------------------
DEFAULT_MAX_WORDS = 200_000
MAX_LEET_PER_TOKEN = 12         # how many leet variants to produce per token
MAX_COMBINATIONS = 3            # up to 3-token permutations
MAX_ADDITIONAL_INSERTS = 3      # max inserted numbers/symbols blocks per candidate
SYMBOLS = list("!@#$%^&*()-_+=[]{};:,.<>?/\\|")  # pool of symbols to insert
DIGITS = list("0123456789")
COMMON_SUFFIXES = ["123","1234","12345","2020","2021","2022","2023","2024","007"]
COMMON_PREFIXES = ["!", "#", "@", "*"]
KEYBOARD_ADJ = ["qwerty","asdf","zxcv","123qwe","qaz"]
# Probability weights for inserting patterns (0..1)
P_INSERT_SYMBOL_BLOCK = 0.45
P_INSERT_DIGIT_BLOCK = 0.55
P_LEET_CHANGE = 0.35
P_MIX_CASE = 0.65
P_JOIN_WITH_SYMBOL = 0.45
# Limit how many outputs per base token to avoid explosion
MAX_VARIANTS_PER_BASE = 50

# LEET mapping (common)
LEET_MAP = {
    "a": ["4","@"],
    "b": ["8"],
    "e": ["3"],
    "i": ["1","!"],
    "l": ["1","|"],
    "o": ["0"],
    "s": ["5","$"],
    "t": ["7"],
    "g": ["9"],
    "z": ["2"]
}

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
    out = []
    try:
        a = int(age)
        this = datetime.datetime.now().year
        birth = this - a
        out += [str(birth), str(birth)[-2:], str(birth-1), str(birth+1)]
    except Exception:
        pass
    return out

def unique_preserve_order(seq: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out

# safe random choice using secrets for unpredictability
def rnd_choice(seq: List[Any]) -> Any:
    return secrets.choice(seq)

def rnd_choices(seq: List[Any], k: int) -> List[Any]:
    return [secrets.choice(seq) for _ in range(k)]

# -----------------------------------------------------------
# Variant generators
# -----------------------------------------------------------

def case_variants(token: str) -> Iterable[str]:
    """Return common case variations: lower, upper, capitalized, alt caps."""
    if not token:
        return
    yield token.lower()
    yield token.upper()
    yield token.capitalize()
    # mixed-case patterns: e.g. JoHn
    if len(token) >= 3:
        # random-ish mixed-case patterns deterministic (but we yield a few)
        yield token[:1].upper() + token[1:].lower()
        mid = token[0:2].upper() + token[2:].lower()
        yield mid

def leet_variants(token: str, max_out: int = MAX_LEET_PER_TOKEN) -> Iterable[str]:
    """Produce leet substitutions limited to max_out variants."""
    if not token:
        return
    token_low = token.lower()
    positions = [i for i,ch in enumerate(token_low) if ch in LEET_MAP]
    yielded = set()

    # always include original
    yielded.add(token)
    yield token

    # single substitutions
    for i in positions:
        for sub in LEET_MAP[token_low[i]]:
            arr = list(token)
            arr[i] = sub
            out = "".join(arr)
            if out not in yielded:
                yielded.add(out)
                yield out
            # capitalized variant
            yield out.capitalize() if len(out) > 1 else out

    # double substitutions (combinatorial limited)
    if len(positions) >= 2:
        combos = itertools.combinations(positions, 2)
        for i1,i2 in combos:
            for a in LEET_MAP[token_low[i1]]:
                for b in LEET_MAP[token_low[i2]]:
                    arr = list(token)
                    arr[i1] = a; arr[i2] = b
                    out = "".join(arr)
                    if out not in yielded:
                        yielded.add(out)
                        yield out
    # cap
    count = 0
    for v in list(yielded):
        count += 1
        if count >= max_out:
            break

def random_case_token(token: str) -> str:
    """Randomly mix capitalization in a human-like way."""
    if not token:
        return token
    chars = []
    for c in token:
        if secrets.randbelow(100) < 35:
            chars.append(c.upper())
        else:
            chars.append(c.lower())
    return "".join(chars)

def insert_symbol_block(base: str, count: int=1) -> str:
    """Insert `count` symbol block(s) at random positions (start/mid/end)."""
    if not base:
        base = ""
    for _ in range(count):
        block_len = secrets.choice([1,2,3])
        block = "".join(rnd_choices(SYMBOLS, block_len))
        pos = secrets.choice(['start','end','mid'])
        if pos == 'start':
            base = block + base
        elif pos == 'end':
            base = base + block
        else:
            mid = secrets.randbelow(max(1, len(base)))
            base = base[:mid] + block + base[mid:]
    return base

def insert_digit_block(base: str, count: int=1) -> str:
    """Insert digit block(s) similarly."""
    if not base:
        base = ""
    for _ in range(count):
        block_len = secrets.choice([1,2,3,4])
        block = "".join(rnd_choices(DIGITS, block_len))
        pos = secrets.choice(['start','end','mid'])
        if pos == 'start':
            base = block + base
        elif pos == 'end':
            base = base + block
        else:
            mid = secrets.randbelow(max(1, len(base)))
            base = base[:mid] + block + base[mid:]
    return base

def join_with_random_separator(parts: List[str]) -> str:
    """Join small list of parts with either nothing or a random separator symbol."""
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    sep_choices = ["", "", "", "-", "_", ".", "", rnd_choice(SYMBOLS)]
    sep = rnd_choice(sep_choices)
    return sep.join(parts)

# -----------------------------------------------------------
# High-level generation pipeline
# -----------------------------------------------------------

def build_base_parts(inputs: Dict[str, Any]) -> List[str]:
    """Extract tokens from inputs and normalize them into a parts list."""
    parts: List[str] = []
    for k in ("first","last","middle","nickname"):
        v = inputs.get(k)
        if v:
            v = normalize(str(v))
            if v:
                parts.append(slug(v))
                parts.append(v)
    # phone -> digits, last4, first3
    p = inputs.get("phone")
    if p:
        digits = re.sub(r"\D", "", str(p))
        if digits:
            parts.append(digits)
            if len(digits) >= 4:
                parts.append(digits[-4:])
            parts.append(digits[:3])
    # address tokens
    addr = inputs.get("address")
    if addr:
        for t in re.split(r"[,\\s/\\\\]+", str(addr)):
            if t:
                parts.append(slug(t))
    # friends
    for f in (inputs.get("friends") or []):
        if f:
            parts.append(slug(f))
            parts.append(normalize(str(f)))
    # company/pet/hobby
    for k in ("company","pet","hobby"):
        v = inputs.get(k)
        if v:
            parts.append(slug(v))
    # domain/email
    email = inputs.get("email")
    if email:
        local = str(email).split("@")[0]
        parts.append(local)
    domain = inputs.get("domain")
    if domain:
        parts.append(domain)
        if str(domain).startswith("www."):
            parts.append(str(domain)[4:])
    # years
    years = set()
    age = inputs.get("age")
    if age:
        for y in generate_years_from_age(str(age)):
            years.add(y)
    for k in ("birth_year","year"):
        v = inputs.get(k)
        if v:
            years.add(str(v))
    for y in years:
        parts.append(y)
    # dedupe preserve-order
    return unique_preserve_order(parts)

# -----------------------------------------------------------
# Candidate generation (streaming)
# -----------------------------------------------------------

def generate_wordlist_stream(inputs: Dict[str, Any], max_words: int = DEFAULT_MAX_WORDS, seed: Optional[int] = None) -> Generator[str, None, None]:
    """
    Stream realistic password candidates. Stops when max_words reached.
    Uses probabilistic insertion of digits/symbols and many variants.
    """
    # Optional seed for reproducibility (not cryptographically secure)
    if seed is not None:
        import random
        random.seed(seed)
    parts = build_base_parts(inputs)
    if not parts:
        return

    written = 0

    # Stage 1: single-token rich variants
    for token in parts:
        if written >= max_words:
            return
        # case variants
        for v in case_variants(token):
            yield v
            written += 1
            if written >= max_words:
                return
        # random mixed-case variant
        if secrets.randbelow(100) < int(P_MIX_CASE*100):
            mv = random_case_token(token)
            yield mv
            written += 1
            if written >= max_words:
                return
        # leet variants (some)
        if secrets.randbelow(100) < int(P_LEET_CHANGE*100):
            for lv in leet_variants(token, max_out=MAX_LEET_PER_TOKEN):
                yield lv
                written += 1
                if written >= max_words:
                    return
        # suffix/prefix basics
        for suf in COMMON_SUFFIXES:
            cand = token + suf
            yield cand
            written += 1
            if written >= max_words:
                return
        for pre in COMMON_PREFIXES:
            cand = pre + token
            yield cand
            written += 1
            if written >= max_words:
                return

    # Stage 2: permutations of tokens (1..MAX_COMBINATIONS) with mangling
    # We'll prioritize smaller permutations first (2-token combos) and produce realistic mixes.
    for r in range(2, min(MAX_COMBINATIONS, len(parts)) + 1):
        # iterate permutations but limit total produced by early break if max reached
        for combo in itertools.permutations(parts, r):
            if written >= max_words:
                return
            # join with random separator sometimes
            joined = join_with_random_separator(list(combo))
            # produce case variants
            for v in case_variants(joined):
                yield v
                written += 1
                if written >= max_words:
                    return
            # maybe produce leet
            if secrets.randbelow(100) < int(P_LEET_CHANGE*100):
                for lv in leet_variants(joined, max_out=8):
                    yield lv
                    written += 1
                    if written >= max_words:
                        return
            # randomly insert symbols/digits blocks
            inserts = secrets.randbelow(MAX_ADDITIONAL_INSERTS + 1)  # 0..MAX_ADDITIONAL_INSERTS
            if inserts:
                # alternate insertion types
                cur = joined
                for _ in range(inserts):
                    if secrets.randbelow(100) < int(P_INSERT_SYMBOL_BLOCK*100):
                        cur = insert_symbol_block(cur, count=1)
                    else:
                        cur = insert_digit_block(cur, count=1)
                    yield cur
                    written += 1
                    if written >= max_words:
                        return
            # suffixes & prefixes
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
            # keyboard adjacency appends
            for kbd in KEYBOARD_ADJ[:2]:
                yield joined + kbd
                written += 1
                if written >= max_words:
                    return

    # Stage 3: friend/company targeted combos and email-like patterns
    friends = inputs.get("friends") or []
    company = inputs.get("company") or ""
    for f in friends:
        if written >= max_words:
            return
        for main in (inputs.get("first") or "", inputs.get("last") or "", company):
            if not main or not f:
                continue
            combo = slug(main) + slug(f)
            # common combinations user might choose
            variants = [combo, combo + "123", combo + "!" , combo + secrets.choice(DIGITS)]
            for v in variants:
                yield v
                written += 1
                if written >= max_words:
                    return
            # leet & symbol variants
            if secrets.randbelow(100) < 50:
                for lv in leet_variants(combo, max_out=6):
                    yield lv
                    written += 1
                    if written >= max_words:
                        return

    # Stage 4: fallback churn: repeat tokens, mirrored, interleaved digits
    for p in parts:
        if written >= max_words:
            return
        # repeat, mirrored
        yield p + p
        written += 1
        if written >= max_words:
            return
        yield p[::-1]  # reversed token
        written += 1
        if written >= max_words:
            return
        # insert small numbers
        yield p + secrets.choice(DIGITS)
        written += 1
        if written >= max_words:
            return

    # done
    return
