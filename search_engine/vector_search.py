"""
Vector Search Engine
Handles FAISS-based similarity search for document retrieval.
"""

import faiss
import numpy as np
import pickle
import os
from search_engine.embedder import Embedder

class VectorSearch:
    def __init__(self, use_accurate_model=False, use_fast_model=True):
        """Initialize the vector search engine with speed/accuracy options."""
        self.embedder = Embedder()
        if use_accurate_model:
            # Switch to the most accurate model available
            self.embedder.switch_to_most_accurate_model()
        elif use_fast_model:
            # Switch the embedder to a fast model for high speed
            self.embedder.switch_to_fast_model()
        
        self.index = None
        self.documents = []  # Store document metadata
        self.embeddings = None
        self.chunk_embeddings = []  # Store chunk-level embeddings
        self.chunks = []  # Store document chunks for better retrieval
        
        # Use more sophisticated FAISS index
        self.use_hnsw = True  # Use HNSW for better accuracy
        self.nprobe = 50  # Number of clusters to search (for IVF)
        
        self.index_file = os.path.join(os.path.dirname(__file__), '..', 'models', 'embeddings.index')
        self.metadata_file = os.path.join(os.path.dirname(__file__), '..', 'models', 'metadata.pkl')
        
        print(f"VectorSearch initialized with model: {self.embedder.get_model_info()['model_name']}")
    
    def build_index(self, files_data, use_chunking=True, batch_size=32):
        """
        Build sophisticated FAISS index from document embeddings with enhanced accuracy.
        
        Args:
            files_data (list): List of tuples (file_path, content)
            use_chunking (bool): Whether to use intelligent chunking for better accuracy
            batch_size (int): Batch size for embedding (speed/accuracy tradeoff)
        """
        if not files_data:
            print("No files to index")
            return
        
        print(f"Building enhanced index for {len(files_data)} documents...")
        
        # Reset storage
        self.documents = []
        self.chunks = []
        all_texts = []
        
        for file_path, content in files_data:
            filename = os.path.basename(file_path)
            filename_no_ext = os.path.splitext(filename)[0]
            
            # Store document metadata
            doc_metadata = {
                'file_path': file_path,
                'filename': filename,
                'content': content[:1000],  # Store more content for preview
                'full_content': content,
                'word_count': len(content.split())
            }
            
            if use_chunking and len(content.split()) > 100:
                # Use intelligent chunking for long documents
                chunks = self._chunk_text_intelligently(content)
                
                for i, chunk in enumerate(chunks):
                    # Enhanced searchable text with context
                    searchable_text = f"File: {filename_no_ext}. Content: {chunk}"
                    processed_text = self.embedder.preprocess_text(searchable_text, enhance_accuracy=True)
                    all_texts.append(processed_text)
                    
                    # Store chunk metadata with reference to parent document
                    chunk_metadata = doc_metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': i,
                        'chunk_content': chunk,
                        'is_chunk': True,
                        'parent_doc_index': len(self.documents)
                    })
                    self.chunks.append(chunk_metadata)
            else:
                # For short documents, use the whole content
                searchable_text = f"File: {filename_no_ext}. {content}"
                processed_text = self.embedder.preprocess_text(searchable_text, enhance_accuracy=True)
                all_texts.append(processed_text)
                
                # Store as a single chunk
                doc_metadata.update({
                    'chunk_id': 0,
                    'chunk_content': content,
                    'is_chunk': False,
                    'parent_doc_index': len(self.documents)
                })
                self.chunks.append(doc_metadata)
            
            self.documents.append(doc_metadata)
        
        print(f"Created {len(all_texts)} searchable segments from {len(files_data)} documents")
        
        # Generate embeddings with enhanced preprocessing
        print("Generating high-quality embeddings...")
        self.embeddings = self.embedder.embed_texts(all_texts, preprocess=True, batch_size=batch_size)
        
        if len(self.embeddings) == 0:
            print("No embeddings generated")
            return
        
        # Create sophisticated FAISS index
        print("Creating sophisticated search index...")
        self.index = self._create_sophisticated_index(self.embeddings)
        
        # Add embeddings to index 
        embeddings_float32 = self.embeddings.astype(np.float32)
        
        print("Adding embeddings to index...")
        # Note: Suppressing type checker warnings for FAISS API
        self.index.add(embeddings_float32)  # type: ignore
        
        # Set search parameters for better accuracy (only for IVF indices)
        try:
            if hasattr(self.index, 'nprobe'):
                self.index.nprobe = min(self.nprobe, getattr(self.index, 'nlist', 50))  # type: ignore
        except:
            pass  # Some index types don't support nprobe
        
        print(f"Enhanced index built successfully with {self.index.ntotal} segments")
        print(f"Index type: {type(self.index).__name__}")
        
        # Save index and metadata
        self._save_index()
    
    def search(self, query, top_k=10, rerank_results=True, diversity_threshold=0.85):
        """
        Enhanced search with re-ranking and diversity for better accuracy.
        
        Args:
            query (str): Search query
            top_k (int): Number of top results to return
            rerank_results (bool): Apply semantic re-ranking
            diversity_threshold (float): Threshold for result diversity (0.0-1.0)
            
        Returns:
            list: List of tuples (file_path, similarity_score, content_preview, match_type)
        """
        if not self.index or not self.chunks:
            raise RuntimeError("Index not built. Please index documents first.")
        
        # Enhanced query preprocessing
        processed_query = self.embedder.preprocess_text(query, enhance_accuracy=True)
        
        # Generate multiple query variations for better recall
        query_variations = [
            processed_query,
            f"Find: {processed_query}",
            f"Search for: {processed_query}",
            f"Document about: {processed_query}"
        ]
        
        all_results = []
        
        # Search with multiple query variations
        for i, query_var in enumerate(query_variations):
            query_embedding = self.embedder.embed_text(query_var, preprocess=False)
            
            # Convert to numpy and reshape properly
            query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            
            # Perform search with FAISS
            search_k = min(top_k * 3, len(self.chunks))  # Get more candidates
            
            # Use the standard FAISS search API
            distances, indices = self.index.search(query_embedding, search_k)  # type: ignore
            similarities = distances  # For inner product, higher is better
            
            # Process results
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx >= 0 and idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    
                    # Calculate additional relevance signals
                    query_words = set(query.lower().split())
                    content_words = set(chunk['chunk_content'].lower().split())
                    filename_words = set(chunk['filename'].lower().split())
                    
                    # Word overlap scores
                    content_overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
                    filename_overlap = len(query_words.intersection(filename_words)) / max(len(query_words), 1)
                    
                    # Combined relevance score
                    relevance_score = (
                        float(similarity) * 0.7 +  # Semantic similarity
                        content_overlap * 0.2 +    # Content word overlap
                        filename_overlap * 0.1     # Filename relevance
                    )
                    
                    # Determine match type
                    match_type = "semantic"
                    if filename_overlap > 0.3:
                        match_type = "filename"
                    elif content_overlap > 0.3:
                        match_type = "content"
                    
                    all_results.append({
                        'file_path': chunk['file_path'],
                        'similarity': relevance_score,
                        'original_similarity': float(similarity),
                        'content_preview': chunk['chunk_content'][:300],
                        'filename': chunk['filename'],
                        'match_type': match_type,
                        'query_variation': i,
                        'chunk_id': chunk.get('chunk_id', 0),
                        'word_count': chunk.get('word_count', 0)
                    })
        
        # Remove duplicates and apply diversity filtering
        unique_results = self._deduplicate_and_diversify(all_results, diversity_threshold)
        
        # Sort by combined relevance score
        unique_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Take top results
        final_results = unique_results[:top_k]
        
        # Apply semantic re-ranking if requested
        if rerank_results and len(final_results) > 1:
            final_results = self._semantic_rerank(query, final_results)
        
        # Format results
        formatted_results = []
        for result in final_results:
            formatted_results.append((
                result['file_path'],
                result['similarity'],
                result['content_preview'],
                result['match_type']
            ))
        
        return formatted_results
    
    def _deduplicate_and_diversify(self, results, threshold=0.85):
        """Remove duplicate and overly similar results."""
        if not results:
            return []
        
        unique_results = []
        seen_files = {}
        
        # Sort by similarity first
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        for result in results:
            file_path = result['file_path']
            
            # If we haven't seen this file, add it
            if file_path not in seen_files:
                seen_files[file_path] = result
                unique_results.append(result)
            else:
                # If we've seen this file, only add if significantly different chunk
                existing = seen_files[file_path]
                if (result['similarity'] > existing['similarity'] * 1.1 or 
                    result['chunk_id'] != existing['chunk_id']):
                    # Replace with better result
                    for i, ur in enumerate(unique_results):
                        if ur['file_path'] == file_path:
                            unique_results[i] = result
                            seen_files[file_path] = result
                            break
        
        return unique_results
    
    def _semantic_rerank(self, query, results):
        """Apply semantic re-ranking for better result ordering."""
        if len(results) <= 1:
            return results
        
        # Create embeddings for result contents
        result_texts = [f"{r['filename']} {r['content_preview']}" for r in results]
        result_embeddings = self.embedder.embed_texts(result_texts, preprocess=True)
        query_embedding = self.embedder.embed_text(query, preprocess=True)
        
        # Calculate more sophisticated similarity scores
        for i, result in enumerate(results):
            if i < len(result_embeddings):
                # Cross-attention style scoring
                semantic_sim = np.dot(query_embedding, result_embeddings[i])
                
                # Combine with original score
                result['similarity'] = (
                    result['similarity'] * 0.6 +  # Original score
                    semantic_sim * 0.4             # Re-ranking score
                )
        
        # Re-sort by updated scores
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def _save_index(self):
        """Save the enhanced FAISS index and metadata to disk."""
        try:
            # Create models directory if it doesn't exist
            models_dir = os.path.dirname(self.index_file)
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            # Save FAISS index
            if self.index:
                faiss.write_index(self.index, self.index_file)
            
            # Save enhanced metadata
            metadata = {
                'documents': self.documents,
                'chunks': self.chunks,
                'embeddings': self.embeddings,
                'model_info': self.embedder.get_model_info(),
                'index_type': type(self.index).__name__ if self.index else None,
                'version': '2.0'  # Version for compatibility
            }
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            print(f"Enhanced index saved to {self.index_file}")
            print(f"Saved {len(self.chunks)} chunks from {len(self.documents)} documents")
            
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def load_index(self):
        """Load the enhanced FAISS index and metadata from disk."""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                # Load FAISS index
                self.index = faiss.read_index(self.index_file)
                
                # Load metadata
                with open(self.metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                
                self.documents = metadata.get('documents', [])
                self.chunks = metadata.get('chunks', metadata.get('documents', []))  # Backward compatibility
                self.embeddings = metadata.get('embeddings')
                
                # Set search parameters for loaded index
                try:
                    if hasattr(self.index, 'nprobe'):
                        self.index.nprobe = min(self.nprobe, getattr(self.index, 'nlist', 50))  # type: ignore
                except:
                    pass
                
                version = metadata.get('version', '1.0')
                model_info = metadata.get('model_info', {})
                
                print(f"Enhanced index loaded successfully (v{version})")
                print(f"Loaded {len(self.chunks)} chunks from {len(self.documents)} documents")
                print(f"Index type: {type(self.index).__name__}")
                if model_info:
                    print(f"Original model: {model_info.get('model_name', 'Unknown')}")
                
                return True
            else:
                print("No saved index found")
                return False
                
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def get_index_stats(self):
        """Get comprehensive statistics about the current index."""
        if not self.index:
            return {
                "total_documents": len(self.documents) if hasattr(self, 'documents') else 0,
                "total_chunks": len(self.chunks) if hasattr(self, 'chunks') else 0,
                "index_size": 0,
                "embedding_dimension": 0,
                "index_type": None,
                "model_info": self.embedder.get_model_info() if hasattr(self, 'embedder') else {},
            }
        
        stats = {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal,
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "index_type": type(self.index).__name__,
            "model_info": self.embedder.get_model_info()
        }
        
        # Add index-specific stats safely
        try:
            if hasattr(self.index, 'nlist'):
                stats["index_clusters"] = getattr(self.index, 'nlist', None)
        except:
            pass
        
        try:
            if hasattr(self.index, 'nprobe'):
                stats["search_clusters"] = getattr(self.index, 'nprobe', None)
        except:
            pass
        
        return stats
    
    def get_document_preview(self, file_path, max_length=200):
        """Get a preview of a specific document."""
        for doc in self.documents:
            if doc['file_path'] == file_path:
                content = doc.get('full_content', doc.get('content', ''))
                if len(content) > max_length:
                    return content[:max_length] + "..."
                return content
        return "Document not found"
    
    def search_with_explanation(self, query, top_k=5):
        """
        Search with detailed explanation of why results were returned.
        
        Args:
            query (str): Search query
            top_k (int): Number of results
            
        Returns:
            dict: Results with explanations
        """
        results = self.search(query, top_k, rerank_results=True)
        
        explanation = {
            "query": query,
            "model_used": self.embedder.get_model_info()["model_name"],
            "search_strategy": "Enhanced semantic search with re-ranking",
            "total_searchable_chunks": len(self.chunks),
            "results": []
        }
        
        for i, (file_path, similarity, content, match_type) in enumerate(results):
            result_info = {
                "rank": i + 1,
                "file_path": file_path,
                "similarity_score": round(similarity, 4),
                "match_type": match_type,
                "content_preview": content,
                "explanation": self._get_match_explanation(query, content, match_type, similarity)
            }
            explanation["results"].append(result_info)
        
        return explanation
    
    def _get_match_explanation(self, query, content, match_type, similarity):
        """Generate explanation for why a result was matched."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        overlap = query_words.intersection(content_words)
        
        if match_type == "filename":
            return f"Strong filename relevance (similarity: {similarity:.3f})"
        elif match_type == "content" and overlap:
            return f"Content contains matching words: {', '.join(list(overlap)[:3])} (similarity: {similarity:.3f})"
        else:
            return f"Semantic similarity based on meaning and context (similarity: {similarity:.3f})"
    
    def _chunk_text_intelligently(self, text, max_chunk_size=300, overlap=50):
        """
        Intelligently chunk text for better semantic representation.
        
        Args:
            text (str): Text to chunk
            max_chunk_size (int): Maximum chunk size in words
            overlap (int): Overlap between chunks in words
            
        Returns:
            list: List of text chunks
        """
        if not text or len(text.split()) <= max_chunk_size:
            return [text]
        
        # Split by sentences first
        sentences = []
        current_sentence = ""
        
        # Simple sentence splitting (can be enhanced with spaCy/NLTK)
        for char in text:
            current_sentence += char
            if char in '.!?' and len(current_sentence.strip()) > 10:
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_word_count + sentence_words <= max_chunk_size:
                current_chunk.append(sentence)
                current_word_count += sentence_words
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap from previous chunk
                if len(current_chunk) > 1 and overlap > 0:
                    overlap_words = ' '.join(current_chunk[-1:]).split()[-overlap:]
                    current_chunk = [' '.join(overlap_words), sentence]
                    current_word_count = len(overlap_words) + sentence_words
                else:
                    current_chunk = [sentence]
                    current_word_count = sentence_words
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _create_sophisticated_index(self, embeddings):
        """
        Create a sophisticated FAISS index for better accuracy.
        
        Args:
            embeddings (np.ndarray): Embedding vectors
            
        Returns:
            faiss.Index: Optimized FAISS index
        """
        dimension = embeddings.shape[1]
        n_embeddings = embeddings.shape[0]
        
        print(f"Creating sophisticated index for {n_embeddings} embeddings with dimension {dimension}")
        
        if n_embeddings < 1000:
            # For small datasets, use exact search with inner product
            index = faiss.IndexFlatIP(dimension)
            print("Using exact search (IndexFlatIP) for small dataset")
        elif n_embeddings < 10000:
            # For medium datasets, use HNSW for better accuracy
            index = faiss.IndexHNSWFlat(dimension, 32)  # 32 connections per layer
            index.hnsw.efConstruction = 200  # Higher for better recall
            index.hnsw.efSearch = 100  # Higher for better search quality
            print("Using HNSW index for medium dataset")
        else:
            # For large datasets, use IVF with product quantization
            nlist = min(int(np.sqrt(n_embeddings)), 1000)  # Number of clusters
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            print(f"Using IVF index with {nlist} clusters for large dataset")
        
        return index
