"""PDF text extraction (text layer only; scanned PDFs yield no text)."""

import logging

from pdfminer.high_level import extract_text as extract_pdf_text

from odf.extract.clean import clean_text

# Suppress annoying PDFMiner warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def extract(file_path):
    try:
        return clean_text(extract_pdf_text(file_path))
    except Exception:
        return ""
