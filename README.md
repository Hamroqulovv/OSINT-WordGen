OSINT WordGen v1.0💥

<h3>🧠 Advanced OSINT-Based Password Wordlist Generator</h3> <p>Generate human-like password wordlists based on real OSINT data — built for professional pentesters and cybersecurity experts.</p>

📌 Overview

OSINT WordGen is a powerful tool that leverages Open Source Intelligence (OSINT) to generate password wordlists that mimic real human behavior.
Instead of producing random or basic words, it combines names, dates, phone numbers, addresses, nicknames, and other information to produce smart, realistic, and highly effective password candidates.

This tool is designed for:

🔐 Penetration testers performing password audits

🧠 Red teamers simulating credential attacks

🕵️‍♂️ OSINT analysts generating context-aware wordlists

🧰 Cybersecurity researchers testing password strength

✨ Features

✅ Human-like password generation with OSINT data
✅ Combines names, dates, symbols, and numbers intelligently
✅ Randomized and mixed-case password variations
✅ Real-time progress bar and logging system
✅ Auto-setup virtual environment — no manual pip install needed
✅ Saves results automatically into the output/ folder

⚙️ Installation
Clone the repository and make the tool executable:
git clone https://github.com/Hamroqulovv/password-generator.git
cd osint-wordgen
chmod +x run.sh
     
     🧠 First run automatically creates a virtual environment and installs dependencies.

🚀 Usage
🔧 Basic Usage

Simply run the tool without arguments — it will generate and save the wordlist automatically:

  ./run.sh

📁 Custom Output Location

If you want to specify the output file manually:

  ./run.sh -o output/custom_wordlist.txt
          
✅ After generation, the wordlist will be saved automatically in the output/ directory.

📊 Example Output

The generated wordlist is designed to mimic how real users create passwords.
For example:

John1990!\b
johnDoe@123
mary_2001
P@ssw0rd!
Doe!2024
johndoe_#2000
    
    Thousands of smart combinations will be created automatically.

🧪 Advanced Options
Option	Description
-o <file>	Specify output file name (default: output/wordlist.txt)
--no-spinner	Disable spinner animation
--no-log	Disable session logging
-m <number>	Set maximum number of words

🔐 Authorization Check

Before generation starts, the tool requires a secret confirmation phrase.
This ensures that only the developer or authorized users can run it.
    
    Type the confirmation phrase exactly to proceed: ***************

⚠️ This phrase is not included in the source code or repository.
Only the tool creator knows it.

🛠 Project Structure
"""
osint-wordgen/
│
├── run.sh                 # Startup script
├── main.py               # Entry point
├── wordgen/              # Wordlist generation engine
│   ├── generator.py
│   └── utils.py
├── requirements.txt
├── LICENSE
├── README.md
└── output/               # Generated
"""
 wordlists are saved here

⚠️ Legal Disclaimer

This tool is strictly for authorized security research, red teaming, and penetration testing purposes.
You must have explicit written permission before using it against any system or account.
The developers assume no liability for misuse or illegal activity.

🧑‍💻 Author
HAMROQULOV Security Labs
🔗 GitHub: @Hamroqulovv
📧 Contact: hamroqulovvv@gmail.com

<div align="center">

💡 "Security through intelligence — OSINT is power." 🔐
