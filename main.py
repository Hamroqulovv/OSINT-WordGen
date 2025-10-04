#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — HAMROQULOV OSINT WordGen (professional entrypoint)

Runs an interactive collection of OSINT inputs, requires user confirmation phrase,
streams password candidate generation to disk, displays progress and logs session.
"""
from dotenv import load_dotenv
import os
import argparse
import sys
import time
import datetime
import logging
from pathlib import Path
from termcolor import colored

load_dotenv()

# local package
from wordgen.utils import print_banner, spinner, make_session_log, save_last_wordlist
from wordgen.generator import generate_wordlist_stream, slug, normalize

# .env faylini yuklash
load_dotenv()
SECRET_PHRASE = os.getenv("CONFIRMATION_PHRASE")
# Confirmation phrase (explicit written authorization)

# defaults
DEFAULT_MAX_WORDS = 200000

# Logging setup
def setup_logger(logfile: Path):
    logger = logging.getLogger("osint_wordgen")
    logger.setLevel(logging.DEBUG)

    # file handler
    fh = logging.FileHandler(str(logfile), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter("%(message)s")
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    logger.info(f"Session log: {logfile}")
    return logger

# Interactive input prompts
def interactive_collect_inputs():
    print(colored("Provide OSINT inputs. Press Enter to skip any field.", "cyan"))
    data = {}
    try:
        data["first"] = normalize(input("Ism (First name): ").strip())
        data["last"] = normalize(input("Familiya (Last name): ").strip())
        data["middle"] = normalize(input("Otasining ismi (Middle name): ").strip())
        data["nickname"] = normalize(input("Nickname (optional): ").strip())
        data["phone"] = normalize(input("Phone (e.g. +998901234567): ").strip())
        data["address"] = normalize(input("Manzil / Shahar (Address / City): ").strip())
        data["age"] = normalize(input("Yoshi (yillar)  | Age (years): ").strip())
        friends = input("Do'stlar ismi (Eng yaqini) (e.g. Ali,Karim): ").strip()
        data["friends"] = [s.strip() for s in friends.split(",")] if friends else []
        data["company"] = normalize(input("Kompaniya / Tashkilot | (optional): ").strip())
        data["pet"] = normalize(input("Uy hayvonlari nomi | Pet name (optional): ").strip())
        data["hobby"] = normalize(input("Xobbi | Hobby (optional): ").strip())
        data["birth_year"] = normalize(input("Tug'ilgan yili | Birth year (optional): ").strip())
        data["email"] = normalize(input("Email (optional): ").strip())
        data["domain"] = normalize(input("Domen | Domain (optional): ").strip())
    except KeyboardInterrupt:
        print("\n[!] Input interrupted by user.")
        raise
    return data

# parse args
def parse_args():
    p = argparse.ArgumentParser(prog="HAMROQULOV-OSINT-WordGen")
    p.add_argument(
    "-o", "--output",
    default="output/wordlist.txt",
    help="Output wordlist file (default: output/wordlist.txt)"
)
    p.add_argument("-m", "--max-words", type=int, default=DEFAULT_MAX_WORDS, help="Nomzodlarning maksimal soni | Max number of candidates")
    p.add_argument("--no-spinner", action="store_true", help="Boshlash spinnerini o'chirib qo'ying | Disable startup spinner")
    p.add_argument("--no-log", action="store_true", help="Sessiya jurnali faylini yozmang | Do not write session log file")
    return p.parse_args()

def main():
    args = parse_args()

    # Banner
    print_banner()

    # spinner
    if not args.no_spinner:
        for _ in spinner(duration=1.8, interval=0.06):
            pass

    # Create session log path and logger
    logpath = make_session_log()
    logger = setup_logger(logpath)
    if args.no_log:
        # disable file handlers
        for h in list(logger.handlers):
            if isinstance(h, logging.FileHandler):
                logger.removeHandler(h)
        logger.warning("File logging disabled (--no-log).")

    # Confirmation phrase
    logger.warning("Ushbu vosita parol nomzodlarini yaratadi. YOZMA avtorizatsiyangiz borligiga ishonch hosil qiling  |  This tool will generate password candidates. Ensure you have WRITTEN authorization.")
    attempts = 0
    confirmed = False
    while attempts < 3:
        attempts += 1
        try:
            resp = input(colored("Tasdiqlash iborasini kiriting: ", "magenta")).strip()
        except KeyboardInterrupt:
            logger.error("Tasdiqlash foydalanuvchi tomonidan bekor qilindi.")
            sys.exit(1)
        logger.debug(f"Tasdiqlashga urinish: {resp!r}")
        if resp == SECRET_PHRASE:
            confirmed = True
            logger.info(colored("Avtorizatsiya foydalanuvchi tomonidan tasdiqlangan.", "green"))
            break
        else:
            logger.error(colored("Bu ibora mos kelmadi. Qayta urinib ko'ring.", "red"))
    if not confirmed:
        logger.critical(colored("Tasdiqlash amalga oshmadi. Noto'g'ri foydalanishning oldini olish uchun chiqish.", "red"))
        sys.exit(1)

    # Collect inputs
    try:
        inputs = interactive_collect_inputs()
    except KeyboardInterrupt:
        logger.critical("Kirish bekor qilindi.")
        sys.exit(1)

    logger.debug(f"Yig'ilgan ma'lumotlar: {inputs}")

    # Prepare output
    out = Path(args.output)
    if not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)

    logger.info(colored(f"Starting generation to: {out} (max {args.max_words})", "cyan"))
    start = time.time()
    written = 0
    try:
        with out.open("w", encoding="utf-8") as fout:
            # progress bar using tqdm
            from tqdm import tqdm
            with tqdm(total=args.max_words, unit="pw", ncols=90, desc="Generating") as pbar:
                for pw in generate_wordlist_stream(inputs, max_words=args.max_words):
                    fout.write(pw + "\n")
                    written += 1
                    pbar.update(1)
                if written < args.max_words:
                    pbar.total = written
                    pbar.refresh()
    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user. Partial output saved.")
    except Exception as e:
        logger.critical(f"Error during generation: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    logger.info(colored("\n[✔] Generation completed.", "green"))
    logger.info(colored(f"  Output file: {out.resolve()}", "cyan"))
    logger.info(colored(f"  Total candidates: {written}", "cyan"))
    logger.info(colored(f"  Time elapsed: {elapsed:.2f} seconds", "cyan"))

    # record last path
    try:
        save_last_wordlist(str(out.resolve()))
    except Exception:
        logger.debug("Could not save last wordlist pointer; continuing.")

    logger.info("Session finished. Check log for details.")
    logger.info(f"Log file: {logpath}")
    # friendly exit
    input("\nPress Enter to exit...")
    sys.exit(0)

if __name__ == "__main__":
    main()
