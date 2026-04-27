"""Prüfen ob die vermuteten B-Seiten 2_0/2_1/2_2 jetzt resolved sind."""
from __future__ import annotations
import json
from pathlib import Path

rd = Path(__file__).parent / "output" / "review" / "hood" / "HoodSetGER_2"
for p in sorted(rd.glob("2_*/parsed.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d.get("set_indicator_raw", "")
    print(f"{p.parent.name}:")
    print(f"  type={d.get('type_code')}  code={d.get('code')}  rot={d.get('rotation')}deg")
    print(f"  raw_indicator (last 50): {raw[-50:]!r}")
    print()
