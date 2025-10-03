#!/usr/bin/env python3
# Utilities: logo, spinner, logging helper, minor helpers

import sys
import time
import datetime
from pathlib import Path
from termcolor import colored
from pyfiglet import Figlet

LOG_ROOT = Path.home() / ".osint_wordgen" / "logs"
LOG_ROOT.mkdir(parents=True, exist_ok=True)

def print_banner(big_text="HAMROQULOV", subtitle="OSINT WordGen v1.0"):
    f = Figlet(font="big")
    big = f.renderText(big_text)
    print(colored(big, "cyan"))
    # Right-side-ish subtitle
    width = 80
    pad = max(1, width - len(subtitle))
    print(colored(" " * pad + subtitle + "\n", "yellow"))
    print(colored("🔎 Smart OSINT-based password wordlist generator — Authorized use only\n", "green"))

def spinner(duration=2.0, interval=0.08):
    symbols = ["|", "/", "-", "\"]"]
    start = time.time()
    i = 0
    while (time.time() - start) < duration:
        sys.stdout.write("\r  Starting " + symbols[i % len(symbols)])
        sys.stdout.flush()
        time.sleep(interval)
        i += 1
        yield None
    sys.stdout.write("\r  Starting done!        \n")
    sys.stdout.flush()

def now_ts():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def save_last_wordlist(path: str):
    try:
        root = Path.home() / ".osint_wordgen"
        root.mkdir(parents=True, exist_ok=True)
        with open(root / "last_wordlist.txt", "w", encoding="utf-8") as f:
            f.write(path + "\n")
    except Exception:
        pass

def make_session_log():
    ts = now_ts()
    path = LOG_ROOT / f"session-{ts}.log"
    return path
