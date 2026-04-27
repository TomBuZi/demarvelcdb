from difflib import SequenceMatcher

_FINGERPRINT_FIELDS = (
    "name", "real_name", "subname",
    "type_code", "faction_code",
    "cost", "cost_per_hero",
    "text", "real_text",
    "traits", "real_traits",
    "health", "health_per_hero", "health_per_group", "health_star",
    "attack", "attack_star", "attack_cost",
    "thwart", "thwart_star", "thwart_cost",
    "defense", "defense_star",
    "recover", "recover_star",
    "hand_size",
    "resource_energy", "resource_physical", "resource_mental", "resource_wild",
    "base_threat", "base_threat_fixed", "base_threat_per_group",
    "escalation_threat", "escalation_threat_fixed", "escalation_threat_star",
    "threat_fixed", "threat_per_group", "threat_star",
    "scheme_star", "boost_star",
    "deck_limit",
    "is_unique", "permanent", "double_sided",
)

_FUZZY_THRESHOLD = 0.5
_FUZZY_LIMIT     = 5


def _fingerprint(card: dict) -> tuple:
    def norm(v):
        return None if v == "" else v
    return tuple(norm(card.get(f)) for f in _FINGERPRINT_FIELDS)


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _decorate(hits: list[dict]) -> list[dict]:
    seen:      dict[tuple, dict]       = {}
    all_packs: dict[tuple, list[dict]] = {}
    order:     list[tuple]             = []
    for c in hits:
        fp = _fingerprint(c)
        if fp not in seen:
            seen[fp] = c
            order.append(fp)
        elif c["code"] < seen[fp]["code"]:
            seen[fp] = c
        all_packs.setdefault(fp, []).append({
            "pack_name": c.get("pack_name", ""),
            "position":  c.get("position"),
            "quantity":  c.get("quantity"),
        })

    result = []
    for fp in order:
        card = dict(seen[fp])
        card["all_packs"] = all_packs[fp]
        result.append(card)
    return result


def search_cards(cards: list[dict], query: str) -> tuple[str, list[dict]]:
    """Suche in drei Stufen: exakter Name → Teilstring → Fuzzy-Top-5.

    Rückgabe: ("exact"|"substring"|"fuzzy"|"none", treffer)
    """
    q = query.lower()

    def matches(c: dict, exact: bool) -> bool:
        if c.get("duplicate_of"):
            return False
        name = (c.get("name") or "").lower()
        real = (c.get("real_name") or "").lower()
        return (name == q or real == q) if exact else (q in name or q in real)

    hits = [c for c in cards if matches(c, exact=True)]
    if hits:
        return ("exact", _decorate(hits))

    hits = [c for c in cards if matches(c, exact=False)]
    if hits:
        return ("substring", _decorate(hits))

    # Fuzzy: pro Kandidat die beste Ratio gegen Name oder Real-Name; nach Score
    # absteigend dedupen über Fingerprint, max. 5 Ergebnisse.
    scored = []
    for c in cards:
        if c.get("duplicate_of"):
            continue
        name = (c.get("name") or "").lower()
        real = (c.get("real_name") or "").lower()
        r = max(_ratio(q, name), _ratio(q, real))
        if r >= _FUZZY_THRESHOLD:
            scored.append((r, c))
    scored.sort(key=lambda t: -t[0])

    seen_fp: set[tuple] = set()
    top: list[dict] = []
    for _r, c in scored:
        fp = _fingerprint(c)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        top.append(c)
        if len(top) >= _FUZZY_LIMIT:
            break

    if not top:
        return ("none", [])
    return ("fuzzy", _decorate(top))
