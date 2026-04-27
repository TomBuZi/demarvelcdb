"""Quick check: physical-card list for the_hood + lookups (10/16), (15/16), (16/16)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mapping

pm = mapping.PackMapper("hood")
pm.load()

print("the_hood physical card sequence:")
for i, code in enumerate(pm._physical_by_set["the_hood"], 1):
    card = pm.get_card(code)
    print(f"  ({i:>2}/16)  {code}  {card['type_code']:<14}  {card['name']}")

print()
for indicator in (1, 9, 10, 11, 14, 15, 16, 17):
    print(f"  find_code(the_hood, {indicator:>2}) → {pm.find_code('the_hood', indicator)}")

print()
print("Andere Sets:")
for sc in ("state_of_emergency", "ransacked_armory", "wrecking_crew_modular", "crossfire_crew"):
    print(f"  {sc}: {pm._physical_by_set[sc]}")
