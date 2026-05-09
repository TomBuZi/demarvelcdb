import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import importlib.util
spec = importlib.util.spec_from_file_location("ra", "_reverse_audit.py")
_reverse_audit = importlib.util.module_from_spec(spec)
# Don't run module-level code that re-wraps stdout
import re
src = open("_reverse_audit.py", encoding='utf-8').read()
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')", "")
exec(compile(src, "_reverse_audit.py", "exec"), _reverse_audit.__dict__)
en = {c['code']: c for c in json.load(open('C:/Repos/marvelsdb-json-data/pack/aoa_encounter.json', encoding='utf-8'))}
de = {c['code']: c for c in json.load(open('C:/Repos/demarvelcdb/translations_local/aoa_encounter.json', encoding='utf-8'))}
for code, dec in de.items():
    enc = en.get(code)
    if not enc: continue
    issues = _reverse_audit.audit_card(enc, dec)
    for s, msg in issues:
        if 'Guard' in msg or 'Toughness' in msg or 'Stalwart' in msg or 'Steady' in msg or "'Magik'" in msg or "'Bishop'" in msg:
            print(f'{code} {dec["name"]}: {msg}')
