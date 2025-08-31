# file: app/config.py
from __future__ import annotations
import os
import tomllib
from dataclasses import dataclass
from typing import List
from .util import app_storage_dir

CONFIG_PATH = os.path.join(app_storage_dir(), "config.toml")

@dataclass
class MailConfig:
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_addr: str
    to_addrs: List[str]

@dataclass
class AppConfig:
    mail: MailConfig


def load_config() -> AppConfig:
    # ENV overrides for CI/testing
    env = os.environ
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'rb') as f:
            data = tomllib.load(f)
    else:
        data = {
            'mail': {
                'smtp_host': env.get('SMTP_HOST', 'smtp.gmail.com'),
                'smtp_port': int(env.get('SMTP_PORT', '587')),
                'username': env.get('SMTP_USER', ''),
                'password': env.get('SMTP_PASS', ''),
                'from_addr': env.get('MAIL_FROM', env.get('SMTP_USER', '')),
                'to_addrs': [x.strip() for x in env.get('MAIL_TO', '').split(',') if x.strip()],
            }
        }
    mail = MailConfig(**data['mail'])
    return AppConfig(mail=mail)
