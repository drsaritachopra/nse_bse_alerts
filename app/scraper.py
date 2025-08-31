# file: app/scraper.py
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from .util import get_ist_now

UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
)

@dataclass
class Item:
    source: str  # NSE or BSE
    symbol: str
    headline: str
    url: str
    when: datetime

    @property
    def key(self) -> str:
        base = f"{self.source}|{self.symbol}|{self.headline}|{self.when.isoformat()}"
        return hashlib.sha1(base.encode()).hexdigest()


# --- NSE ---

def _nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/",
    })
    # warm cookies
    s.get("https://www.nseindia.com", timeout=15)
    return s


def fetch_nse(limit: int = 100) -> List[Item]:
    s = _nse_session()
    url = "https://www.nseindia.com/api/corporate-announcements"
    params = {"index": "equities"}
    r = s.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    rows = data.get('data') or data.get('corporateActions') or []

    out: List[Item] = []
    for row in rows[:limit]:
        symbol = row.get('symbol') or row.get('scrip') or ''
        headline = row.get('headline') or row.get('subject') or ''
        urlp = row.get('pdfUrl') or row.get('attachment') or row.get('moreLink') or ''
        when_str = row.get('date') or row.get('sm_dt') or row.get('announcedDate') or ''
        # Try multiple formats
        when = _parse_dt_guess(when_str)
        if when is None:
            when = get_ist_now()
        out.append(Item('NSE', symbol, headline, urlp, when))
    return out


# --- BSE ---

def fetch_bse(limit: int = 100) -> List[Item]:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json"})

    # Endpoint 1: Announcements (broad)
    today = get_ist_now().strftime('%Y%m%d')
    url = (
        "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
        f"?strCat=-1&strType=C&strFromDate={today}&strToDate={today}&strSearch=P&scripcode="
    )
    r = s.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and 'Table' in data:
        rows = data['Table']
    else:
        rows = data if isinstance(data, list) else []

    out: List[Item] = []
    for row in rows[:limit]:
        symbol = (row.get('SCRIP_CD') or row.get('Scripcode') or row.get('SC') or '')
        headline = row.get('HEADLINE') or row.get('HEAD_TEXT') or row.get('Newssub') or ''
        urlp = row.get('ATTACHMENTNAME') or row.get('PdfLink') or row.get('Url') or ''
        when_str = row.get('NEWS_DT') or row.get('DtTm') or row.get('NEWS_TIME') or ''
        when = _parse_dt_guess(when_str)
        if when is None:
            when = get_ist_now()
        out.append(Item('BSE', str(symbol), headline, urlp, when))
    return out


# --- helpers ---

def _parse_dt_guess(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    fmts = [
        "%d-%b-%Y %H:%M:%S",
        "%d %b %Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y",
        "%Y-%m-%d",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            pass
    return None
