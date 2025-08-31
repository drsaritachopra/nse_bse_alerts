# file: app/store.py
from __future__ import annotations
import os
import sqlite3
from contextlib import closing
from typing import Iterable, Tuple
from .util import app_storage_dir

DB_PATH = os.path.join(app_storage_dir(), 'seen.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
  k TEXT PRIMARY KEY,
  ts INTEGER
);
"""


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with closing(conn.cursor()) as c:
        c.execute(SCHEMA)
        conn.commit()
    return conn


def has(key: str) -> bool:
    with closing(_conn()) as conn, closing(conn.cursor()) as c:
        c.execute("SELECT 1 FROM seen WHERE k=?", (key,))
        return c.fetchone() is not None


def add_all(keys: Iterable[Tuple[str, int]]):
    with closing(_conn()) as conn, closing(conn.cursor()) as c:
        c.executemany("INSERT OR IGNORE INTO seen (k, ts) VALUES (?, ?)", list(keys))
        conn.commit()
