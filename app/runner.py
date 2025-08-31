# file: app/runner.py
from __future__ import annotations
import html
import os
import time
from typing import Iterable, List
from datetime import datetime

from . import store
from .filtering import is_corporate_action
from .scraper import fetch_nse, fetch_bse, Item
from .emailer import send_mail
from .util import app_storage_dir, get_ist_now

LOCK_PATH = os.path.join(app_storage_dir(), 'run.lock')


def ensure_app_dirs():
    os.makedirs(app_storage_dir(), exist_ok=True)


class FileLock:
    # Why: prevent overlapping runs between UI and service
    def __init__(self, path: str, stale_seconds: int = 600):
        self.path = path
        self.stale = stale_seconds

    def __enter__(self):
        try:
            if os.path.exists(self.path):
                age = time.time() - os.path.getmtime(self.path)
                if age < self.stale:
                    raise RuntimeError("another run is in progress")
            with open(self.path, 'w') as f:
                f.write(str(time.time()))
        except Exception:
            raise

    def __exit__(self, exc_type, exc, tb):
        try:
            if os.path.exists(self.path):
                os.remove(self.path)
        except Exception:
            pass


def _render_email(items: List[Item]) -> str:
    rows = []
    for it in items:
        rows.append(
            f"<tr><td>{html.escape(it.source)}</td><td>{html.escape(it.symbol)}</td>"
            f"<td>{html.escape(it.headline)}</td>"
            f"<td>{it.when.strftime('%Y-%m-%d %H:%M')}</td>"
            f"<td><a href='{html.escape(it.url)}'>link</a></td></tr>"
        )
    table = (
        "<table border=1 cellspacing=0 cellpadding=6>"
        "<tr><th>Src</th><th>Symbol</th><th>Headline</th><th>When</th><th>Doc</th></tr>"
        + "".join(rows)
        + "</table>"
    )
    return table


def _collect() -> List[Item]:
    items: List[Item] = []
    try:
        items.extend(fetch_nse())
    except Exception as e:
        print("[nse]", e)
    try:
        items.extend(fetch_bse())
    except Exception as e:
        print("[bse]", e)
    return items


def _filter_new(items: List[Item]) -> List[Item]:
    fresh = [it for it in items if is_corporate_action(it.__dict__)]
    unseen = [it for it in fresh if not store.has(it.key)]
    return unseen


def _remember(items: List[Item]):
    now_ts = int(time.time())
    store.add_all((it.key, now_ts) for it in items)


def check_and_alert(trigger: str | None = None, manual: bool = False) -> int:
    with FileLock(LOCK_PATH):
        items = _collect()
        new_items = _filter_new(items)
        if new_items:
            subj = f"Corp Actions ({len(new_items)}) — {get_ist_now().strftime('%d %b %Y %H:%M')}"
            body = _render_email(new_items)
            if trigger:
                body = f"<p><i>Trigger: {trigger}</i></p>" + body
            send_mail(subj, body)
            _remember(new_items)
        return len(new_items)


if __name__ == "__main__":
    # CLI helper: run once and print count
    cnt = check_and_alert(trigger="manual CLI", manual=True)
    print("New:", cnt)
