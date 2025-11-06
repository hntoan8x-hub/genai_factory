# src/shared_libs/feature_store/connectors/chromadb_connector.py

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import uuid
import asyncio  # Thêm asyncio
import tempfile
import os

# Import BaseVectorStore đã được tinh chỉnh (kế thừa từ BaseComponent)
from feature_store.base.base_vector_store import BaseVectorStore 

try:
    import chromadb
    from chromadb import Documents, Embedding, IDs, Metadata, Collection
except ImportError:
    chromadb = None
    Collection = Any

logger = logging.getLogger(__name__)

class ChromaDBConnector(BaseVectorStore):
    """
    A stateful connector for the Chroma Vector Database, enhanced with ASYNCHRONOUS I/O.
    """
    
    def __init__(self, collection_name: str, path: Optional[str] = None, **kwargs):
        """
        Initializes the ChromaDB Connector.
        """
        super().__init__(**kwargs)
        if chromadb is None:
            raise ImportError("The 'chromadb' library is required for ChromaDBConnector.")
            
        self._collection_name = collection_name
        self._persist_path = path
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[Collection] = None
        self._is_fitted = False
        
        logger.info(f"ChromaDBConnector initialized. Collection: {collection_name}, Path: {path if path else 'In-Memory'}")

    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def connect(self):
        """Hardening 1: Establishes the ChromaDB client connection."""
        try:
            if self._persist_path:
                # Sử dụng PersistentClient cho lưu trữ trên đĩa
                self._client = chromadb.PersistentClient(path=self._persist_path)
            else:
                self._client = chromadb.Client() # In-memory
                
            self._collection = self._client.get_or_create_collection(name=self._collection_name)
            
            self._is_fitted = self._collection.count() > 0
            logger.info(f"ChromaDB connected and collection '{self._collection_name}' loaded. Count: {self._collection.count()}.")
        except Exception as e:
            logger.critical(f"Critical failure connecting to ChromaDB: {e}", exc_info=True)
            raise RuntimeError("ChromaDB connection failed.") from e

    def disconnect(self):
        """Hardening 2: Disconnects/Closes the ChromaDB client."""
        if self._client:
            self._client = None
            self._collection = None
            logger.info("ChromaDB client disconnected/cleared.")

    # ----------------------------------------------------
    # CRUD OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 3: Adds vectors and metadata to the collection (Synchronous)."""
        if self._collection is None:
            raise RuntimeError("ChromaDB is not connected. Call connect() first.")
        
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D NumPy array (N x D).")
            
        try:
            num_vectors = vectors.shape[0]
            ids = [str(uuid.uuid4()) for _ in range(num_vectors)]
            
            embeddings_list = vectors.tolist() 
            
            self._collection.add(
                embeddings=embeddings_list,
                ids=ids,
                metadatas=metadatas 
            )
            self._is_fitted = True
            logger.debug(f"Added {num_vectors} vectors to ChromaDB collection.")
            return ids
        except Exception as e:
            logger.error(f"Failed to add vectors to ChromaDB: {e}", exc_info=True)
            raise RuntimeError("ChromaDB add operation failed.") from e

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Hardening 4: Performs similarity search (Synchronous)."""
        if self._collection is None:
            raise RuntimeError("ChromaDB is not connected. Call connect() first.")
        if query_vector.ndim != 1 and query_vector.ndim != 2:
            raise ValueError("Query vector must be a 1D or 2D array.")
            
        try:
            query = query_vector.tolist() if query_vector.ndim == 1 else query_vector.tolist()
            
            results = self._collection.query(
                query_embeddings=[query], 
                n_results=k,
                include=['metadatas', 'distances'] 
            )
            
            formatted_results = []
            
            if results.get('ids') and results['ids'][0]:
                for doc_id, distance, metadata in zip(results['ids'][0], results['distances'][0], results['metadatas'][0]):
                    # Sử dụng khoảng cách (distance) làm score, vì Chroma trả về distance (thấp hơn là tốt hơn)
                    formatted_results.append((doc_id, distance, metadata if metadata else {})) 
            
            logger.debug(f"ChromaDB search completed. Retrieved {len(formatted_results)} results.")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}", exc_info=True)
            return [] 

    def delete(self, ids: List[str]) -> bool:
        """Hardening 5: Deletes vectors by ID (Synchronous)."""
        if self._collection is None:
            raise RuntimeError("ChromaDB is not connected. Call connect() first.")
        
        try:
            self._collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors from ChromaDB: {e}", exc_info=True)
            return False

    # ----------------------------------------------------
    # ASYNCHRONOUS CRUD OPERATIONS (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------

    async def async_add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Asynchronously adds vectors using asyncio.to_thread (IoC)."""
        return await asyncio.to_thread(self.add, vectors, metadatas)

    async def async_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Asynchronously executes similarity search (CRITICAL for RAG Inference)."""
        return await asyncio.to_thread(self.search, query_vector, k)

    async def async_delete(self, ids: List[str]) -> bool:
        """Asynchronously deletes vectors by ID."""
        return await asyncio.to_thread(self.delete, ids)


    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def fit(self, data: Any):
        """Hardening 6: 'fit' is a no-op as the index is built incrementally."""
        logger.info("ChromaDB fit method called. Index is built incrementally via add().")

    def get_state(self) -> Dict[str, Any]:
        """Hardening 7: Saves the state by saving the persistence path/config."""
        if self._persist_path:
            # Strategy: Save the path and collection name.
            return {
                "collection_name": self._collection_name,
                "persist_path": self._persist_path,
                "vector_count": self._collection.count() if self._collection else 0
            }
        else:
            logger.warning("Attempted to get state for in-memory ChromaDB. Index will be lost.")
            return {}

    def set_state(self, state: Dict[str, Any]):
        """Hardening 8: Loads the state by ensuring the client is reconnected to the persisted path."""
        if "persist_path" in state and state["persist_path"]:
            self._collection_name = state["collection_name"]
            self._persist_path = state["persist_path"]
            # Reconnecting automatically reloads the persisted index
            self.connect() 
        else:
            logger.warning("Attempted to set state from non-persisted state. Index will start empty.")