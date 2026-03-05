# NotEmails

<div align="center">

```
 _   _       _   _____                 _ _
| \ | | ___ | |_| ____|_ __ ___   __ _(_) |___
|  \| |/ _ \| __|  _| | '_ ` _ \ / _` | | / __|
| |\  | (_) | |_| |___| | | | | | (_| | | \__ \
|_| \_|\___/ \__|_____|_| |_| |_|\__,_|_|_|___/
```

**CLI tool for managing [NotLetters.com](https://notletters.com) email accounts**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Rich](https://img.shields.io/badge/Rich-Terminal-orange.svg)](https://github.com/Textualize/rich)

</div>

---

## What It Does

- **Bulk Password Changer** — Change passwords for hundreds of accounts at once, with threaded processing.
- **Email Receiver** — Pull emails from all your accounts, filter by keyword or starred status, and save them locally.
- **Email Purchase** — Buy new email accounts directly from the NotLetters API (Limited, Unlimited, RU Zone, Personal).
- **Balance Checker** — Quick view of your account info, balance, and rate limit.
- **API Connection Test** — Diagnose connectivity issues before you start working.

---

## Getting Started

```bash
git clone https://github.com/g8tsz/NotLetters-Email-Tool
cd NotLetters-Email-Tool
pip install -r requirements.txt
```

Then just run it:

```bash
python notemails.py
```

On first launch you'll be asked for your API key. It gets saved to `config.json` so you only have to enter it once.  
To reset it, delete `config.json` or say "Yes" when the tool asks if you want to change it.

> Get your API key at [notletters.com](https://notletters.com)

---

## Input Format

Create a text file with your accounts in `email:password` format:

```
email1@notletters.com:password1
email2@notletters.com:password2
email3@notletters.com:password3
```

---

## Output Files

### Password Changer

| File               | Contents                                                                   |
| ------------------ | -------------------------------------------------------------------------- |
| `updated.txt`      | Only the accounts that were successfully updated                           |
| `updated_mail.txt` | All accounts — updated ones get the new password, failed ones keep the old |

### Email Receiver

```
emails_with_letters/
├── accounts_with_mail.txt
├── user1_at_notletters_com/
│   ├── letter_1_abc12345.txt
│   └── letter_2_def67890.txt
└── user2_at_notletters_com/
    └── letter_1_ghi11223.txt
```

### Email Purchase

```
purchased_emails_20250118_143022.txt
```

---

## Troubleshooting

| Problem                  | Fix                                            |
| ------------------------ | ---------------------------------------------- |
| `API Key Not Configured` | Run the script — it'll ask you for it          |
| `File not found`         | Double-check the file path you entered         |
| `401 Unauthorized`       | Your `email:password` combo is wrong           |
| `Rate Limit Exceeded`    | The tool handles this automatically, just wait |

---

## API Details

|                |                                  |
| -------------- | -------------------------------- |
| **Base URL**   | `https://api.notletters.com`     |
| **Rate Limit** | 10 req/s (handled automatically) |
| **Auth**       | Bearer token                     |

---

## Disclaimer

This tool is for educational and legitimate use only. You're responsible for following [NotLetters.com](https://notletters.com) terms of service and any applicable laws.

---

## License

MIT — see [LICENSE](LICENSE) for details.

