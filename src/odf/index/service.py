"""
Index Service
The "index a folder" workflow: tidy the index, scan, extract and store.
UI-free, so it can be tested and reused (e.g. by a CLI or folder watcher).
"""

from dataclasses import dataclass

from odf.index import file_indexer, scanner


@dataclass
class IndexResult:
    files_found: int       # supported files in the folder, including unchanged ones
    removed_deleted: int   # files dropped from the index because they no longer exist
    repaired_stale: int    # files whose superseded versions were removed


class IndexService:
    def __init__(self, store):
        self.store = store

    def chunk_count(self):
        """Number of chunks in the index."""
        return self.store.count()

    def index_folder(self, folder, on_progress=None, on_cleanup=None):
        """
        Index every supported file under `folder`, skipping unchanged ones.

        on_cleanup(removed): called once deleted files are dropped, before the
            (possibly slow) folder scan.
        on_progress(done, total, filename): called after each new/modified file
            is stored. `total` is every file found, including unchanged ones.

        Raises ValueError if `folder` doesn't exist.
        """
        removed = self.store.cleanup_deleted_files()
        if on_cleanup:
            on_cleanup(removed)
        repaired = self.store.remove_stale_versions()

        files = scanner.scan_directory(folder)
        total = len(files)
        if total:
            progress = (lambda done, filename: on_progress(done, total, filename)) if on_progress else None
            documents = file_indexer.process_files(files, existing_ids=self.store.get_all_ids())
            self.store.add_documents(documents, progress_callback=progress)

        return IndexResult(files_found=total, removed_deleted=removed, repaired_stale=repaired)
