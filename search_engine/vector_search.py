""" 
Vector Search Engine 
Handles ChromaDB-based similarity search for document retrieval. 
"""

import os
import sys
import shutil
import gc
import time
import chromadb
from chromadb.config import Settings  # <--- Essential for Reset Permission 
from search_engine.embedder import Embedder


class VectorSearch:
    def __init__(self):
        """Initialize the vector search engine with ChromaDB."""
        self.embedder = Embedder()

        # Determine database path 
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.join(os.path.dirname(__file__), '..')

        self.db_path = os.path.join(base_dir, 'data', 'chroma_db')

        # Initialize Database with RESET permissions  
        self._init_db()

    def _init_db(self):
        """Helper to initialize the DB with specific settings."""
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)

        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(allow_reset=True)  # <--- THIS FIXES THE LOCK 
        )

        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"VectorSearch initialized at {self.db_path}")

    def _recursive_text_split(self, text, chunk_size=1000, chunk_overlap=100):
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
            break_point = -1
            for sep in ['\n\n', '\n', '. ', ' ']:
                idx = text.rfind(sep, start, end)
                if idx != -1 and idx > start + (chunk_size // 2):
                    break_point = idx + len(sep)
                    break
            if break_point != -1:
                chunks.append(text[start:break_point])
                start = break_point - chunk_overlap
            else:
                chunks.append(text[start:end])
                start = end - chunk_overlap
        return chunks

    def add_documents(self, documents_generator, batch_size=100, progress_callback=None):
        batch_ids, batch_documents, batch_metadatas = [], [], []
        count = 0

        for item in documents_generator:
            if isinstance(item, tuple):
                base_id, content, file_path = item
                metadata = {"source": file_path, "filename": os.path.basename(file_path)}
            else:
                content = item['content']
                base_id = item['id']
                metadata = item['metadata']

            chunks = self._recursive_text_split(content)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{base_id}_chunk_{i}"
                batch_ids.append(chunk_id)
                batch_documents.append(chunk)
                chunk_meta = metadata.copy()
                chunk_meta['chunk_index'] = i
                batch_metadatas.append(chunk_meta)

            if len(batch_ids) >= batch_size:
                self._process_batch(batch_ids, batch_documents, batch_metadatas)
                batch_ids, batch_documents, batch_metadatas = [], [], []

            count += 1
            if progress_callback:
                progress_callback(count, metadata.get('filename', ''))
            elif count % 100 == 0:
                print(f"Processed {count} documents...")

        if batch_ids:
            self._process_batch(batch_ids, batch_documents, batch_metadatas)
        print(f"Finished adding {count} documents.")

    def _process_batch(self, ids, documents, metadatas):
        try:
            embeddings = self.embedder.embed_texts(documents)
            self.collection.upsert(
                ids=ids, 
                documents=documents, 
                metadatas=metadatas, 
                embeddings=embeddings.tolist()
            )
        except Exception as e:
            print(f"Error processing batch: {e}")

    def search(self, query, top_k=10, filter_metadata=None):
        try:
            if self.collection.count() == 0:
                return []
            query_embedding = self.embedder.embed_text(query)
            candidate_k = top_k * 3
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=candidate_k,
                where=filter_metadata
            )
            if not results['ids']:
                return []

            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            candidates = []
            query_lower = query.lower().strip()

            for i in range(len(ids)):
                base_score = 1 - (distances[i])
                final_score = base_score
                content_text = documents[i] or ""
                metadata = metadatas[i] or {}
                filename = metadata.get('filename', '').lower()

                if query_lower in filename:
                    final_score += 0.25
                if query_lower in content_text.lower():
                    final_score += 0.15
                final_score = min(1.0, final_score)

                candidates.append({
                    'id': ids[i],
                    'similarity': max(0.0, float(final_score)),
                    'content': content_text,
                    'metadata': metadata,
                    'file_path': metadata.get('source'),
                    'filename': metadata.get('filename', 'Unknown'),
                })
            candidates.sort(key=lambda x: x['similarity'], reverse=True)
            return candidates[:top_k]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_stats(self):
        return {"count": self.collection.count(), "path": self.db_path}

    def get_all_ids(self):
        try:
            if self.collection.count() == 0:
                return set()
            result = self.collection.get(include=[])
            all_server_ids = result['ids']
            file_ids = set()
            for sid in all_server_ids:
                if '_chunk_' in sid:
                    file_ids.add(sid.split('_chunk_')[0])
                else:
                    file_ids.add(sid)
            return file_ids
        except Exception as e:
            print(f"Error getting IDs: {e}")
            return set()

    # --- UPDATED CLEAN LOGIC --- 
    def clear_database(self):
        """ 
        Resets the database. Tries the official method first (Safe),  
        then falls back to 'Nuclear' folder deletion if needed. 
        """
        print("Resetting database...")

        # Method 1: The Official Way (Fast & Safe) 
        try:
            self.client.reset()
            print(" Database reset via client.reset()")
            # Re-initialize collection hooks after reset 
            self.collection = self.client.get_or_create_collection(
                name="documents", metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f" Standard reset failed: {e}")
            print(" Attempting nuclear folder deletion...")

        # Method 2: The Nuclear Way (If file locks persist) 
        try:
            # 1. Stop the internal system (Releases locks) 
            if hasattr(self.client, '_system'):
                self.client._system.stop()

            # 2. Kill references 
            self.client = None
            self.collection = None
            gc.collect()
            time.sleep(1.0)  # Wait for Windows to release handles 

            # 3. Delete folder 
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
                print(" Physical folder deleted.")

            # 4. Rebuild 
            self._init_db()
            return True

        except Exception as e:
            print(f" Critical Error during hard clean: {e}")
            # Last resort: Try to reconnect anyway so app doesn't crash 
            try:
                self._init_db()
            except:
                pass
            return False
