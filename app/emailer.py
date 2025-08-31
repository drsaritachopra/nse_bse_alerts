# file: app/emailer.py
from __future__ import annotations
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from .config import load_config


def send_mail(subject: str, html_body: str):
    cfg = load_config().mail
    if not cfg.username or not cfg.to_addrs:
        raise RuntimeError("Mail not configured: set username/password/to_addrs")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = cfg.from_addr
    msg['To'] = ", ".join(cfg.to_addrs)
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as s:
        s.starttls()
        s.login(cfg.username, cfg.password)
        s.sendmail(cfg.from_addr, cfg.to_addrs, msg.as_string())
