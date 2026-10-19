"""Split document text into overlapping chunks for embedding."""

# Preferred break points, best first
SEPARATORS = ["\n\n", "\n", ". ", " "]


def split_text(text, chunk_size=1000, chunk_overlap=100):
    """
    Split text into chunks recursively (similar to LangChain).
    Simple implementation: split by paragraphs, then sentences, then chars.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break

        # Try to find a good breaking point (newline, period, space)
        # Look back from 'end' to find a separator
        break_point = -1
        for sep in SEPARATORS:
            idx = text.rfind(sep, start, end)
            if idx != -1 and idx > start + (chunk_size // 2):  # Ensure we don't split too early
                break_point = idx + len(sep)
                break

        if break_point != -1:
            chunks.append(text[start:break_point])
            start = break_point - chunk_overlap  # Overlap
        else:
            # Force split
            chunks.append(text[start:end])
            start = end - chunk_overlap

    return chunks
