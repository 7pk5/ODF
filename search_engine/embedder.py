"""
Document and Query Embedder
Handles text embedding using FastEmbed for high-performance semantic search.
"""

from fastembed import TextEmbedding
import numpy as np
from typing import List, Union

class Embedder:
    def __init__(self, model_name='BAAI/bge-small-en-v1.5'):
        """
        Initialize the embedder with FastEmbed.
        
        Args:
            model_name (str): Name of the model to use. 
                            Default 'BAAI/bge-small-en-v1.5' is very fast and accurate.
        """
        self.model_name = model_name
        try:
            print(f"Loading embedding model: {model_name}")
            
            # Determine cache directory for models
            import sys
            import os
            
            if getattr(sys, 'frozen', False):
                # If running as .exe, look in the internal temp folder (_MEIPASS)
                # We will tell PyInstaller to put 'models' folder there.
                base_dir = sys._MEIPASS
            else:
                # If running as script, assume 'models' folder is in project root
                base_dir = os.path.join(os.path.dirname(__file__), '..')
            
            model_cache_dir = os.path.join(base_dir, 'models')
            
            # Create models dir if not exists (for script mode)
            if not os.path.exists(model_cache_dir) and not getattr(sys, 'frozen', False):
                os.makedirs(model_cache_dir)
            
            # Configure FastEmbed to use our custom cache dir
            # and local_files_only=True ensures it doesn't try to download if missing
            self.model = TextEmbedding(
                model_name=model_name, 
                threads=None,
                cache_dir=model_cache_dir,
                local_files_only=True 
            )
            print(f"Model '{model_name}' loaded successfully!")
        except Exception as e:
            print(f"Failed to load model '{model_name}': {e}")
            raise RuntimeError(f"Failed to initialize FastEmbed: {e}")

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts (list): List of texts to embed
            batch_size (int): Batch size for processing (handled by FastEmbed internally)
            
        Returns:
            np.ndarray: Array of embedding vectors
        """
        if not texts:
            return np.array([])
        
        # Generator to list conversion as FastEmbed returns a generator
        try:
            # FastEmbed handles batching internally, but we can pass batch_size hint if needed
            embeddings_generator = self.model.embed(texts, batch_size=batch_size)
            embeddings_list = list(embeddings_generator)
            return np.array(embeddings_list)
        except Exception as e:
            print(f"Error embedding texts: {e}")
            return np.array([])

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Embedding vector
        """
        if not text:
            return np.array([])
        
        embeddings = self.embed_texts([text])
        if len(embeddings) > 0:
            return embeddings[0]
        return np.array([])
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        """
        # FastEmbed doesn't expose this directly on the instance easily without embedding,
        # but BAAI/bge-small-en-v1.5 is 384. 
        # We can do a dummy embed to check.
        dummy_emb = self.embed_text("test")
        if len(dummy_emb) > 0:
            return len(dummy_emb)
        return 384 # Default for bge-small
    
    def get_model_info(self) -> dict:
        """
        Get information about the currently loaded model.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "library": "fastembed"
        }
