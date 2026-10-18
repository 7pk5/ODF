"""
Vector Store
ChromaDB-backed storage of document chunks and their embeddings.
"""

import chromadb
from chromadb.config import Settings
import os
from odf import paths
from odf.index.chunking import split_text

COLLECTION_NAME = "documents"


class VectorStore:
    def __init__(self, embedder):
        """Open (or create) the persistent ChromaDB index; `embedder` embeds chunks on add."""
        self.embedder = embedder

        # Initialize ChromaDB persistent client in the OS user-data dir (EXE)
        # or project root (script), so it always has write permission
        self.db_path = paths.chroma_db_dir()

        # Telemetry off explicitly: ODF promises no network calls after the
        # one-time model download, whatever a chromadb upgrade defaults to
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

        print(f"VectorStore initialized with ChromaDB at {self.db_path}")

    def add_documents(self, documents_generator, batch_size=100, progress_callback=None):
        """
        Add documents to the ChromaDB collection in batches.
        
        Args:
            documents_generator: Generator yielding dictionaries with 'content', 'metadata', 'id'
            batch_size (int): Number of documents to add at once
            progress_callback (func): Optional callback(count, current_doc_name)
        """
        batch_ids = []
        batch_documents = []
        batch_metadatas = []
        
        count = 0
        
        for doc in documents_generator:
            content = doc['content']
            base_id = doc['id']
            metadata = doc['metadata']

            # A modified file gets new chunk IDs (path+mtime), so drop the
            # previous version's chunks first or search returns stale text
            self.delete_by_source(metadata['source'])

            # Split content into chunks
            chunks = split_text(content)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{base_id}_chunk_{i}"
                batch_ids.append(chunk_id)
                batch_documents.append(chunk)
                # Helper: Add chunk index to metadata for debugging/ordering
                chunk_meta = metadata.copy()
                chunk_meta['chunk_index'] = i
                batch_metadatas.append(chunk_meta)
            
            # Check batch size based on *chunks*, not files
            if len(batch_ids) >= batch_size:
                self._process_batch(batch_ids, batch_documents, batch_metadatas)
                batch_ids, batch_documents, batch_metadatas = [], [], []
            
            count += 1
            if progress_callback:
                progress_callback(count, doc.get('metadata', {}).get('filename', ''))
            elif count % 100 == 0:
                print(f"Processed {count} documents...")

        # Process remaining
        if batch_ids:
            self._process_batch(batch_ids, batch_documents, batch_metadatas)
            
        print(f"Finished adding {count} documents to index.")

    def _process_batch(self, ids, documents, metadatas):
        """Helper to embedding and upsert a batch."""
        try:
            # Check which documents already exist to avoid re-work (Naïve check, Chroma handles upsert but we can save embedding time)
            # For now, we trust upsert. To optimize, we could check existence first.
            
            # Generate embeddings using FastEmbed
            embeddings = self.embedder.embed_texts(documents)
            
            # Upsert to Chroma
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings.tolist()
            )
        except Exception as e:
            print(f"Error processing batch: {e}")

    def count(self):
        """Number of chunks in the index."""
        return self.collection.count()

    def query(self, query_embedding, n_results, where=None):
        """
        Nearest chunks to `query_embedding`, closest first, as dicts with
        id, distance (cosine, 0-2), document (chunk text) and metadata.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )
        if not results['ids']:
            return []
        return [
            {
                'id': chunk_id,
                'distance': distance,
                'document': document or "",
                'metadata': metadata or {},
            }
            for chunk_id, distance, document, metadata in zip(
                results['ids'][0], results['distances'][0],
                results['documents'][0], results['metadatas'][0],
            )
        ]

    def get_stats(self):
        """Get database statistics."""
        return {
            "count": self.count(),
            "path": self.db_path
        }
    
    def get_all_ids(self):
        """Get set of all document IDs currently in the index."""
        try:
            if self.collection.count() == 0:
                return set()
            
            # ChromaDB get() without args returns all info. We just need IDs.
            # Depending on DB size, this might be heavy, but IDs are small (MD5).
            result = self.collection.get(include=[]) # Don't fetch embeddings or documents
            all_server_ids = result['ids']
            
            # Convert server IDs (file_hash_chunk_X) back to file IDs (file_hash)
            # We just split by '_chunk_' and take the first part
            file_ids = set()
            for sid in all_server_ids:
                if '_chunk_' in sid:
                    file_ids.add(sid.split('_chunk_')[0])
                else:
                    file_ids.add(sid) # Backwards compatibility
            
            return file_ids
        except Exception as e:
            print(f"Error getting IDs: {e}")
            return set()

    def get_all_source_paths(self):
        """Return set of all unique file paths currently stored in the index."""
        try:
            if self.collection.count() == 0:
                return set()
            result = self.collection.get(include=["metadatas"])
            return {m["source"] for m in result["metadatas"] if m and "source" in m}
        except Exception as e:
            print(f"Error getting source paths: {e}")
            return set()

    def delete_by_source(self, file_path):
        """Delete all chunks belonging to a specific file path."""
        try:
            result = self.collection.get(where={"source": {"$eq": file_path}}, include=[])
            if result["ids"]:
                self.collection.delete(ids=result["ids"])
                return len(result["ids"])
            return 0
        except Exception as e:
            print(f"Error deleting chunks for {file_path}: {e}")
            return 0

    def cleanup_deleted_files(self):
        """Remove index entries for files that no longer exist on disk. Returns count of removed files."""
        try:
            sources = self.get_all_source_paths()
            missing = [p for p in sources if not os.path.exists(p)]
            for path in missing:
                self.delete_by_source(path)
            if missing:
                print(f"Cleaned up {len(missing)} deleted file(s) from index.")
            return len(missing)
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 0

    def remove_stale_versions(self):
        """
        Delete chunks from superseded versions of a file, keeping only the newest
        (by stored mtime). Repairs indexes built before re-indexing replaced old
        chunks. Returns count of files cleaned.
        """
        try:
            if self.collection.count() == 0:
                return 0
            result = self.collection.get(include=["metadatas"])

            # source -> {modified -> [chunk ids]}
            versions = {}
            for chunk_id, m in zip(result["ids"], result["metadatas"]):
                if m and "source" in m:
                    versions.setdefault(m["source"], {}).setdefault(m.get("modified", 0), []).append(chunk_id)

            stale_ids = []
            cleaned = 0
            for by_mtime in versions.values():
                if len(by_mtime) > 1:
                    newest = max(by_mtime)
                    stale_ids += [cid for mtime, ids in by_mtime.items() if mtime != newest for cid in ids]
                    cleaned += 1

            if stale_ids:
                step = self.client.get_max_batch_size()
                for i in range(0, len(stale_ids), step):
                    self.collection.delete(ids=stale_ids[i:i + step])
                print(f"Removed stale versions of {cleaned} file(s) from index.")
            return cleaned
        except Exception as e:
            print(f"Error removing stale versions: {e}")
            return 0

    def clear(self):
        """Delete all documents in collection."""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
            print("Index cleared.")
        except Exception as e:
            print(f"Error clearing index: {e}")
