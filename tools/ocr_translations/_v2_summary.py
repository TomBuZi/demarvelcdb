"""V2 review summary with type breakdown and unresolved-by-rotation."""
import json
from collections import Counter, defaultdict
from pathlib import Path

review_dir = Path(__file__).parent / "output" / "review" / "hood"
parsed_files = sorted(review_dir.glob("*/*/parsed.json"))

per_sheet: dict[str, list[dict]] = defaultdict(list)
type_count: Counter = Counter()
type_resolved: Counter = Counter()
unresolved: list[dict] = []

for pf in parsed_files:
    sheet = pf.parts[-3]
    data = json.loads(pf.read_text(encoding="utf-8"))
    per_sheet[sheet].append(data)
    typ = data.get("type_code") or "(unresolved)"
    type_count[typ] += 1
    if data.get("code"):
        type_resolved[typ] += 1
    else:
        unresolved.append(data)

print(f"Karten gesamt:  {len(parsed_files)}")
print(f"Mit code:       {sum(type_resolved.values())}")
print(f"Ohne code:      {len(unresolved)}")
print()
print("Pro Type:")
for typ, n in sorted(type_count.items()):
    res = type_resolved.get(typ, 0)
    print(f"  {typ:<14} {res}/{n}")
print()
print("Pro Bogen (mit/gesamt):")
for sheet in sorted(per_sheet):
    n = len(per_sheet[sheet])
    nc = sum(1 for d in per_sheet[sheet] if d.get("code"))
    print(f"  {sheet:<20} {nc}/{n}")
print()
print("Unresolved (alle):")
for d in unresolved:
    raw = (d.get("set_indicator_raw") or "").replace("\n", " | ")[:60]
    print(f"  [{d['sheet']} r{d['row']}c{d['col']}] rot={d.get('rotation', 0):>3}° indicator_raw={raw!r}")
