"""Plain-text extraction, trying common encodings in order."""

import logging

from odf.extract.clean import clean_text

log = logging.getLogger(__name__)

ENCODINGS = ["utf-8", "utf-16", "latin-1", "cp1252"]


def extract(file_path):
    for encoding in ENCODINGS:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return clean_text(file.read())
        except Exception:
            continue
    log.warning("Could not read text file %s with any of %s", file_path, ENCODINGS)
    return ""
