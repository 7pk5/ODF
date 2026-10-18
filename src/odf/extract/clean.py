"""Normalise extracted text before chunking."""

import re

# Cap text size per file to avoid huge token counts (~50-70 pages)
MAX_CHARS = 100_000


def clean_text(text):
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove null bytes etc
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip()[:MAX_CHARS]
