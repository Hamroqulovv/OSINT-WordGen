#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — OSINT WordGen v2 (professional entrypoint)

Interactive, Matrix-themed OSINT password wordlist generator for authorized
security testing. Collects target OSINT data (interactively or from a JSON
profile), requires an explicit authorization acknowledgement, then streams
de-duplicated, length-filtered password candidates to disk with a live
progress bar and a session log.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Make sure ANSI/VT colors work on Windows terminals before anything prints.
try:
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except Exception:  # pragma: no cover - colorama is optional at runtime
    pass

from wordgen import ui
from wordgen.generator import DEFAULT_MAX_WORDS, GenStats, has_usable_inputs, stream_unique
from wordgen.strength import estimate
from wordgen.utils import (
    load_input_json,
    make_session_log,
    save_input_json,
    save_last_wordlist,
    setup_logger,
)

AUTH_PHRASE = "I HAVE AUTHORIZATION"

DISCLAIMER = (
    "This tool generates password candidates from OSINT data for AUTHORIZED\n"
    "security testing only — pentests, red-team engagements, password audits.\n"
    "You must have explicit, written permission for any target you assess.\n"
    "Unauthorized use against systems or accounts you do not own is illegal\n"
    "and is solely your responsibility."
)

# (label shown to operator, inputs key, is_list)
FIELDS: List[Tuple[str, str, bool]] = [
    ("First name", "first", False),
    ("Last name", "last", False),
    ("Middle name", "middle", False),
    ("Nickname", "nickname", False),
    ("Phone (e.g. +998901234567)", "phone", False),
    ("Address / City", "address", False),
    ("Age (years)", "age", False),
    ("Close friends (comma separated)", "friends", True),
    ("Company / Organization", "company", False),
    ("Pet name", "pet", False),
    ("Hobby", "hobby", False),
    ("Birth year", "birth_year", False),
    ("Email", "email", False),
    ("Domain", "domain", False),
]

SAMPLE_COUNT = 12


# --------------------------------------------------------------------------
# Args
# --------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="osint-wordgen",
        description="OSINT-based password wordlist generator (authorized testing only).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python main.py                         interactive run\n"
            "  python main.py -i simple_input.json    load target from JSON\n"
            "  python main.py -m 50000 --min-len 8    cap size, drop short pws\n"
            "  python main.py -o out/list.txt --seed 42 --no-animation\n"
        ),
    )
    p.add_argument("-o", "--output", default="output/wordlist.txt",
                   help="Output wordlist file (default: output/wordlist.txt)")
    p.add_argument("-m", "--max-words", type=int, default=DEFAULT_MAX_WORDS,
                   help=f"Max unique candidates (default: {DEFAULT_MAX_WORDS})")
    p.add_argument("-i", "--input", metavar="FILE",
                   help="Load OSINT inputs from a JSON profile (skips prompts)")
    p.add_argument("--save-input", metavar="FILE",
                   help="Save the collected OSINT inputs to a JSON file")
    p.add_argument("--min-len", type=int, default=1, help="Drop candidates shorter than N")
    p.add_argument("--max-len", type=int, default=128, help="Drop candidates longer than N")
    p.add_argument("--no-dedup", action="store_true", help="Do not de-duplicate output")
    p.add_argument("--seed", type=int, default=None,
                   help="Seed for reproducible output (default: secure random)")
    p.add_argument("--authorized", action="store_true",
                   help="Assert authorization non-interactively (skips the prompt)")
    p.add_argument("--no-animation", action="store_true",
                   help="Disable intro/typing/glitch animations (good for scripts)")
    p.add_argument("--no-log", action="store_true", help="Do not write a session log file")
    return p.parse_args()


# --------------------------------------------------------------------------
# Input collection
# --------------------------------------------------------------------------
def interactive_collect() -> Dict[str, Any]:
    ui.section("TARGET OSINT INPUT")
    ui.info("Fill what you know. Press Enter to skip any field.")
    ui.console.print()
    data: Dict[str, Any] = {}
    for label, key, is_list in FIELDS:
        raw = ui.ask(f"{label:<34}:").strip()
        if is_list:
            data[key] = [s.strip() for s in raw.split(",") if s.strip()]
        else:
            data[key] = raw
    return data


