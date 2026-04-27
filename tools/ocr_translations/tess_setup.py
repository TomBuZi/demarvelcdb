"""Zentrale Tesseract-Konfiguration. Wird von `extract.py` und `orient.py`
importiert, damit beide Pfade funktionieren — egal in welcher Reihenfolge
sie geladen werden.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytesseract

TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
if Path(TESSERACT_CMD).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

LOCAL_TESSDATA_DIR = Path(__file__).parent / "tessdata"
if LOCAL_TESSDATA_DIR.exists():
    os.environ["TESSDATA_PREFIX"] = str(LOCAL_TESSDATA_DIR)
