"""Liste alle main_scheme-Slots, damit wir sie für A/B-Untersuchung vergleichen."""
from __future__ import annotations
import json
from pathlib import Path

REVIEW = Path(__file__).parent / "output" / "review" / "hood"
for pf in sorted(REVIEW.glob("*/*/parsed.json")):
    data = json.loads(pf.read_text(encoding="utf-8"))
    if data.get("type_code") in ("main_scheme", "side_scheme"):
        print(f"{pf.parent.relative_to(REVIEW)}  type={data['type_code']:11}  code={data.get('code')}  rot={data.get('rotation')}°  indicator={data.get('set_indicator_raw')[:60]!r}")
