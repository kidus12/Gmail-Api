# Gmail Mail-Merge (Python + Gmail API) — Public-Safe Demo

A sanitized example of a Python script that sends personalized emails using the Gmail API.
It reads recipients from a CSV and renders an email template with simple placeholders.

> ⚠️ This repository is for demonstration. Do not commit real recipient data, attachments,
> or credentials. Respect Gmail/Workspace quotas and applicable laws (e.g., CAN-SPAM).

## Features
- Personalized emails from CSV (`name,email`)
- Templated body (`templates/outreach_email.txt.j2`)
- DRY-RUN mode enabled by default for safety
- Simple, rate-limit-friendly sending with minimal retry

## Quick Start
1. Create a Google Cloud OAuth client for the Gmail API and download `credentials.json`.
   Place it next to `main.py` **but do not commit it**.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` → `.env` and edit values as needed. By default, `DRY_RUN=true`.
4. Try a dry run:
   ```bash
   python main.py --help
   python main.py
   ```
   On first run, your browser opens to complete OAuth; a `token.json` is created locally.

## Environment Variables
- `SENDER_EMAIL` — e.g., "Sender Name <sender@example.com>"
- `CC_EMAIL` — optional CC address
- `SUBJECT` — subject line
- `RECIPIENTS_CSV` — CSV path (default: `recipients.example.csv`)
- `DRY_RUN` — `true` or `false` (default: `true`)
- `PER_SEND_DELAY_SEC` — float seconds between sends
- `ATTACHMENTS` — comma-separated paths (optional)

## CSV Format
```
name,email
Alex Example,alex@example.com
```

## Safety
- Add real values to `.env` **locally only**.
- Keep `credentials.json` and `token.json` out of git.
- Use dry-run to preview before sending.
- Do not send unsolicited email.
