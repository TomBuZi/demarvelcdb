# OCR-Tool: Deutsche Übersetzungen aus Karten-Scans

Erzeugt aus Bogen-Scans deutscher Marvel-Champions-Karten (z.B. unter `C:\Repos\Sourcen_Scans\Loindir\`) eine lokale `<pack>_encounter.json` im zzorba-Schema, die der Discord-Bot als Overlay über die englischen GitHub-Daten legt.

## Setup (einmalig)

1. **Tesseract OCR installieren** (Windows)
   ```powershell
   winget install --id UB-Mannheim.TesseractOCR --silent --accept-source-agreements --accept-package-agreements
   ```
   Standard-Installpfad ist `C:\Program Files\Tesseract-OCR\tesseract.exe`. Falls Tesseract anderswo liegt, Umgebungsvariable `TESSERACT_CMD` setzen oder die Konstante in `extract.py` anpassen.

2. **Sprachdaten** (`deu`, `eng`, `osd`)

   Liegen bereits in `tessdata/` neben `extract.py` (per `tessdata_best`). Falls der Ordner verloren geht, neu befüllen:
   ```powershell
   Copy-Item "C:\Program Files\Tesseract-OCR\tessdata\eng.traineddata" tessdata\
   Copy-Item "C:\Program Files\Tesseract-OCR\tessdata\osd.traineddata" tessdata\
   Invoke-WebRequest "https://github.com/tesseract-ocr/tessdata_best/raw/main/deu.traineddata" -OutFile tessdata\deu.traineddata
   ```
   `extract.py` ruft Tesseract automatisch mit `--tessdata-dir` auf diesen Ordner auf.

3. **Python-Abhängigkeiten**
   ```bash
   pip install -r requirements.txt
   ```

## Bedienung

```bash
# Schritt A: Bögen segmentieren, OCR laufen lassen, Review-Artefakte schreiben
# (--scans-dir hat Default C:\Repos\Sourcen_Scans\mereel)
python extract.py --pack hood

# → erzeugt output/review/hood/<bogen>/<row>_<col>/{cropped.png, regions/, parsed.json}

# Schritt B: Review der parsed.json-Dateien (manuell, in einem Editor)
#   - cropped.png neben parsed.json öffnen, vergleichen, korrigieren
#   - Symbole, b/i-Tags und Anführungszeichen prüfen

# Schritt C: parsed.json-Dateien zur finalen <pack>_encounter.json zusammenführen
python extract.py --pack hood --consolidate

# Schritt D: Datei in den Bot kopieren
cp output/hood_encounter.json ../../translations_local/hood_encounter.json

# Schritt E: Lokal testen
cd ../..
python test_local.py
```

## Layout-Datei pflegen

`layouts/<pack>.yaml` beschreibt pro Bogen, wie die einzelnen Karten daraus geschnitten werden. Zwei Modi werden unterstützt:

**Auto-Detect** (empfohlen, sofern weiße Bereiche zwischen den Karten sauber sichtbar sind):

```yaml
"HoodSetGER_1.jpg":
  auto_detect: true
  cols: 3                          # nur Hinweis für Review-Ordner-Struktur
  set_indicator_hint: the_hood     # Fallback, falls OCR den Indikator nicht liest
```

`extract.py` findet die Karten via Konturerkennung — keine Pixelgrids zu pflegen. Klappt zuverlässig, wenn der Hintergrund hell und gleichmäßig weiß ist.

**Festes Grid** (Fallback, wenn Auto-Detect scheitert oder Karten aneinanderkleben):

```yaml
"Old_Sheet.JPG":
  rows: 3
  cols: 3
  origin_x: 120     # Pixel-Offset zur ersten Karte (links oben)
  origin_y: 80
  card_w: 1500      # Kartenbreite in Pixeln
  card_h: 2100
  gap_x: 50         # horizontaler Abstand zwischen Karten
  gap_y: 50
  cards:
    - { row: 0, col: 0 }
    - { row: 0, col: 1 }
    # unbenutzte Slots einfach weglassen
```

## Wie das Tool den Kartentyp findet (v2-Pipeline)

Pro Karten-Crop:

1. **Orientierungs-Detektion** (`orient.detect`): Der Crop wird in vier 90°-Schritten rotiert. Pro Rotation wird der untere Streifen (y=0.91–0.99) per Tesseract gelesen und nach dem Set-Indikator-Pattern `XXX (n/m)` durchsucht. Die Rotation, in der ein parseable Indikator mit auflösbarem `code` herauskommt, gewinnt.

2. **Type-Lookup**: Aus dem `code` zieht der `PackMapper` den `type_code` der englischen Karte (`villain`/`minion`/`treachery`/`environment`/`attachment`/`main_scheme`/`side_scheme`).

3. **Type-Layout**: `extract.py:TYPE_LAYOUTS` definiert pro Type zwei relative Bereiche: `title` (für `name`) und `body` (für die Content-Splittung). Bei Anhängen wird der Title-Crop zusätzlich um 90° vorrotiert, weil der Titel im Druck auf der linken Kante steht.

4. **Content-Splitting** (`sections.split_sections`): Statt rigid Traits/Text/Flavor jeweils aus festen y-Streifen zu cropen, OCR-en wir die ganze Body-Region zeilenweise (`pytesseract.image_to_data`) und sortieren die Zeilen heuristisch in:
   - **traits** — kurze, zentrierte, punkt-getrennte Großbuchstaben-Zeile am Anfang
   - **flavor** — zusammenhängender Block am Ende, eingerahmt von `„…"`
   - **text** — alles dazwischen

   Felder dürfen leer bleiben — nicht jede Karte hat Traits oder Flavor.

## Hinweis zu Karten-Orientierung

Wenn `orient.detect` keine Rotation auflösen kann (kein Indikator lesbar), bleibt der Crop bei 0° und die Pipeline fällt auf das Hochformat-Template zurück. Im Review erkennt man das am `rotation: 0` und leerem `code` in der `parsed.json`; die Felder dort dann direkt anhand des `cropped.png` korrigieren.

## Hinweise

- **Schritt A ist nicht idempotent in einer Hinsicht**: Manuelle Edits an `parsed.json`-Dateien werden beim erneuten Lauf überschrieben. Wenn du editiert hast, geh direkt zu Schritt C (`--consolidate`).
- **Symbole** ([energy], [mental], [physical]) erkennt OCR nicht zuverlässig. `postprocess.py` hat eine wachsende Lookup-Tabelle für typische Müll-Token; manuelles Nachbessern beim Review bleibt nötig.
- Der Bot lädt `translations_local/<pack>_encounter.json` automatisch, wenn die Datei existiert (Patch in `bot.py:_load_encounter_pack`). Lokale Übersetzungen haben Vorrang vor GitHub-Übersetzungen.
