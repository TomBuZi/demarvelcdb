import json
import os

_RULEBOOK: list[dict] | None = None


def load_rulebook() -> list[dict]:
    global _RULEBOOK
    if _RULEBOOK is None:
        path = os.path.join(os.path.dirname(__file__), "rulebook_entries.json")
        with open(path, encoding="utf-8") as f:
            _RULEBOOK = json.load(f)
    return _RULEBOOK


def search_rules(query: str) -> list[dict]:
    entries = load_rulebook()
    q = query.strip().upper()

    exact = [e for e in entries if e["title"] == q]
    if exact:
        return exact

    return [e for e in entries if q in e["title"]]
