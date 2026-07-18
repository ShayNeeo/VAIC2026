"""OCR fallback for scanned/image PDFs where app/knowledge/parsers.py's
pypdf-based text-layer extraction yields no usable text (see
extraction_quality()'s "publishable" check). Local Tesseract only -- this
repo processes synthetic/demo business documents; document bytes never
leave the machine for OCR, unlike a cloud OCR API.

Caller contract (app/intake/service.py): this module never fabricates
text. If Tesseract or PyMuPDF is unavailable, or the OCR result itself is
low-confidence/empty, it raises OcrUnavailableError or returns pages with
empty text -- the caller's own extraction_quality()/confidence gate is
what decides whether the result is usable, exactly the same fail-closed
shape the pre-OCR NEEDS_OCR path already had.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TESSDATA_DIR = ROOT / "data" / "ocr_tessdata"


class OcrUnavailableError(RuntimeError):
    """Tesseract/PyMuPDF/Pillow are not importable or runnable in this
    environment. Distinct from "OCR ran but text quality was poor" --
    that case returns a normal (low-confidence) result instead of
    raising, so the caller can log which happened rather than treating
    both as the same failure."""


def _tessdata_dir() -> str:
    configured = Path(settings.TESSDATA_DIR)
    return str(configured if configured.exists() else DEFAULT_TESSDATA_DIR)


def _configure_pytesseract():
    try:
        import pytesseract
    except ImportError as exc:
        raise OcrUnavailableError("pytesseract is not installed") from exc
    cmd = settings.TESSERACT_CMD
    if cmd and Path(cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


def ocr_pdf_bytes(data: bytes, *, lang: Optional[str] = None, dpi: Optional[int] = None) -> List[Dict[str, Any]]:
    """Rasterize each page of a PDF at `dpi` and OCR it with Tesseract.

    Returns one dict per page: {"page": int, "text": str,
    "mean_confidence": float in [0,1]}. Raises OcrUnavailableError if the
    OCR toolchain itself cannot run (missing library, missing Tesseract
    binary, missing language data) -- callers must treat that as "OCR not
    available in this environment", never silently substitute empty text
    for it.
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise OcrUnavailableError("pymupdf is not installed") from exc

    pytesseract = _configure_pytesseract()
    try:
        from PIL import Image
    except ImportError as exc:
        raise OcrUnavailableError("Pillow is not installed") from exc

    effective_lang = lang or settings.OCR_LANG
    effective_dpi = dpi or settings.OCR_DPI
    # pytesseract passes `config` straight through to the tesseract CLI
    # without shell quoting -- a manually quoted path (`--tessdata-dir
    # "X"`) ends up with the literal quote characters baked into the path
    # tesseract tries to open. Use an absolute, unquoted path instead.
    tessdata_dir = str(Path(_tessdata_dir()).resolve())
    config = f"--tessdata-dir {tessdata_dir}"

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # pymupdf raises its own RuntimeError/ValueError variants
        raise OcrUnavailableError(f"could not open PDF for OCR rasterization: {exc}") from exc

    results: List[Dict[str, Any]] = []
    try:
        zoom = effective_dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            try:
                ocr_data = pytesseract.image_to_data(
                    image, lang=effective_lang, config=config, output_type=pytesseract.Output.DICT,
                )
            except pytesseract.TesseractNotFoundError as exc:
                raise OcrUnavailableError("tesseract binary not found") from exc
            except pytesseract.TesseractError as exc:
                raise OcrUnavailableError(f"tesseract failed: {exc}") from exc

            words = [w for w in ocr_data.get("text", []) if w.strip()]
            confidences = [
                float(conf) for conf, word in zip(ocr_data.get("conf", []), ocr_data.get("text", []))
                if word.strip() and float(conf) >= 0
            ]
            mean_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            results.append({"page": index, "text": " ".join(words), "mean_confidence": round(mean_confidence, 4)})
    finally:
        doc.close()
    return results


def is_ocr_available() -> bool:
    """Cheap capability probe (no PDF rasterization) for a health-check or
    a UI badge -- true only if the whole toolchain (PyMuPDF, pytesseract,
    Pillow, the Tesseract binary, and the language data directory) is
    actually usable, not just importable."""
    try:
        import fitz  # noqa: F401
        from PIL import Image  # noqa: F401

        pytesseract = _configure_pytesseract()
        pytesseract.get_tesseract_version()
    except Exception:
        return False
    return Path(_tessdata_dir()).exists()
