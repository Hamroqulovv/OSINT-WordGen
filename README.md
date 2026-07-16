<h1 align="center">OSINT WordGen <sub>v2.0</sub></h1>

<p align="center">
  <b>🧠 Advanced OSINT-based password wordlist generator</b><br>
  Human-like password candidates from real OSINT data — built for professional
  pentesters, red teamers and cybersecurity researchers.<br>
  <i>Matrix-themed terminal UI · authorized use only</i>
</p>

```
██╗    ██╗ ██████╗ ██████╗ ██████╗  ██████╗ ███████╗███╗   ██╗
██║    ██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝ ██╔════╝████╗  ██║
██║ █╗ ██║██║   ██║██████╔╝██║  ██║██║  ███╗█████╗  ██╔██╗ ██║
██║███╗██║██║   ██║██╔══██╗██║  ██║██║   ██║██╔══╝  ██║╚██╗██║
╚███╔███╔╝╚██████╔╝██║  ██║██████╔╝╚██████╔╝███████╗██║ ╚████║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝
        H A M R O Q U L O V  ·  OSINT WordGen  ·  by @Hamroqulovv
```

---

## 📌 Overview

**OSINT WordGen** turns Open Source Intelligence (names, dates, phone numbers,
addresses, nicknames, hobbies, …) into password wordlists that mimic how real
people actually build passwords. Instead of dumping random strings, it combines
and mangles target data with leetspeak, case-mixing, digit/symbol injection,
token permutations and targeted friend/company combos to produce smart,
realistic and highly effective candidates.

Designed for:

- 🔐 **Penetration testers** running password audits
- 🧠 **Red teamers** simulating credential attacks
- 🕵️ **OSINT analysts** building context-aware wordlists
- 🧰 **Security researchers** testing password strength

---

## ✨ Features

- 🟢 **Matrix / hacker terminal UI** — digital-rain intro, glitch-reveal ASCII
  banner, boot sequence and typing effects (all skippable with `--no-animation`)
- 🧬 **Human-like engine** — leet, case-mixing, digit/symbol blocks, random
  separators, birth-year math, permutations and friend/company combos
- ♻️ **Global de-duplication** — no repeated candidates across generation stages
- 📏 **Length filtering** — `--min-len` / `--max-len` to match password policies
- 🎯 **Reproducible runs** — `--seed` for byte-identical wordlists (defaults to
  secure random)
- 📂 **JSON target profiles** — run non-interactively with `-i profile.json`,
  or save what you typed with `--save-input`
- 📊 **Live progress + stats** — rate, elapsed/ETA, duplicates skipped, length
  distribution, and a sample-candidate strength preview
- 🪵 **Session logging** — every run is logged to `~/.osint_wordgen/logs/`
- 🖥️ **Cross-platform launchers** — `run.sh` (Linux/macOS), `run.ps1` &
  `run.bat` (Windows), each auto-creating a virtualenv on first run

---

## ⚙️ Requirements

- Python **3.9+**
- Dependencies (installed automatically by the launchers): `rich`, `pyfiglet`,
  `colorama`

---

## 🚀 Installation

```bash
git clone https://github.com/Hamroqulovv/password-generator.git
cd password-generator
```

**Linux / macOS**

```bash
chmod +x run.sh
./run.sh
```

**Windows (PowerShell)**

```powershell
.\run.ps1
```

**Windows (cmd)**

```bat
run.bat
```

> 🧠 The first run automatically creates a `.venv` and installs dependencies.
> You can also run it manually: `pip install -r requirements.txt && python main.py`.

---

## 🧭 Usage

**Interactive** — collect OSINT fields via prompts, then generate:

```bash
./run.sh
```

**From a JSON profile** — skip the prompts entirely:

```bash
./run.sh -i simple_input.json -o output/wordlist.txt
```

**Tuned run** — cap size, drop short passwords, reproducible, no animation:

```bash
./run.sh -m 50000 --min-len 8 --seed 42 --no-animation
```

### Options

| Option | Description |
| --- | --- |
| `-o, --output <file>` | Output wordlist file (default: `output/wordlist.txt`) |
| `-m, --max-words <n>` | Max **unique** candidates (default: `200000`) |
| `-i, --input <file>` | Load OSINT inputs from a JSON profile (skips prompts) |
| `--save-input <file>` | Save the collected inputs to a JSON file |
| `--min-len <n>` | Drop candidates shorter than `n` |
| `--max-len <n>` | Drop candidates longer than `n` |
| `--no-dedup` | Do not de-duplicate output |
| `--seed <n>` | Seed for reproducible output |
| `--authorized` | Assert authorization non-interactively (skips the prompt) |
| `--no-animation` | Disable intro/typing/glitch animations |
| `--no-log` | Do not write a session log file |

---

## 📊 Example output

Candidates are designed to mimic how real users create passwords:

```
Otabek2020
0t4bek!
Hamroqulov.Otabek
MyCompany2023
Tashk3ntAli
!998-example.com
KuzKarim123
```

The engine also prints a live progress bar and a completion summary with a
sample-candidate strength preview.

---

## 📥 OSINT input fields

`first`, `last`, `middle`, `nickname`, `phone`, `address`, `age`, `friends`
(list or comma-separated), `company`, `pet`, `hobby`, `birth_year`, `email`,
`domain`. All fields are optional — provide whatever you have. See
[`simple_input.json`](simple_input.json) for an example profile.

---

## 🔐 Authorization model

Before generation starts, the tool shows a legal notice and requires you to
type **`I HAVE AUTHORIZATION`** (or pass `--authorized` for automation). This is
an **accountability prompt**, not an access-control mechanism — it exists to make
you consciously confirm you have written permission for the target.

> ℹ️ Earlier versions gated the tool behind a secret phrase stored in a
> committed `.env` file. That secret was public in the repo and provided no real
> protection, so it has been removed in favor of this explicit acknowledgement.

---

## 🛠 Project structure

```
password-generator/
├── run.sh / run.ps1 / run.bat   # cross-platform launchers
├── main.py                      # CLI entry point & orchestration
├── wordgen/
│   ├── generator.py             # generation engine (+ dedup, filters, stats)
│   ├── ui.py                    # Matrix-themed UI & animations (rich)
│   ├── strength.py              # password-strength estimation
│   └── utils.py                 # logging, session log, JSON I/O
├── simple_input.json            # example OSINT profile
├── requirements.txt
├── LICENSE
└── output/                      # generated wordlists (git-ignored)
```

---

## ⚠️ Legal disclaimer

This tool is strictly for **authorized** security research, red teaming and
penetration testing. You **must** have explicit written permission before using
it against any system or account. The author assumes **no liability** for misuse
or illegal activity.

---

## 🧑‍💻 Author

**HAMROQULOV Security Labs**
🔗 GitHub: [@Hamroqulovv](https://github.com/Hamroqulovv)

<div align="center"><i>💡 "Security through intelligence — OSINT is power." 🔐</i></div>
