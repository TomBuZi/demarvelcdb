"""Schaut sich die Felder pro Karte im Hood-Pack-JSON an, mit Fokus auf
`quantity`, `set_position` und mögliche Duplikate-Hinweise."""
import json
import requests
from collections import defaultdict

URL = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master/pack/hood_encounter.json"
cards = requests.get(URL).json()

print(f"Total Einträge im JSON: {len(cards)}")
print()

# Welche Felder kommen überhaupt vor?
all_fields: set[str] = set()
for c in cards:
    all_fields.update(c.keys())
print("Vorhandene Felder:", sorted(all_fields))
print()

# Sets mit Set-Größen-Übersicht
sets = defaultdict(list)
for c in cards:
    sets[c.get("set_code", "?")].append(c)

print("=== the_hood Set im Detail ===")
for c in sorted(sets.get("the_hood", []), key=lambda x: (x.get("set_position", 0), x.get("code", ""))):
    qty = c.get("quantity", "?")
    pos = c.get("set_position", "?")
    code = c.get("code", "?")
    typ = c.get("type_code", "?")
    name = c.get("name", "?")
    dup = c.get("duplicate_of") or c.get("double_sided") or ""
    print(f"  pos={pos}  qty={qty}  code={code:<8}  type={typ:<14}  name={name}  extras={dup}")

# Summe der quantity-Werte pro Set, um die "(n/m)"-Nenner zu prüfen
print()
print("=== Set-Größen via quantity-Summe ===")
for sc, cs in sorted(sets.items()):
    total_qty = sum(c.get("quantity", 0) for c in cs)
    n_entries = len(cs)
    n_unique_pos = len(set(c.get("set_position") for c in cs))
    print(f"  {sc}: {n_entries} Einträge, {n_unique_pos} Positionen, sum(quantity)={total_qty}")

# Beispiel-Karte komplett (für komplette Schema-Übersicht)
print()
print("=== Beispiel: komplette Karte (Madame Masque) ===")
for c in cards:
    if c.get("code") == "24010":
        print(json.dumps(c, ensure_ascii=False, indent=2))
        break
