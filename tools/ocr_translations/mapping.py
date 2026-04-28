"""Mapping vom Set-Indikator (z.B. 'THE HOOD (1/4)') zur Card-ID (`code`).

Lädt das englische Pack-JSON aus zzorba/marvelsdb-json-data und baut einen
Index `(set_code, set_position) -> code`. Set-Namen, die OCR aus dem
Set-Indikator liest, werden auf den `set_code` der englischen Karten
normalisiert.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

import requests

GITHUB_RAW = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master"

# Manuelle Übersetzungen, wenn der deutsche Set-Name keine offensichtliche
# Ähnlichkeit zum englischen `set_code` hat. Schlüssel sind normalisierte
# (lowercased, snake-case) deutsche Bezeichnungen, Werte sind die englischen
# `set_code`-Strings.
DE_TO_EN_SET_CODE: dict[str, str] = {
    # Hood-Pack
    "chaos_auf_den_strassen": "streets_of_mayhem",
    "chaos_auf_den_straen": "streets_of_mayhem",  # OCR liest 'ß' oft als 'en'
    "geplundertes_waffenlager": "ransacked_armory",
    "geplunderles_waffenlager": "ransacked_armory",  # OCR-Verlesungen
    "ausnahmezustand": "state_of_emergency",

    # Age of Apocalypse (Erstkontakt — wird nach Visualize-Lauf justiert)
    "apokalypse":            "apocalypse",
    "vier_reiter":           "four_horsemen",
    "die_vier_reiter":       "four_horsemen",
    "klan_akkaba":           "clan_akkaba",
    "pralaten":              "prelates",
    "praelaten":             "prelates",
    "dunkle_reiter":         "dark_riders",
    "dunkles_biest":         "dark_beast",
    "blauer_mond":           "blue_moon",
    "wildes_land":           "savage_land",
    "dystopischer_albtraum": "dystopian_nightmare",
    "albtraum_der_dystopie": "dystopian_nightmare",
    "aufseher":              "overseer",
    "jagdhunde":             "hounds",
    "zelestiale_technik":    "celestial_tech",
    "zelestiale_techniken":  "celestial_tech",
    # Mission/Campaign-Sets (bleiben oft englisch oder sind direkt mappable)
    # en_sabah_nur, infinites, magik, magik_nemesis, bishop, bishop_nemesis,
    # genosha, age_of_apocalypse, aoa_campaign, aoa_mission, standard_iii
    # → werden via direktem Substring-Match aufgelöst
}


@dataclass
class CardRef:
    code: str
    set_code: str
    set_position: int
    name: str
    type_code: str


class PackMapper:
    def __init__(self, pack_code: str):
        self.pack_code = pack_code
        self._cards: list[CardRef] = []
        self._by_pos: dict[tuple[str, int], list[CardRef]] = {}
        self._by_code: dict[str, dict] = {}
        self._set_codes: set[str] = set()
        # Pro Set: expandierte Liste der physisch gedruckten Karten in der
        # Reihenfolge, wie sie auf dem Indikator (n/m) durchnummeriert sind.
        # a/b-Doppelseiter zählen als 1 physische Karte; quantity>1 erzeugt
        # mehrere Einträge desselben Codes.
        self._physical_by_set: dict[str, list[str]] = {}

    def load(self) -> None:
        url = f"{GITHUB_RAW}/pack/{self.pack_code}_encounter.json"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        for entry in raw:
            if "set_code" not in entry or "set_position" not in entry:
                continue
            ref = CardRef(
                code=entry["code"],
                set_code=entry["set_code"],
                set_position=int(entry["set_position"]),
                name=entry.get("name", ""),
                type_code=entry.get("type_code", ""),
            )
            self._cards.append(ref)
            self._by_pos.setdefault((ref.set_code, ref.set_position), []).append(ref)
            self._by_code[entry["code"]] = entry
            self._set_codes.add(ref.set_code)

        # Für jedes Set die "physikalische" Karten-Liste bauen (quantity-aware,
        # a/b-Doppelseiter zusammengefasst). Das ist die Reihenfolge, die der
        # Indikator (n/m) durchnummeriert.
        for set_code in self._set_codes:
            self._physical_by_set[set_code] = self._build_physical_list(set_code, raw)

    def _build_physical_list(self, set_code: str, all_entries: list[dict]) -> list[str]:
        """Liefert die expandierte Code-Liste für ein Set in Indikator-
        Reihenfolge:
          - Sortierung nach `set_position` aufsteigend
          - Karten mit gleicher `set_position` (a/b-Sides) → 1 Eintrag,
            kanonisiert auf den Code mit kleinster Suffix (also 'a' vor 'b')
          - Quantity > 1 → mehrere Einträge desselben Codes hintereinander
        """
        in_set = [e for e in all_entries if e.get("set_code") == set_code]
        # Gruppieren nach set_position, dann a/b kollabieren (kleinster Code wird Repräsentant).
        by_pos: dict[int, list[dict]] = {}
        for e in in_set:
            by_pos.setdefault(int(e["set_position"]), []).append(e)
        physical: list[str] = []
        for pos in sorted(by_pos.keys()):
            entries = sorted(by_pos[pos], key=lambda e: e["code"])
            rep = entries[0]
            qty = int(rep.get("quantity", 1))
            for _ in range(qty):
                physical.append(rep["code"])
        return physical

    def get_card(self, code: str | None) -> dict | None:
        if not code:
            return None
        return self._by_code.get(code)

    def get_type_code(self, code: str | None) -> str | None:
        card = self.get_card(code)
        return card.get("type_code") if card else None

    @staticmethod
    def normalize_set_name(raw: str) -> str:
        """Wandelt OCR-Output wie 'THE HOOD' oder 'BEASTY BOYS' in einen
        kanonischen Snake-Case-Schlüssel um, der mit `set_code` vergleichbar ist.

        Reihenfolge ist wichtig: erst Whitespace (inkl. Newline) zu Space
        normalisieren, dann deutsche Umlaute auf ASCII abbilden, ERST DANN
        Sonderzeichen entfernen — sonst klebt OCR-Vor-/Nachsatz an den
        Wörtern (z.B. "leo\\n\\ngeplündertes\\nwaffenlager" wäre vorher zu
        "leogeplnderteswaffenlager" mutiert).
        """
        if not raw:
            return ""
        s = raw.strip().lower()
        s = re.sub(r"\s+", " ", s)
        s = (
            s.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
        )
        s = re.sub(r"[^a-z0-9 ]+", "", s)
        s = re.sub(r"\s+", "_", s).strip("_")
        return s

    def resolve_set_code(self, ocr_set_name: str, hint: str | None = None) -> str | None:
        """Mappt einen OCR-Set-Namen auf einen `set_code`. Stufenweise:
        1) direkter Treffer, 2) Substring beider Richtungen, 3) DE→EN-Dict
        für deutsche Set-Namen ohne englische Verwandtschaft, 4) close-match
        (Tippfehler-tolerant), 5) Token-exact-Match (z.B. 'm boys' → 'beasty_boys').
        """
        candidate = self.normalize_set_name(ocr_set_name)
        if not candidate:
            if hint and hint in self._set_codes:
                return hint
            return None

        # 1) direkter Treffer
        if candidate in self._set_codes:
            return candidate

        # 2) Substring (z.B. 'hood' → 'the_hood', 'the_hood' → 'the_hood_x')
        for code in self._set_codes:
            if candidate in code or code in candidate:
                return code

        # 3) DE→EN-Übersetzungstabelle
        translated = DE_TO_EN_SET_CODE.get(candidate)
        if translated and translated in self._set_codes:
            return translated
        # auch Substring-Suche im Übersetzungs-Dict
        for de_key, en_code in DE_TO_EN_SET_CODE.items():
            if (de_key in candidate or candidate in de_key) and en_code in self._set_codes:
                return en_code

        # 4) close-match — fängt OCR-Tippfehler ('the_hold' → 'the_hood',
        # 'wrechng_crew' → 'wrecking_crew_modular')
        matches = difflib.get_close_matches(candidate, list(self._set_codes), n=1, cutoff=0.6)
        if matches:
            return matches[0]

        # 5) Token-Match: kanonisiere beide Strings auf Tokens und such Treffer
        cand_tokens = [t for t in candidate.split("_") if len(t) >= 3]
        for code in self._set_codes:
            code_tokens = code.split("_")
            for ct in cand_tokens:
                if ct in code_tokens:
                    return code
                # fuzzy auf Token-Ebene für leichte OCR-Verlesungen
                for st in code_tokens:
                    if len(st) >= 4 and difflib.SequenceMatcher(None, ct, st).ratio() >= 0.85:
                        return code

        if hint and hint in self._set_codes:
            return hint
        return None

    @staticmethod
    def parse_set_indicator(raw: str) -> tuple[str, int | None]:
        """Zerlegt einen OCR-Output wie 'BEASTY BOYS (3/4)' in (set_name,
        set_position). Wenn die Position nicht eindeutig erkennbar ist,
        liefert es `None` zurück und das Review muss eingreifen.
        """
        if not raw:
            return "", None
        # Pattern: alles vor der ersten Klammer als Name, Zahl/Zahl in der Klammer
        m = re.search(r"^(.*?)[\s(]*\(?\s*(\d+)\s*[/\\]\s*\d+\s*\)?", raw)
        if m:
            return m.group(1).strip(), int(m.group(2))
        # Fallback: suche irgendwo ein "<n>/<m>"
        m2 = re.search(r"(\d+)\s*[/\\]\s*\d+", raw)
        if m2:
            name_part = raw[: m2.start()].strip()
            return name_part, int(m2.group(1))
        return raw.strip(), None

    @staticmethod
    def parse_card_suffix(raw: str) -> str | None:
        """Sucht nach dem Card-Code-Suffix (`4A`, `5B`, `13` etc.), der bei
        Marvel-Champions-Karten unten rechts neben dem Copyright-Footer
        gedruckt ist. Bei Doppelseitern (a/b) ist das die einzige Stelle, an
        der die Seite eindeutig markiert ist — der `(n/m)`-Indikator fehlt
        auf B-Seiten oft komplett.

        Liefert das Suffix in Lowercase (z.B. 'b'-Seite → '4b'), oder `None`
        wenn kein passendes Muster gefunden wurde. Wir bevorzugen Treffer
        mit Buchstabe (eindeutiger), nehmen aber auch reine Zahlen-Suffixe.
        """
        if not raw:
            return None
        # OCR liest oft Müll davor (z.B. `© MARVEL © 2021 FFG AA 6A`); wir
        # suchen nach dem letzten Token im Format <Zahl><Buchstabe?> mit
        # mindestens 1 Ziffer.
        candidates = re.findall(r"\b(\d+)([AB])\b", raw, flags=re.IGNORECASE)
        if candidates:
            num, letter = candidates[-1]
            return f"{num}{letter}".lower()
        # Reines Zahlen-Suffix als Fallback (für Karten ohne A/B): nur am
        # Ende, damit wir nicht das `(n/m)` der Mitte wiedereinfangen.
        m = re.search(r"\b(\d{1,3})\s*$", raw.rstrip())
        if m:
            return m.group(1).lower()
        return None

    def find_code_by_suffix(self, visible_suffix: str) -> str | None:
        """Findet den Card-Code, dessen Identifier auf das gegebene Suffix
        endet. `visible_suffix` ist Lowercase (z.B. 'b' für B-Seite, '4a',
        '13'). Erst exakte Endung, dann Endung ohne Pack-Prefix.

        Gibt nur dann einen Code zurück, wenn das Suffix EINDEUTIG einem
        Code zuzuordnen ist — sonst `None`, damit wir nicht raten.
        """
        if not visible_suffix:
            return None
        target = visible_suffix.lower()
        matches = [
            c for c in self._by_code
            if c.lower().endswith(target)
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # Suffix ist mehrdeutig — bevorzuge den kürzesten Code (am
            # nächsten zum Suffix), den längeren ignorieren wir.
            matches.sort(key=len)
            shortest_len = len(matches[0])
            shortlist = [m for m in matches if len(m) == shortest_len]
            if len(shortlist) == 1:
                return shortlist[0]
        return None

    def find_code(self, set_code: str, indicator_position: int) -> str | None:
        """Schlägt den Card-`code` aus einer Indikator-Position (n in `(n/m)`)
        nach. Verwendet die quantity-aware physische Karten-Liste, sodass
        gedruckte Mehrfach-Kopien (z.B. Upper Hand qty=3 → Indikator 14, 15, 16)
        und a/b-Doppelseiter korrekt aufgelöst werden.

        Falls die Position außerhalb der physischen Liste liegt, fallen wir
        auf den klassischen `set_position`-Lookup zurück — als Notnagel für
        Sets, deren `quantity`-Daten in zzorbas JSON nicht stimmen.
        """
        physical = self._physical_by_set.get(set_code, [])
        if 1 <= indicator_position <= len(physical):
            return physical[indicator_position - 1]
        # Fallback: alter set_position-Lookup
        refs = self._by_pos.get((set_code, indicator_position), [])
        if refs:
            return refs[0].code
        return None

    def all_cards(self) -> list[CardRef]:
        return list(self._cards)