def normalize_loaded(data: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce a loaded JSON profile into the shape the engine expects."""
    friends = data.get("friends")
    if isinstance(friends, str):
        data["friends"] = [s.strip() for s in friends.split(",") if s.strip()]
    return data


def profile_fields(inputs: Dict[str, Any]) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for label, key, is_list in FIELDS:
        val = inputs.get(key)
        if is_list:
            val = ", ".join(val) if val else ""
        if val:
            rows.append((label.split(" (")[0], str(val)))
    return rows


# --------------------------------------------------------------------------
# Authorization
# --------------------------------------------------------------------------
def authorize(args: argparse.Namespace, logger) -> bool:
    ui.section("AUTHORIZATION")
    ui.disclaimer(DISCLAIMER)
    if args.authorized:
        logger.info("Authorization asserted via --authorized flag.")
        ui.ok("Authorization asserted via --authorized flag.")
        ui.access_granted()
        return True

    for attempt in range(1, 4):
        resp = ui.ask(f"Type '{AUTH_PHRASE}' to continue:").strip()
        logger.debug("auth attempt %d: %r", attempt, resp)
        if resp.upper() == AUTH_PHRASE:
            logger.info("Authorization confirmed by operator.")
            ui.access_granted()
            return True
        ui.err(f"Phrase did not match. Attempts left: {3 - attempt}")

    ui.access_denied()
    logger.critical("Authorization failed; aborting.")
    return False


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------
def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def run_generation(inputs: Dict[str, Any], args: argparse.Namespace, logger):
    out = Path(args.output)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)

    stats = GenStats()
    reservoir: List[str] = []
    seen_for_sample = 0
    start = time.time()
    interrupted = False

    ui.section("GENERATION")
    ui.info(f"Writing up to {args.max_words:,} candidates → [hx.value]{out}[/]")

    with out.open("w", encoding="utf-8", newline="\n") as fout:
        progress = ui.make_progress()
        with progress:
            task = progress.add_task("generating", total=args.max_words, rate="0/s")
            try:
                for pw in stream_unique(
                    inputs,
                    max_words=args.max_words,
                    min_len=args.min_len,
                    max_len=args.max_len,
                    dedup=not args.no_dedup,
                    seed=args.seed,
                    stats=stats,
                ):
                    fout.write(pw + "\n")

                    seen_for_sample += 1
                    if len(reservoir) < SAMPLE_COUNT:
                        reservoir.append(pw)
                    else:
                        j = random.randint(0, seen_for_sample - 1)
                        if j < SAMPLE_COUNT:
                            reservoir[j] = pw

                    if stats.written % 500 == 0:
                        now = time.time()
                        rate = stats.written / (now - start) if now > start else 0
                        progress.update(task, completed=stats.written, rate=f"{rate:,.0f}/s")
            except KeyboardInterrupt:
                interrupted = True
                logger.warning("Generation interrupted by operator; partial output saved.")

            final_rate = stats.written / (time.time() - start) if time.time() > start else 0
            progress.update(
                task, completed=stats.written, total=max(stats.written, 1),
                rate=f"{final_rate:,.0f}/s",
            )

    elapsed = time.time() - start
    return stats, reservoir, elapsed, interrupted, out


def show_results(stats: GenStats, reservoir: List[str], elapsed: float,
                 out: Path, args: argparse.Namespace) -> None:
    ui.section("RESULTS")

    if stats.written == 0:
        ui.warn("No candidates were generated — the target profile looked empty.")
        return

    size = out.stat().st_size if out.exists() else 0
    speed = stats.written / elapsed if elapsed > 0 else 0
    rows: List[Tuple[str, str]] = [
        ("Output file", str(out.resolve())),
        ("File size", human_size(size)),
        ("Unique written", f"{stats.written:,}"),
    ]
    if not args.no_dedup:
        rows.append(("Duplicates skipped", f"{stats.duplicates:,}"))
    filtered = stats.too_short + stats.too_long
    if filtered:
        rows.append(("Filtered by length", f"{filtered:,}"))
    rows += [
        ("Length range", f"{stats.min_len_seen}–{stats.max_len_seen}"),
        ("Average length", f"{stats.avg_len:.1f}"),
        ("Raw generated", f"{stats.raw:,}"),
        ("Elapsed", f"{elapsed:.2f}s"),
        ("Speed", f"{speed:,.0f} pw/s"),
    ]
    ui.summary(rows)

    samples = []
    for pw in sorted(set(reservoir), key=len)[:SAMPLE_COUNT]:
        score, label, _bits = estimate(pw)
        samples.append((pw, score, label))
    ui.sample_table(samples)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    ui.set_animations(not args.no_animation)

    logpath = None if args.no_log else make_session_log()
    logger = setup_logger(logpath)
    logger.info("=== OSINT WordGen session start ===")

    ui.matrix_rain()
    ui.show_banner()
    ui.boot_sequence([
        "loading OSINT engine",
        "arming transformation rules",
        "opening secure session",
    ])

    if not authorize(args, logger):
        return 1

    # Collect / load inputs
    if args.input:
        try:
            inputs = normalize_loaded(load_input_json(args.input))
            ui.ok(f"Loaded target profile from [hx.value]{args.input}[/]")
        except Exception as exc:
            ui.err(f"Could not load input file: {exc}")
            logger.error("input load failed: %s", exc)
            return 1
    else:
        inputs = interactive_collect()

    if args.save_input:
        try:
            save_input_json(args.save_input, inputs)
            ui.ok(f"Saved target profile to [hx.value]{args.save_input}[/]")
        except Exception as exc:
            ui.warn(f"Could not save input profile: {exc}")

    if not has_usable_inputs(inputs):
        ui.err("No usable OSINT data provided. Give at least one field (name, phone, ...).")
        logger.error("no usable inputs; aborting.")
        return 1

    ui.section("TARGET PROFILE")
    ui.target_profile(profile_fields(inputs))
    logger.info("collected inputs: %s", inputs)

    stats, reservoir, elapsed, interrupted, out = run_generation(inputs, args, logger)
    show_results(stats, reservoir, elapsed, out, args)

    if interrupted:
        ui.warn("Session ended early (Ctrl+C). Partial wordlist saved.")

    try:
        save_last_wordlist(str(out.resolve()))
    except Exception:
        pass

    if logpath:
        ui.info(f"Session log: [hx.value]{logpath}[/]")
    logger.info("=== session finished: %d candidates ===", stats.written)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        ui._show_cursor()
        ui.console.print("\n  [hx.err]✗ Aborted by user.[/]")
        sys.exit(130)
