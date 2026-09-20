"""
Outreach engine — sends personalized emails with Gmail SMTP.
Supports initial contact, follow-up 1, follow-up 2, and reply tracking.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import time
import random
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SENDER_NAME, SENDER_EMAIL, SENDER_PHONE,
    MIN_DELAY_BETWEEN_EMAILS_SEC, MAX_DELAY_BETWEEN_EMAILS_SEC,
    MAX_EMAILS_PER_DAY, DB_PATH,
)
from email_templates import render_email


# ── Database helpers ────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def mark_initial_sent(lead_id: int, template_key: str):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE leads SET email_stage='INITIAL_SENT', status='CONTACTED', "
            "initial_sent_at=?, contacted_at=?, template_used=? WHERE id=?",
            (datetime.now().isoformat(), datetime.now().isoformat(), template_key, lead_id),
        )
        conn.commit()


def mark_followup1_sent(lead_id: int):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE leads SET email_stage='FOLLOWUP1_SENT', followup1_sent_at=? WHERE id=?",
            (datetime.now().isoformat(), lead_id),
        )
        conn.commit()


def mark_followup2_sent(lead_id: int):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE leads SET email_stage='FOLLOWUP2_SENT', followup2_sent_at=? WHERE id=?",
            (datetime.now().isoformat(), lead_id),
        )
        conn.commit()


def mark_reply(lead_id: int, reply_type: str, notes: str = ""):
    """reply_type: INTERESTED, NOT_INTERESTED, QUESTION, OTHER"""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE leads SET reply_received=1, reply_type=?, reply_notes=?, "
            "reply_received_at=?, email_stage='REPLIED' WHERE id=?",
            (reply_type, notes, datetime.now().isoformat(), lead_id),
        )
        conn.commit()


# ── SMTP sender ─────────────────────────────────────────────────────────────

def send_single_email(
    to_email: str,
    subject: str,
    body: str,
    cc_email: Optional[str] = None,
    dry_run: bool = True,
) -> bool:
    """Sends an email via Gmail SMTP or simulates sending in dry-run mode."""
    recipients = [to_email]
    if cc_email and cc_email.lower() != to_email.lower():
        recipients.append(cc_email)

    if dry_run:
        cc_str = f" (CC: {cc_email})" if cc_email else ""
        print(f"[DRY-RUN] → {to_email}{cc_str}")
        print(f"  Subject: {subject}")
        print(f"  Body: {len(body)} chars\n")
        return True

    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError(
            "SMTP credentials not configured! "
            "Set SMTP_USER and SMTP_PASSWORD in your .env file.\n"
            "For Gmail, use an App Password: https://myaccount.google.com/apppasswords"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL or SMTP_USER}>"
    msg["To"] = to_email
    if cc_email and cc_email.lower() != to_email.lower():
        msg["Cc"] = cc_email
    msg["Reply-To"] = SENDER_EMAIL or SMTP_USER

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL or SMTP_USER, recipients, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] Failed → {to_email}: {e}")
        return False



# ── Batch outreach ──────────────────────────────────────────────────────────

def run_outreach_batch(
    leads: List[Dict[str, Any]],
    template_key: str = "pl_initial_outreach",
    stage: str = "initial",          # "initial" | "followup1" | "followup2"
    dry_run: bool = True,
    max_count: int = 10,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_phone: Optional[str] = None,
) -> Dict[str, int]:
    """Executes a batch of outreach emails with human-like delays."""
    stats = {"attempted": 0, "sent": 0, "skipped": 0, "failed": 0}

    s_name = sender_name or SENDER_NAME
    s_email = sender_email or SENDER_EMAIL or SMTP_USER
    s_phone = sender_phone or SENDER_PHONE

    # Filter eligible leads based on stage
    if stage == "initial":
        targets = [
            l for l in leads
            if (l.get("email") or l.get("primary_contact_email"))
            and l.get("email_stage", "NONE") == "NONE"
        ]
        mark_fn = lambda lid: mark_initial_sent(lid, template_key)
    elif stage == "followup1":
        targets = [
            l for l in leads
            if l.get("email_stage") == "INITIAL_SENT"
            and not l.get("reply_received")
        ]
        template_key = "pl_follow_up_1"
        mark_fn = mark_followup1_sent
    elif stage == "followup2":
        targets = [
            l for l in leads
            if l.get("email_stage") == "FOLLOWUP1_SENT"
            and not l.get("reply_received")
        ]
        template_key = "pl_follow_up_2"
        mark_fn = mark_followup2_sent
    else:
        print(f"Unknown stage: {stage}")
        return stats

    targets = targets[:max_count]

    if not targets:
        print(f"No eligible leads for stage '{stage}'.")
        return stats

    print(f"📧 Starting {stage} batch: {len(targets)} leads (dry_run={dry_run})")
    print("=" * 60)

    for i, lead in enumerate(targets, 1):
        stats["attempted"] += 1
        rendered = render_email(
            lead=lead,
            template_key=template_key,
            sender_name=s_name,
            sender_email=s_email,
            sender_phone=s_phone,
        )

        # Route to Decision Maker first, CC company desk
        p_email = lead.get("primary_contact_email", "")
        c_email = lead.get("email", "")

        if p_email and c_email and p_email.lower() != c_email.lower():
            to_addr = p_email
            cc_addr = c_email
        else:
            to_addr = p_email or c_email
            cc_addr = None

        if not to_addr or to_addr in ("", "N/A"):
            stats["skipped"] += 1
            continue

        success = send_single_email(
            to_email=to_addr,
            subject=rendered["subject"],
            body=rendered["body"],
            cc_email=cc_addr,
            dry_run=dry_run,
        )

        if success:
            stats["sent"] += 1
            if not dry_run:
                mark_fn(lead["id"])
                recip_info = f"{to_addr} (CC: {cc_addr})" if cc_addr else to_addr
                print(f"  ✅ [{i}/{len(targets)}] Sent to {lead['name']} → {recip_info}")
        else:
            stats["failed"] += 1

        # Rate-limit to avoid Gmail's spam detection
        if i < len(targets) and not dry_run:
            delay = random.randint(MIN_DELAY_BETWEEN_EMAILS_SEC, MAX_DELAY_BETWEEN_EMAILS_SEC)
            print(f"  ⏳ Waiting {delay}s...")
            time.sleep(delay)

    print("=" * 60)
    print(f"Done: {stats['sent']} sent, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats
