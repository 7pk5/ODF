"""
File Indexer
Turns document files into index-ready records (id, text, metadata),
extracting text in parallel.
"""

import hashlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from odf.extract import extension_of, extract_text

log = logging.getLogger(__name__)


def document_id(file_path, mtime):
    """Fingerprint of one version of a file: md5(path + mtime)."""
    return hashlib.md5(f"{file_path}_{mtime}".encode()).hexdigest()


def process_files(file_paths, existing_ids=None):
    """
    Process a list of files in parallel (threads) and yield documents,
    skipping files whose current version is already in `existing_ids`.
    """
    if existing_ids is None:
        existing_ids = set()

    log.info("Processing %d files with %d existing IDs", len(file_paths), len(existing_ids))

    # Computing the ID (md5 of path+mtime) is cheap; extracting text is
    # expensive, so check the ID before submitting work to the pool.
    files_to_process = []
    skipped_count = 0

    for f in file_paths:
        try:
            if document_id(f, os.stat(f).st_mtime) in existing_ids:
                skipped_count += 1
                continue
            files_to_process.append(f)
        except OSError:
            continue

    log.info("Skipping %d already indexed files. Processing %d new/modified files.",
             skipped_count, len(files_to_process))

    # Threads rather than processes for Windows stability (ProcessPool requires strict entry point guards)
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count())) as executor:
        future_to_file = {executor.submit(process_file, f): f for f in files_to_process}

        # Yield results as they complete
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                if result:
                    yield result
            except Exception:
                log.exception("Error processing %s", future_to_file[future])


def process_file(file_path):
    """Extract text and metadata from one file, or None if it has no text."""
    try:
        ext = extension_of(file_path)
        content = extract_text(file_path, ext)

        if not content or not content.strip():
            log.warning("No text content found in %s", file_path)
            return None

        file_stats = os.stat(file_path)
        return {
            "id": document_id(file_path, file_stats.st_mtime),
            "content": content,
            "metadata": {
                "source": file_path,
                "filename": os.path.basename(file_path),
                "modified": file_stats.st_mtime,
                "size": file_stats.st_size,
                "type": ext
            }
        }
    except Exception:
        log.exception("Error processing %s", file_path)
        return None
