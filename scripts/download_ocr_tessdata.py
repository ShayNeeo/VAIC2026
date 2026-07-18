"""One-time setup: download the Tesseract language data app/knowledge/ocr.py
needs into data/ocr_tessdata/ (gitignored -- not committed, same treatment
as data/vector_db/). Requires the Tesseract OCR binary to already be
installed separately (Windows: `winget install --id UB-Mannheim.TesseractOCR
-e`); this script only fetches the .traineddata language files, which the
UB-Mannheim installer only bundles for English.

Usage: python scripts/download_ocr_tessdata.py
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "data" / "ocr_tessdata"
BASE_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main"
LANGUAGES = ["eng", "vie", "osd"]


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for lang in LANGUAGES:
        target = TARGET_DIR / f"{lang}.traineddata"
        if target.exists():
            print(f"skip (already present): {target}")
            continue
        url = f"{BASE_URL}/{lang}.traineddata"
        print(f"downloading {url} -> {target}")
        urllib.request.urlretrieve(url, target)
    print("done.")


if __name__ == "__main__":
    main()
