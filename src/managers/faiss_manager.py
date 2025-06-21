# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
FAISS Vector Search Manager for Music Analyzer
"""
import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class FAISSManager:
    def __init__(self, index_dir: str = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize FAISS manager
        
        Args:
            index_dir: Directory to store FAISS indexes
            model_name: Sentence transformer model for embeddings
        """
        self.index_dir = index_dir or os.getenv('FAISS_INDEX_PATH', './faiss_indexes')
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = None
        self.id_to_metadata = {}
        self.next_id = 0
        
        # Load existing index if available
        self.load_index()
    
    def load_index(self):
        """Load existing FAISS index from disk"""
        index_path = os.path.join(self.index_dir, 'music.index')
        metadata_path = os.path.join(self.index_dir, 'music_metadata.pkl')
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.id_to_metadata = data['id_to_metadata']
                    self.next_id = data['next_id']
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Using IndexFlatIP for inner product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.id_to_metadata = {}
        self.next_id = 0
        logger.info("Created new FAISS index")
    
    def save_index(self):
        """Save FAISS index to disk"""
        index_path = os.path.join(self.index_dir, 'music.index')
        metadata_path = os.path.join(self.index_dir, 'music_metadata.pkl')
        
        try:
            faiss.write_index(self.index, index_path)
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'id_to_metadata': self.id_to_metadata,
                    'next_id': self.next_id
                }, f)
            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)
    
    async def add_transcription(self, file_id: str, transcription_id: str, 
                               text: str, metadata: Dict) -> int:
        """
        Add a transcription to the index
        
        Args:
            file_id: Music file ID
            transcription_id: Transcription ID
            text: Transcribed text
            metadata: Additional metadata (title, artist, genre, etc.)
        
        Returns:
            Internal FAISS ID
        """
        # Generate embedding
        embedding = await asyncio.to_thread(self.generate_embedding, text)
        
        # Add to index
        self.index.add(np.array([embedding]))
        
        # Store metadata
        self.id_to_metadata[self.next_id] = {
            'file_id': file_id,
            'transcription_id': transcription_id,
            'text': text[:500],  # Store preview
            'metadata': metadata,
            'indexed_at': datetime.utcnow().isoformat()
        }
        
        current_id = self.next_id
        self.next_id += 1
        
        # Save index periodically
        if self.next_id % 100 == 0:
            await asyncio.to_thread(self.save_index)
        
        return current_id
    
    async def search(self, query: str, k: int = 10, 
                    filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar transcriptions
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filters (genre, artist, etc.)
        
        Returns:
            List of search results with scores
        """
        if not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = await asyncio.to_thread(self.generate_embedding, query)
        
        # Search in index
        scores, indices = self.index.search(np.array([query_embedding]), k * 2)
        
        # Process results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # Invalid index
                continue
            
            metadata = self.id_to_metadata.get(idx)
            if not metadata:
                continue
            
            # Apply filters if provided
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if metadata.get('metadata', {}).get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append({
                'score': float(score),
                'file_id': metadata['file_id'],
                'transcription_id': metadata['transcription_id'],
                'text_preview': metadata['text'],
                'metadata': metadata['metadata'],
                'indexed_at': metadata['indexed_at']
            })
            
            if len(results) >= k:
                break
        
        return results
    
    async def search_by_lyrics(self, lyrics: str, k: int = 10) -> List[Dict]:
        """Search for songs containing specific lyrics"""
        return await self.search(lyrics, k)
    
    async def find_similar_songs(self, file_id: str, k: int = 10) -> List[Dict]:
        """Find songs similar to a given file"""
        # Find the transcription for this file
        for idx, metadata in self.id_to_metadata.items():
            if metadata['file_id'] == file_id:
                # Get the embedding for this file
                text = metadata.get('text', '')
                if text:
                    return await self.search(text, k + 1)  # +1 to exclude self
        return []
    
    async def remove_file(self, file_id: str):
        """Remove all embeddings for a file"""
        # Note: FAISS doesn't support deletion, so we mark as deleted
        # In production, you would periodically rebuild the index
        removed_count = 0
        for idx, metadata in list(self.id_to_metadata.items()):
            if metadata['file_id'] == file_id:
                del self.id_to_metadata[idx]
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Marked {removed_count} embeddings for deletion for file {file_id}")
            await asyncio.to_thread(self.save_index)
    
    async def get_statistics(self) -> Dict:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.embedding_dim,
            'index_size_mb': self._get_index_size_mb(),
            'unique_files': len(set(m['file_id'] for m in self.id_to_metadata.values())),
            'model_name': self.model.get_sentence_embedding_dimension()
        }
    
    def _get_index_size_mb(self) -> float:
        """Get index size in MB"""
        index_path = os.path.join(self.index_dir, 'music.index')
        if os.path.exists(index_path):
            return os.path.getsize(index_path) / (1024 * 1024)
        return 0.0

# Singleton instance
_faiss_manager = None

def get_faiss_manager() -> FAISSManager:
    """Get or create FAISS manager instance"""
    global _faiss_manager
    if _faiss_manager is None:
        _faiss_manager = FAISSManager()
    return _faiss_manager