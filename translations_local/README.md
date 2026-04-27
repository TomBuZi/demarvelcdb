# Lokale Übersetzungen (Overlay)

Dieser Ordner enthält deutsche Übersetzungen für Encounter-Karten, die in
`zzorba/marvelsdb-json-data` (noch) fehlen oder lokal korrigiert werden sollen.

Format pro Datei: `<pack_code>_encounter.json` — exakt das gleiche Schema, das
zzorba unter `translations/de/pack/` verwendet:

```json
[
  {
    "code": "24001",
    "name": "The Hood",
    "text": "<i>Falsches Spiel</i> – <b>Spezial</b>: ...",
    "traits": "Krimineller.",
    "flavor": "<i>„Wenn du nicht ...\"</i>"
  }
]
```

`bot.py` lädt diese Dateien in `_load_encounter_pack` als zweites Overlay
(nach den GitHub-Übersetzungen). Lokale Werte gewinnen gegen GitHub-Werte für
die gleichen Felder (`name`, `text`, `traits`, `flavor`, `subname`).

## Erzeugung

Generiert aus den Card-Scans unter `C:\Repos\Sourcen_Scans\` per OCR-Tool:
`tools/ocr_translations/` — siehe README dort.
