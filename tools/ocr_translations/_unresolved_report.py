"""Erzeugt ein Protokoll der nicht erkannten Karten als Markdown."""
import json
from pathlib import Path

review_dir = Path(__file__).parent / "output" / "review" / "hood"
parsed_files = sorted(review_dir.glob("*/*/parsed.json"))

unresolved = []
for pf in parsed_files:
    d = json.loads(pf.read_text(encoding="utf-8"))
    if not d.get("code"):
        unresolved.append((pf, d))

out_path = Path(__file__).parent / "output" / "unresolved_report.md"
lines = []
lines.append("# Nicht erkannte Karten")
lines.append("")
lines.append(f"**{len(unresolved)} von {len(parsed_files)} Karten** ohne automatisch aufgelösten `code`.")
lines.append("")
lines.append("Spalten:")
lines.append("- **Bogen / Slot**: Pfad im Review-Verzeichnis")
lines.append("- **Rot.**: angewendete 90°-Rotation für Indikator-Suche")
lines.append("- **Deskew**: Schräglagen-Korrektur in Grad (0° = Karte war bereits axis-aligned)")
lines.append("- **Type**: aus Pack-JSON ermittelt (leer = Indikator nicht aufgelöst)")
lines.append("- **Indikator-Roh-OCR**: was Tesseract aus dem unteren Streifen gelesen hat")
lines.append("- **Set / Pos**: aus dem Indikator geparst (None = nicht parsbar)")
lines.append("")
lines.append("| # | Bogen / Slot | Rot. | Deskew | Type | Indikator (raw) | Set / Pos |")
lines.append("|---|---|---:|---:|---|---|---|")

for i, (pf, d) in enumerate(unresolved, 1):
    sheet = pf.parts[-3]
    slot = pf.parent.name
    rot = d.get("rotation", 0)
    deskew = d.get("deskew_angle", 0)
    typ = d.get("type_code") or "—"
    raw = (d.get("set_indicator_raw") or "").replace("\n", " | ").replace("|", "\\|").strip()
    if len(raw) > 80:
        raw = raw[:77] + "..."
    set_code = d.get("set_code") or "—"
    pos = d.get("set_position")
    set_pos = f"{set_code} / {pos}" if pos is not None else f"{set_code} / —"
    lines.append(f"| {i} | `{sheet}/{slot}` | {rot}° | {deskew}° | {typ} | `{raw}` | {set_pos} |")

lines.append("")
lines.append("## Vermutliche Ursachen pro Karte")
lines.append("")

# Group by likely cause
no_indicator = [u for u in unresolved if not (u[1].get("set_indicator_raw") or "").strip()]
unparseable = [u for u in unresolved if (u[1].get("set_indicator_raw") or "").strip() and u[1].get("set_position") is None]
unmappable = [u for u in unresolved if u[1].get("set_position") is not None and not u[1].get("set_code")]
no_code = [u for u in unresolved if u[1].get("set_code") and u[1].get("set_position") is not None and not u[1].get("code")]

def block(title: str, items: list, why: str) -> None:
    if not items:
        return
    lines.append(f"### {title} ({len(items)})")
    lines.append("")
    lines.append(why)
    lines.append("")
    for pf, d in items:
        sheet = pf.parts[-3]
        slot = pf.parent.name
        raw = (d.get("set_indicator_raw") or "").replace("\n", " | ").strip()[:100]
        lines.append(f"- `{sheet}/{slot}` — indicator_raw=`{raw}`")
    lines.append("")

block(
    "OCR fand gar keinen Indikator",
    no_indicator,
    "Tesseract liefert leeren String — vermutlich Banner zu klein, kontrastarm oder von Stat-Boxen verdeckt. Manuell aus `cropped.png` ablesen.",
)
block(
    "Indikator gelesen, aber Position nicht parsbar",
    unparseable,
    "Klammer-mit-Slash-Format `(n/m)` ist im OCR zu zerschossen. Manuell ablesen.",
)
block(
    "Set-Name lässt sich keinem `set_code` zuordnen",
    unmappable,
    "Fuzzy-Match in `mapping.resolve_set_code` schlägt fehl — eventuell deutscher Set-Name fehlt im DE→EN-Dict (`mapping.py:DE_TO_EN_SET_CODE`).",
)
block(
    "Set + Position bekannt, aber `code` nicht im Pack-JSON",
    no_code,
    "Diese Position existiert im englischen `hood_encounter.json` nicht (Hood-Set hat z.B. nur Positionen 1–14, deutsche Karten zeigen aber teils 15/16). Manuelle Code-Zuordnung nötig.",
)

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Geschrieben: {out_path}")
print(f"Unresolved: {len(unresolved)}/{len(parsed_files)}")
