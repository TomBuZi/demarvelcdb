"""Sucht in allen indicator_raw und attempts.json nach `\\d+[AB]`-Suffix.

Damit sehen wir, ob auf den Bögen tatsächlich B-Seiten von Hauptplänen
zu finden sind oder nur A-Seiten gescannt wurden.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

REVIEW = Path(__file__).parent / "output" / "review" / "hood"
SUFFIX_RE = re.compile(r"\b(\d+[AB])\b")

print("=== indicator_raw mit \\d+[AB]-Suffix ===")
for pf in sorted(REVIEW.glob("*/*/parsed.json")):
    data = json.loads(pf.read_text(encoding="utf-8"))
    raw = data.get("set_indicator_raw", "")
    matches = SUFFIX_RE.findall(raw)
    if matches:
        print(f"  {pf.parent.relative_to(REVIEW)}  type={data.get('type_code')}  code={data.get('code')}  suffixes={matches}")

print("\n=== attempts.json mit \\d+B (nur B-Vorkommen) ===")
for pf in sorted(REVIEW.glob("*/*/attempts.json")):
    attempts = json.loads(pf.read_text(encoding="utf-8"))
    for att in attempts:
        text = att.get("raw_text") or ""
        b_matches = re.findall(r"\b\d+B\b", text)
        if b_matches:
            print(f"  {pf.parent.relative_to(REVIEW)}  rot={att['rotation_deg']}°  strip={att['strip_key']}  B-suffixes={b_matches}  raw={text[:80]!r}")
