"""Vergleicht jede deutsche Übersetzung mit dem englischen Original.
Zeigt potenzielle Übersetzungsfehler nach Verdachtswert sortiert."""
import json, re, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TL = 'C:/Repos/demarvelcdb/translations_local'
EN_DIR = 'C:/Repos/marvelsdb-json-data/pack'

# EN→DE name fragments that should appear in DE translation when they appear in EN
# (proper nouns and trait keywords that don't change between languages)
KEEP_AS_IS = ['M.O.D.O.K.', 'A.I.M.', 'S.H.I.E.L.D.', 'Black Widow', 'Citizen V',
              'Baron Zemo', 'Apocalypse', 'X-Men', 'Magneto', 'Bishop', 'Magik',
              'Trevor Fitzroy', 'Bantam', 'Belasco', "S'ym", 'Witchfire', 'Darkchilde',
              'Sarah Garza', 'Songbird', 'Moonstone', 'Jolt', 'Joystick', 'Fixer',
              'Atlas', 'Blizzard', 'Batroc', 'MACH-IV', 'Adaptoid', 'Monica Rappaccini',
              'Maria Hill', 'Nick Fury']

# EN keywords that translate to specific German keywords (must appear in DE)
KEYWORD_MAP = {
    'When Revealed': ['Sobald aufgedeckt'],
    'Forced Response': ['Erzwungene Reaktion'],
    'Forced Interrupt': ['Erzwungene Unterbrechung'],
    'Hero Action': ['Held - Aktion', 'Held – Aktion', 'Held-Aktion'],
    'Hero Response': ['Held - Reaktion', 'Held – Reaktion'],
    'Hero Interrupt': ['Held - Unterbrechung', 'Held – Unterbrechung'],
    'Setup': ['Spielaufbau', 'Vorbereitung'],
    'Quickstrike': ['Erstschlag'],
    'Surge': ['Nachrüsten'],
    'Toughness': ['Zähigkeit'],
    'Stalwart': ['Standhaft', 'Gestählt'],
    'Guard': ['Wache'],
    'Patrol': ['Patrouille'],
    'Steady': ['Standhaft'],
    'Overkill': ['Overkill'],
    'Ranged': ['Fernkampf'],
    'Piercing': ['Durchdringend'],
    'Retaliate': ['Vergeltung'],
    'Restless': ['Unrast', 'Anstacheln'],
    'Villainous': ['Schurkisch'],
    'Victory': ['Sieg'],
    'Confused': ['verwirrt'],
    'Stunned': ['betäubt'],
    'main scheme': ['Hauptplan'],
    'side scheme': ['Nebenplan'],
    'attack': ['Angriff'],
    'thwart': ['Plan voran', 'Widerstand'],
}

# Symbol tokens — must appear identically in both
SYMBOLS = ['[star]', '[per_hero]', '[per_player]', '[boost]', '[crisis]',
           '[acceleration]', '[hazard]', '[amplify]', '[energy]', '[mental]',
           '[physical]', '[wild]']


def normalize(text):
    if not text:
        return ''
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_numbers(text):
    """Find all standalone numbers in text."""
    return re.findall(r'(?<![A-Za-z\d])(\d+)(?![A-Za-z])', text or '')


def count_symbols(text, symbol):
    return (text or '').count(symbol)


def audit_card(en, de):
    """Returns list of (severity, issue) tuples."""
    issues = []
    en_text = en.get('text', '') or ''
    de_text = de.get('text', '') or ''
    en_flavor = en.get('flavor', '') or ''
    de_flavor = de.get('flavor', '') or ''

    # 1. Symbol-Anzahl
    for sym in SYMBOLS:
        en_n = count_symbols(en_text, sym) + count_symbols(en_flavor, sym)
        de_n = count_symbols(de_text, sym) + count_symbols(de_flavor, sym)
        if en_n != de_n:
            issues.append((3, f"Symbol {sym}: EN={en_n}× DE={de_n}×"))

    # 2. Eigennamen (sollten in beiden vorkommen)
    for name in KEEP_AS_IS:
        if name in en_text and name not in de_text:
            issues.append((2, f"Eigenname '{name}' fehlt in DE-text"))

    # 3. Schlüsselwörter
    for en_kw, de_options in KEYWORD_MAP.items():
        if en_kw.lower() in en_text.lower():
            if not any(opt.lower() in de_text.lower() for opt in de_options):
                issues.append((2, f"Keyword '{en_kw}' → erwartet eines von {de_options} in DE"))

    # 4. Zahlen-Vergleich (in nicht-stage-Werten)
    en_nums = find_numbers(en_text)
    de_nums = find_numbers(de_text)
    if sorted(en_nums) != sorted(de_nums):
        issues.append((1, f"Zahlen unterschiedlich: EN={en_nums} DE={de_nums}"))

    # 5. Längen-Verhältnis
    if en_text and de_text:
        ratio = len(de_text) / len(en_text)
        if ratio < 0.6 or ratio > 1.8:
            issues.append((1, f"Längenverhältnis ungewöhnlich: DE/EN = {ratio:.2f} ({len(de_text)}/{len(en_text)})"))

    # 6. Flavor Vorhandensein
    if en_flavor and not de_flavor and len(en_flavor) > 30:
        issues.append((1, f"EN hat Flavor ({len(en_flavor)} chars), DE hat keinen"))

    # 7. Bullet points / list structure
    en_bullets = en_text.count('•') + en_text.count('* ') if en_text else 0
    de_bullets = de_text.count('•')
    if en_bullets != de_bullets and en_bullets > 0:
        issues.append((2, f"Bullet-Anzahl: EN={en_bullets} DE={de_bullets}"))

    return issues


def audit_pack(pack_name):
    en_path = f"{EN_DIR}/{pack_name}_encounter.json"
    de_path = f"{TL}/{pack_name}_encounter.json"
    if not os.path.exists(de_path):
        return
    en = {c['code']: c for c in json.load(open(en_path, encoding='utf-8'))}
    de = {c['code']: c for c in json.load(open(de_path, encoding='utf-8'))}

    print(f"\n{'='*70}\nPack: {pack_name}_encounter ({len(de)} DE entries)\n{'='*70}")

    findings = []
    for code, de_card in de.items():
        en_card = en.get(code)
        if not en_card:
            continue
        issues = audit_card(en_card, de_card)
        if issues:
            findings.append((max(s for s, _ in issues), code, en_card, de_card, issues))

    findings.sort(key=lambda f: -f[0])
    for severity, code, en_card, de_card, issues in findings:
        print(f"\n--- {code} {de_card.get('name')} (sev={severity}) ---")
        for s, msg in sorted(issues, key=lambda i: -i[0]):
            print(f"  [{s}] {msg}")


if __name__ == '__main__':
    packs = sys.argv[1:] or ['aos', 'bp', 'falcon', 'silk', 'winter', 'aoa', 'hood']
    for p in packs:
        audit_pack(p)
