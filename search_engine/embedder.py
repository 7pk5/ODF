"""
Document and Query Embedder
Handles text embedding using sentence-transformers for semantic search.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import os
import re
from typing import List, Union

class Embedder:
    def __init__(self, model_name='BAAI/bge-large-en-v1.5'):
        """
        Initialize the embedder with the most accurate sentence transformer model available.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
                            'BAAI/bge-large-en-v1.5' - Current SOTA accuracy (default)
                            'sentence-transformers/all-mpnet-base-v2' - Excellent overall
                            'intfloat/e5-large-v2' - Very high accuracy
                            'BAAI/bge-base-en-v1.5' - Good accuracy, faster
                            'sentence-transformers/all-MiniLM-L12-v2' - Balanced
        """
        # Model options ranked by accuracy (higher = more accurate but slower)
        self.model_options = {
            'ultra_fast': 'all-MiniLM-L6-v2',                    # Fastest, lowest accuracy
            'fast': 'all-MiniLM-L12-v2',                         # Fast, decent accuracy
            'balanced': 'all-mpnet-base-v2',                     # Good balance
            'high_accuracy': 'BAAI/bge-base-en-v1.5',           # High accuracy
            'very_high_accuracy': 'intfloat/e5-large-v2',       # Very high accuracy
            'sota_accuracy': 'BAAI/bge-large-en-v1.5',          # State-of-the-art accuracy (default)
            'qa_optimized': 'multi-qa-mpnet-base-dot-v1',       # Best for Q&A
            'paraphrase': 'paraphrase-mpnet-base-v2',           # Best for paraphrasing
            'multilingual': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'  # Multilingual support
        }
        
        self.model_name = model_name
        self.model = None
        # Fallback models in order of preference (most accurate first)
        self.backup_models = [
            'BAAI/bge-base-en-v1.5',
            'intfloat/e5-base-v2', 
            'all-mpnet-base-v2',
            'all-MiniLM-L12-v2', 
            'all-MiniLM-L6-v2'
        ]
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model with fallback support."""
        models_to_try = [self.model_name] + self.backup_models
        
        for model_name in models_to_try:
            try:
                print(f"Loading embedding model: {model_name}")
                self.model = SentenceTransformer(model_name)
                self.model_name = model_name  # Update to the successfully loaded model
                print(f"Model '{model_name}' loaded successfully!")
                print(f"Model embedding dimension: {self.model.get_sentence_embedding_dimension()}")
                return
            except Exception as e:
                print(f"Failed to load model '{model_name}': {e}")
                continue
        
        raise RuntimeError("Failed to load any embedding model. Please check your internet connection and try again.")
    
    def embed_text(self, text, preprocess=True):
        """
        Generate embeddings for a single text with enhanced accuracy.
        
        Args:
            text (str): Text to embed
            preprocess (bool): Apply advanced preprocessing for better accuracy
            
        Returns:
            np.ndarray: Embedding vector
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        if not text or not text.strip():
            dim = self.get_embedding_dimension()
            return np.zeros(dim if dim is not None else 384)  # Default fallback dimension
        
        # Apply preprocessing for better accuracy
        if preprocess:
            text = self.preprocess_text(text, enhance_accuracy=True)
        
        try:
            embedding = self.model.encode(text, convert_to_tensor=False, normalize_embeddings=True)
            return embedding
        except Exception as e:
            print(f"Error embedding text: {e}")
            dim = self.get_embedding_dimension()
            return np.zeros(dim if dim is not None else 384)  # Default fallback dimension
    
    def embed_texts(self, texts, preprocess=True, batch_size=32):
        """
        Generate embeddings for multiple texts with enhanced accuracy and batch processing.
        
        Args:
            texts (list): List of texts to embed
            preprocess (bool): Apply advanced preprocessing for better accuracy
            batch_size (int): Number of texts to process in each batch
            
        Returns:
            np.ndarray: Array of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        if not texts:
            return np.array([])
        
        # Preprocess texts for better accuracy
        processed_texts = []
        for text in texts:
            if text and text.strip():
                if preprocess:
                    processed_text = self.preprocess_text(text, enhance_accuracy=True)
                    processed_texts.append(processed_text if processed_text else "empty document")
                else:
                    processed_texts.append(text.strip())
            else:
                processed_texts.append("empty document")
        
        try:
            # Use batch processing for better performance and accuracy
            embeddings = self.model.encode(
                processed_texts, 
                convert_to_tensor=False, 
                normalize_embeddings=True, 
                show_progress_bar=True,
                batch_size=batch_size
            )
            return embeddings
        except Exception as e:
            print(f"Error embedding texts: {e}")
            # Return zero vectors as fallback
            dim = self.get_embedding_dimension()
            fallback_dim = dim if dim is not None else 384
            return np.zeros((len(texts), fallback_dim))
    
    def get_embedding_dimension(self):
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Embedding dimension
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()
    
    def preprocess_text(self, text, max_length=512, enhance_accuracy=True):
        """
        Advanced text preprocessing for maximum embedding accuracy.
        
        Args:
            text (str): Raw text
            max_length (int): Maximum text length
            enhance_accuracy (bool): Apply advanced preprocessing for better accuracy
            
        Returns:
            str: Preprocessed text optimized for accurate embeddings
        """
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        
        if enhance_accuracy:
            # Remove excessive whitespace and normalize
            text = re.sub(r'\s+', ' ', text)
            
            # Remove or normalize special characters that might hurt embedding quality
            text = re.sub(r'[^\w\s\.,;:!?\-\(\)]', ' ', text)
            
            # Ensure sentences end properly for better semantic understanding
            text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
            
            # Remove very short words that don't add semantic value (but keep common short words)
            important_short_words = {'is', 'in', 'on', 'at', 'to', 'of', 'a', 'an', 'the', 'and', 'or', 'but', 'if', 'no', 'not'}
            words = text.split()
            filtered_words = []
            for word in words:
                if len(word) >= 2 or word.lower() in important_short_words:
                    filtered_words.append(word)
            text = ' '.join(filtered_words)
        
        # Intelligent truncation to preserve sentence boundaries
        if len(text) > max_length:
            # Try to cut at sentence boundary
            truncated = text[:max_length]
            last_sentence_end = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?')
            )
            
            if last_sentence_end > max_length * 0.7:  # If we can preserve most of the text
                text = truncated[:last_sentence_end + 1]
            else:
                # Cut at word boundary
                words = truncated.split()
                text = ' '.join(words[:-1])  # Remove potentially cut-off last word
        
        return text.strip()
    
    def switch_to_most_accurate_model(self):
        """
        Switch to the most accurate embedding model available.
        
        Returns:
            bool: True if successfully switched, False otherwise
        """
        accurate_models = [
            'BAAI/bge-large-en-v1.5',      # Current state-of-the-art
            'intfloat/e5-large-v2',        # Very high accuracy
            'BAAI/bge-base-en-v1.5',       # High accuracy, smaller
            'all-mpnet-base-v2'            # Reliable fallback
        ]
        
        for model_name in accurate_models:
            try:
                print(f"Attempting to load high-accuracy model: {model_name}")
                old_model = self.model
                self.model = SentenceTransformer(model_name)
                self.model_name = model_name
                print(f"Successfully switched to: {model_name}")
                print(f"New embedding dimension: {self.model.get_sentence_embedding_dimension()}")
                del old_model  # Free memory
                return True
            except Exception as e:
                print(f"Failed to load {model_name}: {e}")
                continue
        
        print("Could not switch to a more accurate model")
        return False

    def switch_to_fast_model(self):
        """
        Switch to a fast embedding model for high speed (lower accuracy).
        """
        fast_models = [
            'all-MiniLM-L6-v2',
            'all-MiniLM-L12-v2',
            'all-mpnet-base-v2'
        ]
        for model_name in fast_models:
            try:
                print(f"Switching to fast model: {model_name}")
                self.model = SentenceTransformer(model_name)
                self.model_name = model_name
                print(f"Fast model '{model_name}' loaded!")
                return True
            except Exception as e:
                print(f"Failed to load fast model '{model_name}': {e}")
                continue
        print("Could not switch to a fast model")
        return False

    def get_model_info(self):
        """
        Get information about the currently loaded model.
        
        Returns:
            dict: Model information
        """
        if not self.model:
            return {"error": "No model loaded"}
        
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'Unknown'),
            "model_type": "sentence-transformer"
        }

# The embedder now defaults to the most accurate model
embedder = Embedder()  # Uses BAAI/bge-large-en-v1.5 by default

# Or explicitly switch to the most accurate available
embedder.switch_to_most_accurate_model()

# Check what model you're using
info = embedder.get_model_info()
print(f"Using: {info['model_name']} with {info['embedding_dimension']} dimensions")
