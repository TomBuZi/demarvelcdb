"""Zeigt Status-Übersicht über die OCR-Review-Artefakte eines Packs."""
import json
import sys
from collections import defaultdict
from pathlib import Path

pack = sys.argv[1] if len(sys.argv) > 1 else "hood"
review_dir = Path(__file__).parent / "output" / "review" / pack

parsed_files = sorted(review_dir.glob("*/*/parsed.json"))
print(f"Pack: {pack}")
print(f"Review-Verzeichnis: {review_dir}")
print(f"Karten gesamt: {len(parsed_files)}")
print()

per_sheet = defaultdict(list)
no_code = []
with_code = []

for pf in parsed_files:
    sheet = pf.parts[-3]
    data = json.loads(pf.read_text(encoding="utf-8"))
    per_sheet[sheet].append(data)
    if data.get("code"):
        with_code.append(data)
    else:
        no_code.append(data)

print(f"  mit auto-mapped code: {len(with_code)}")
print(f"  OHNE code (Review erforderlich): {len(no_code)}")
print()

print("Pro Bogen:")
for sheet in sorted(per_sheet):
    n = len(per_sheet[sheet])
    n_code = sum(1 for d in per_sheet[sheet] if d.get("code"))
    print(f"  {sheet}: {n} Karten, {n_code} mit code")

print()
print("Karten OHNE auto-mapped code (Beispiele):")
for d in no_code[:15]:
    name_preview = (d.get("name") or "")[:40]
    print(f"  [{d['sheet']} r{d['row']}c{d['col']}] name={name_preview!r} indicator_raw={d.get('set_indicator_raw')[:40]!r}")
print()
print("Karten MIT auto-mapped code (Beispiele):")
for d in with_code[:10]:
    print(f"  code={d['code']} name={d.get('name','')[:40]!r}")
