"""Sammelt manuell von Claude erzeugte Karten-Übersetzungen in einer JSON-Datei.

Nutzung (aus dem Code heraus aufgerufen):
    add_cards([{...}, {...}])     # liefert Liste mit Erfolgs-Statistik
    list_pending()                # listet noch nicht erfasste Slots
    get_done_codes()              # Set bereits erfasster Codes
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent
REVIEW = ROOT / "output" / "review" / "hood"
OUT = ROOT / "output" / "hood_encounter_claude.json"

ZZORBA_FIELDS = ("code", "name", "text", "traits", "flavor", "subname")


def load_existing() -> list[dict]:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))
    return []


def save(entries: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def add_cards(new_cards: list[dict]) -> dict:
    """Fügt neue Karten hinzu. Bei doppelten Codes wird der neue Eintrag
    ignoriert (für resumability nach Mehrfach-Runs).
    """
    existing = load_existing()
    seen = {c["code"] for c in existing}
    added, skipped = [], []
    for c in new_cards:
        if not c.get("code"):
            skipped.append((c.get("name", "?"), "kein code"))
            continue
        if c["code"] in seen:
            skipped.append((c["code"], "schon vorhanden"))
            continue
        clean = {f: c[f] for f in ZZORBA_FIELDS if c.get(f)}
        clean["code"] = c["code"]
        existing.append(clean)
        seen.add(c["code"])
        added.append(c["code"])
    save(existing)
    return {"added": added, "skipped": skipped, "total": len(existing)}


def get_done_codes() -> set[str]:
    return {c["code"] for c in load_existing()}


def list_all_slots() -> list[dict]:
    """Aus den parsed.json: alle 69 Slots mit (slot_path, code, type_code, sheet)."""
    out = []
    for pj in sorted(REVIEW.glob("*/*/parsed.json")):
        d = json.loads(pj.read_text(encoding="utf-8"))
        out.append({
            "slot": str(pj.parent.relative_to(REVIEW)).replace("\\", "/"),
            "code": d.get("code"),
            "type_code": d.get("type_code"),
            "sheet": d.get("sheet"),
            "indicator_raw": d.get("set_indicator_raw", ""),
        })
    return out


def list_pending() -> list[dict]:
    done = get_done_codes()
    return [s for s in list_all_slots() if s["code"] not in done]


def status() -> str:
    all_slots = list_all_slots()
    done_codes = get_done_codes()
    by_sheet: dict[str, list[str]] = {}
    for s in all_slots:
        by_sheet.setdefault(s["sheet"], []).append(s["code"])
    lines = [
        f"Erfasst: {len(done_codes)}/{len(all_slots)} Karten",
        "Pro Bogen:",
    ]
    for sheet, codes in sorted(by_sheet.items()):
        n_done = sum(1 for c in codes if c in done_codes)
        lines.append(f"  {sheet}: {n_done}/{len(codes)}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(status())
    elif cmd == "list-all":
        for s in list_all_slots():
            print(f"  {s['slot']:30}  code={s['code']:8}  type={s['type_code']:11}  sheet={s['sheet']}")
    elif cmd == "list-pending":
        for s in list_pending():
            print(f"  {s['slot']:30}  code={s['code']:8}  type={s['type_code']:11}")
    elif cmd == "reset":
        if OUT.exists():
            OUT.unlink()
        print(f"Gelöscht: {OUT}")
    else:
        print(f"Unknown command: {cmd}")
