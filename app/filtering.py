# file: app/filtering.py
from __future__ import annotations
import re
from typing import Dict, Any
from .constants import CA_KEYWORDS

PAT = re.compile(r"|".join(rf"\b{re.escape(k)}\b" for k in CA_KEYWORDS), re.I)


def is_corporate_action(item: Dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(k, ""))
        for k in ("headline", "subject", "category", "details")
    )
    return bool(PAT.search(text))
