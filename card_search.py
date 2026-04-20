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


def _fingerprint(card: dict) -> tuple:
    def norm(v):
        return None if v == "" else v
    return tuple(norm(card.get(f)) for f in _FINGERPRINT_FIELDS)


def search_cards(cards: list[dict], query: str) -> list[dict]:
    q = query.lower()

    def matches(c: dict, exact: bool) -> bool:
        if c.get("duplicate_of"):
            return False
        name = (c.get("name") or "").lower()
        real = (c.get("real_name") or "").lower()
        return (name == q or real == q) if exact else (q in name or q in real)

    hits = [c for c in cards if matches(c, exact=True)]
    if not hits:
        hits = [c for c in cards if matches(c, exact=False)]

    seen:      dict[tuple, dict]       = {}
    all_packs: dict[tuple, list[dict]] = {}
    for c in hits:
        fp = _fingerprint(c)
        if fp not in seen or c["code"] < seen[fp]["code"]:
            seen[fp] = c
        pack_entry = {
            "pack_name": c.get("pack_name", ""),
            "position":  c.get("position"),
            "quantity":  c.get("quantity"),
        }
        all_packs.setdefault(fp, []).append(pack_entry)

    result = []
    for fp, card in seen.items():
        card = dict(card)
        card["all_packs"] = all_packs[fp]
        result.append(card)
    return result
