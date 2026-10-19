"""
Text extraction from supported document formats.

Each format has its own module exposing `extract(file_path) -> str` that
returns cleaned text, or "" if the file can't be read.
"""

import os

from odf.extract import pdf, text, word

EXTRACTORS = {
    ".pdf": pdf.extract,
    ".docx": word.extract,
    ".txt": text.extract,
}

# Extensions picked up when scanning folders. The .txt extractor exists but
# isn't enabled for indexing yet.
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extension_of(file_path):
    """Lower-cased extension including the dot, e.g. '.pdf'."""
    return os.path.splitext(file_path.lower())[1]


def extract_text(file_path, extension=None):
    """Extract cleaned text from a file, or "" if unsupported or unreadable."""
    extractor = EXTRACTORS.get(extension or extension_of(file_path))
    return extractor(file_path) if extractor else ""
