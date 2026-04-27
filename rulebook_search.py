import json
import os
from difflib import SequenceMatcher

_RULEBOOK: list[dict] | None = None

_FUZZY_THRESHOLD = 0.5
_FUZZY_LIMIT     = 5


def load_rulebook() -> list[dict]:
    global _RULEBOOK
    if _RULEBOOK is None:
        path = os.path.join(os.path.dirname(__file__), "rulebook_entries.json")
        with open(path, encoding="utf-8") as f:
            _RULEBOOK = json.load(f)
    return _RULEBOOK


def search_rules(query: str) -> tuple[str, list[dict]]:
    """Suche in drei Stufen: exakter Titel → Teilstring → Fuzzy-Top-5.

    Rückgabe: ("exact"|"substring"|"fuzzy"|"none", treffer)
    """
    entries = load_rulebook()
    q = query.strip().upper()

    exact = [e for e in entries if e["title"] == q]
    if exact:
        return ("exact", exact)

    substring = [e for e in entries if q in e["title"]]
    if substring:
        return ("substring", substring)

    q_lower = q.lower()
    scored = []
    for e in entries:
        r = SequenceMatcher(None, q_lower, e["title"].lower()).ratio()
        if r >= _FUZZY_THRESHOLD:
            scored.append((r, e))
    scored.sort(key=lambda t: -t[0])
    top = [e for _r, e in scored[:_FUZZY_LIMIT]]
    if not top:
        return ("none", [])
    return ("fuzzy", top)
