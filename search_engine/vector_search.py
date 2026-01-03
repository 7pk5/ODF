"""
Vector Search Engine
Handles ChromaDB-based similarity search for document retrieval.
"""

import chromadb
from chromadb.config import Settings
import os
import uuid
import time
from tqdm import tqdm
from search_engine.embedder import Embedder

class VectorSearch:
    def __init__(self):
        """Initialize the vector search engine with ChromaDB."""
        self.embedder = Embedder()
        
        # Initialize ChromaDB persistent client
        # Persistence Logic:
        # If frozen (exe), store data next to the executable file.
        # If script, store in project root.
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.join(os.path.dirname(__file__), '..')
            
        self.db_path = os.path.join(base_dir, 'data', 'chroma_db')
            
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        
        print(f"VectorSearch initialized with ChromaDB at {self.db_path}")

    def _recursive_text_split(self, text, chunk_size=1000, chunk_overlap=100):
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
            for sep in ['\n\n', '\n', '. ', ' ']:
                idx = text.rfind(sep, start, end)
                if idx != -1 and idx > start + (chunk_size // 2): # Ensure we don't split too early
                    break_point = idx + len(sep)
                    break
            
            if break_point != -1:
                chunks.append(text[start:break_point])
                start = break_point - chunk_overlap # Overlap
            else:
                # Force split
                chunks.append(text[start:end])
                start = end - chunk_overlap
                
        return chunks
    
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
        batch_embeddings = []
        
        count = 0
        
        for doc in documents_generator:
            content = doc['content']
            base_id = doc['id']
            metadata = doc['metadata']
            
            # Split content into chunks
            chunks = self._recursive_text_split(content)
            
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

    def search(self, query, top_k=10, filter_metadata=None):
        """
        Search for documents similar to the query.
        Implements Hybrid Search: Semantic Vector Search + Exact Keyword Boosting.
        """
        try:
            if self.collection.count() == 0:
                return []
                
            query_embedding = self.embedder.embed_text(query)
            
            # Hybrid Search Strategy:
            # 1. Fetch more candidates (3x) from vector search to cast a wider net
            # 2. Check for exact keyword matches in these candidates
            # 3. Apply boosting for exact matches
            # 4. Re-rank and return top_k
            
            candidate_k = top_k * 3
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=candidate_k,
                where=filter_metadata
            )
            
            if not results['ids']:
                return []
                
            # Unpack results
            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            
            candidates = []
            query_lower = query.lower().strip()
            
            for i in range(len(ids)):
                # Base Semantic Score
                # Cosine distance is 0 to 2. Similarity = 1 - (distance / 2) roughly
                base_score = 1 - (distances[i])
                final_score = base_score
                
                content_text = documents[i] or ""
                metadata = metadatas[i] or {}
                filename = metadata.get('filename', '').lower()
                
                # --- HYBRID BOOSTING LOGIC ---
                boost_applied = False
                
                # 1. Title Match Boost (Very High)
                if query_lower in filename:
                    final_score += 0.25
                    boost_applied = True
                    
                # 2. Exact Content Match Boost (Moderate)
                if query_lower in content_text.lower():
                    final_score += 0.15
                    boost_applied = True
                
                # Ensure we don't exceed 1.0 (optional, but good for consistent UI%)
                final_score = min(1.0, final_score)
                
                candidates.append({
                    'id': ids[i],
                    'similarity': max(0.0, float(final_score)),
                    'base_score': base_score, # Debugging
                    'boosted': boost_applied,
                    'content': content_text,
                    'metadata': metadata,
                    'file_path': metadata.get('source'),
                    'filename': metadata.get('filename', 'Unknown'),
                })
                
            # Re-rank based on final_score
            candidates.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top_k
            return candidates[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
            
    def get_stats(self):
        """Get database statistics."""
        return {
            "count": self.collection.count(),
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

    def clear(self):
        """Delete all documents in collection."""
        try:
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(name="documents")
            print("Index cleared.")
        except Exception as e:
            print(f"Error clearing index: {e}")
