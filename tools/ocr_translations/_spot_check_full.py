"""Spot-Check der Pilot-Karten aus dem Plan."""
from __future__ import annotations
import json
from pathlib import Path

# (Slot, erwarteter Type, erwarteter Card-Name)
TARGETS = [
    ("HoodSetGER_1/2_0", "villain",      "The Hood Stage III"),
    ("HoodSetGER_2/1_1", "minion",       "Madame Masque"),
    ("HoodSetGER_5/0_2", "attachment",   "Tech-Fäuste"),
    ("HoodSetGER_1/1_0", "main_scheme",  "Crime State / Verbrechensherrschaft (A)"),
    ("HoodSetGER_2/2_0", "main_scheme",  "Crime State / Verbrechensherrschaft (B)"),
]

review = Path(__file__).parent / "output" / "review" / "hood"

for slot, exp_type, label in TARGETS:
    pj = review / slot / "parsed.json"
    if not pj.exists():
        print(f"=== {label}  ({slot}) ===")
        print("  parsed.json fehlt!\n")
        continue
    d = json.loads(pj.read_text(encoding="utf-8"))
    print(f"=== {label}  ({slot}) ===")
    print(f"  code={d.get('code')}  type={d.get('type_code')}  rot={d.get('rotation')}deg")
    print(f"  name   : {d.get('name')!r}")
    print(f"  traits : {d.get('traits')!r}")
    text = d.get('text') or ''
    print(f"  text   : {text[:300]!r}{'...' if len(text) > 300 else ''}")
    flavor = d.get('flavor') or ''
    print(f"  flavor : {flavor[:200]!r}{'...' if len(flavor) > 200 else ''}")
    print()
