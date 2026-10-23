"""Validate a text PDF and extract its pages locally with pypdf. No model call."""

import io

from pypdf import PdfReader

from relay.service import Problem

MAX_PDF_BYTES = 2 * 1024 * 1024


def extract_pdf(raw):
    """1. Extract selectable text locally. No model call and no PDF instructions executed."""
    if not raw.startswith(b"%PDF-") or not 1 <= len(raw) <= MAX_PDF_BYTES:
        raise Problem(422, "invalid_pdf", "Choose a PDF up to 2 MiB.")
    try:
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 10:
            raise ValueError
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if not text.strip():
                raise Problem(
                    422,
                    "pdf_needs_ocr",
                    "This PDF has an image-only page. Use a text PDF; OCR is not included.",
                )
            pages.append({"page": number, "text": text})
            if sum(len(p["text"]) for p in pages) > 50_000:
                raise ValueError
        text = "\n\n".join(p["text"] for p in pages)
        if len(text.strip()) < 50 or "\x00" in text:
            raise ValueError
        return text, pages
    except Problem:
        raise
    except Exception:
        raise Problem(
            422,
            "invalid_pdf",
            "Use an unencrypted text PDF with 1–10 pages, up to 50,000 extracted characters.",
        ) from None
