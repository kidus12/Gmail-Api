import base64
import csv
import mimetypes
import os
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_creds():
    creds = None
    token_path = Path("token.json")
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return creds

def load_template(path="templates/outreach_email.txt.j2"):
    return Path(path).read_text(encoding="utf-8")

def parse_bool(s: str, default: bool):
    if s is None:
        return default
    s = s.strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def attachments_from_env(env_value):
    if not env_value:
        return []
    return [p.strip() for p in env_value.split(",") if p.strip()]

def send_message(service, message, dry_run=True):
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    if dry_run:
        print("[DRY RUN] Would send:", message["To"], "| subject:", message["Subject"])
        return None

    attempt = 0
    while True:
        try:
            sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
            print("Sent ->", message["To"], "| id=", sent.get("id"))
            return sent
        except HttpError as e:
            status = getattr(e, "status_code", None) or getattr(getattr(e, "resp", None), "status", None)
            if status in (403, 429, 500, 502, 503, 504) and attempt < 5:
                attempt += 1
                sleep_for = min(30.0, 1.0 * (2 ** attempt))
                print(f"Retryable error {status}; backing off {sleep_for:.1f}s...")
                time.sleep(sleep_for)
                continue
            raise

def build_message(to_addr, subject, body, sender, cc=None, attachments=None):
    msg = EmailMessage()
    msg.set_content(body)
    msg["To"] = to_addr
    if cc:
        msg["Cc"] = cc
    msg["From"] = sender
    msg["Subject"] = subject

    for fpath in attachments or []:
        p = Path(fpath)
        if not p.exists():
            print(f"[WARN] Attachment missing: {fpath}")
            continue
        mime, _ = mimetypes.guess_type(str(p))
        if not mime:
            mime = "application/octet-stream"
        maintype, subtype = mime.split("/")
        msg.add_attachment(p.read_bytes(), maintype, subtype, filename=p.name)
    return msg

def main():
    load_dotenv()

    SENDER = os.getenv("SENDER_EMAIL", "Sender <sender@example.com>")
    CC_ADDR = os.getenv("CC_EMAIL", "") or None
    SUBJECT = os.getenv("SUBJECT", "Program Overview")
    CSV_PATH = os.getenv("RECIPIENTS_CSV", "recipients.example.csv")
    DRY_RUN = parse_bool(os.getenv("DRY_RUN", "true"), True)
    PER_SEND_DELAY_SEC = float(os.getenv("PER_SEND_DELAY_SEC", "2.0"))
    ATTACHMENTS = attachments_from_env(os.getenv("ATTACHMENTS", ""))

    template = load_template()
    creds = get_creds()
    service = build("gmail", "v1", credentials=creds)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)  # expected columns: name,email
        for row in reader:
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            if not email:
                print("[WARN] Skipping row without email:", row)
                continue

            body = template.format(recipient_name=name or "there")
            msg = build_message(
                to_addr=email,
                subject=SUBJECT,
                body=body,
                sender=SENDER,
                cc=CC_ADDR,
                attachments=ATTACHMENTS
            )
            send_message(service, msg, dry_run=DRY_RUN)
            time.sleep(PER_SEND_DELAY_SEC)

if __name__ == "__main__":
    main()
