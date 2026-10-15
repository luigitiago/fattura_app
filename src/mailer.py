"""SMTP e-mail sending (standard library only)."""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr


class MailError(Exception):
    """Raised for any failure while sending or testing the mail connection."""


def is_configured(config) -> bool:
    email = config.get("email", default={}) or {}
    return bool(email.get("enabled") and email.get("host") and email.get("sender_email"))


def _connect(config):
    email = config.get("email", default={}) or {}
    host = (email.get("host") or "").strip()
    port = int(email.get("port") or 587)
    security = (email.get("security") or "STARTTLS").strip()
    user = (email.get("user") or "").strip()
    password = email.get("password") or ""

    if not host:
        raise MailError("SMTP host is empty")

    try:
        if security == "SSL":
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            if security == "STARTTLS":
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
        if user:
            server.login(user, password)
        return server
    except smtplib.SMTPException as exc:
        raise MailError(str(exc)) from exc
    except OSError as exc:
        raise MailError(str(exc)) from exc


def test_connection(config) -> None:
    """Raise MailError when the SMTP connection/login fails."""
    server = _connect(config)
    try:
        server.quit()
    except Exception:
        pass


def send_invoice(config, to: str, subject: str, body: str, attachment_path: str | None = None) -> None:
    """Send an e-mail, optionally attaching the generated PDF."""
    email = config.get("email", default={}) or {}
    sender_email = (email.get("sender_email") or "").strip()
    sender_name = (email.get("sender_name") or "").strip() or sender_email
    reply_to = (email.get("reply_to") or "").strip()
    if not sender_email:
        raise MailError("Sender e-mail is empty")

    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as fh:
            data = fh.read()
        filename = os.path.basename(attachment_path)
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)

    server = _connect(config)
    try:
        server.send_message(msg)
    except smtplib.SMTPException as exc:
        raise MailError(str(exc)) from exc
    finally:
        try:
            server.quit()
        except Exception:
            pass
