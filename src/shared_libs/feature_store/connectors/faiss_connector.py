# src/shared_libs/feature_store/connectors/faiss_connector.py

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import tempfile
import os
import uuid
import asyncio # Thêm asyncio

from feature_store.base.base_vector_store import BaseVectorStore

try:
    import faiss
except ImportError:
    faiss = None

logger = logging.getLogger(__name__)

class FAISSConnector(BaseVectorStore):
    """
    A stateful connector for the FAISS Vector Index (File I/O based).
    
    It implements the BaseVectorStore contract, enhanced with ASYNCHRONOUS I/O 
    to handle persistence and search operations without blocking the main event loop.
    """
    
    def __init__(self, vector_dim: int, index_type: str = 'flat', n_list: int = 50, **kwargs):
        """
        Initializes the FAISS Connector.
        """
        super().__init__(**kwargs)
        if faiss is None:
            raise ImportError("The 'faiss-cpu' or 'faiss-gpu' library is required for FAISSConnector.")
            
        self._vector_dim = vector_dim
        self._index_type = index_type.lower()
        self._n_list = n_list
        
        self._index: Optional[faiss.Index] = None # The core state
        self._metadata: Dict[str, Dict[str, Any]] = {} # Simple in-memory metadata store
        self._id_counter = 0
        self._is_fitted = False
        
        logger.info(f"FAISSConnector initialized. Dim: {vector_dim}, Type: {index_type}")

    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def connect(self):
        """Hardening 1: Ensures the index object is created and ready in memory."""
        if self._index is None:
            self._create_index()
            logger.info("FAISS index created in memory.")
        
    def disconnect(self):
        """Hardening 2: Clears the index from memory."""
        self._index = None
        logger.info("FAISS index disconnected (cleared from memory).")
    
    def _create_index(self):
        """Internal method to instantiate the FAISS index based on config."""
        if self._index_type == 'flat':
            self._index = faiss.IndexFlatL2(self._vector_dim)
        elif self._index_type == 'ivfflat':
            # IVFFlat requires training (handled by fit method)
            quantizer = faiss.IndexFlatL2(self._vector_dim)
            self._index = faiss.IndexIVFFlat(quantizer, self._vector_dim, self._n_list, faiss.METRIC_L2)
        else:
            raise ValueError(f"Unsupported FAISS index type: {self._index_type}")
        
    # ----------------------------------------------------
    # CRUD / I/O OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 3: Adds vectors and metadata to the index (Synchronous)."""
        if self._index is None: self.connect()
        if vectors.ndim != 2 or vectors.shape[1] != self._vector_dim:
            raise ValueError(f"Vectors must be 2D NumPy array ({vectors.shape[0]} x {self._vector_dim}).")

        try:
            ids = [str(self._id_counter + i) for i in range(vectors.shape[0])]
            self._index.add(vectors.astype('float32'))
            
            for i, doc_id in enumerate(ids):
                self._metadata[doc_id] = metadatas[i] if metadatas and i < len(metadatas) else {}
            
            self._id_counter += vectors.shape[0]
            self._is_fitted = True
            logger.debug(f"Added {vectors.shape[0]} vectors to FAISS index. Total count: {self._index.ntotal}")
            return ids
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS: {e}", exc_info=True)
            raise RuntimeError("FAISS add operation failed.") from e

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Hardening 4: Performs similarity search (Synchronous)."""
        if self._index is None: self.connect()
        if not self._is_fitted: return []
        if query_vector.ndim == 1: query_vector = query_vector.reshape(1, -1)
        
        try:
            # D: distances, I: internal indices
            distances, internal_ids = self._index.search(query_vector.astype('float32'), k=k)
            
            formatted_results = []
            
            for dist, internal_id in zip(distances[0], internal_ids[0]):
                external_id = str(internal_id) # Map to our sequential string ID
                
                if external_id in self._metadata:
                    formatted_results.append((external_id, float(dist), self._metadata[external_id]))
                else:
                    # Hardening: Handle missing metadata case
                    formatted_results.append((external_id, float(dist), {"warning": "Metadata missing"}))
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {e}", exc_info=True)
            return [] # Return empty list on search failure

    def delete(self, ids: List[str]) -> bool:
        """Hardening 5: FAISS deletion is a NO-OP for simple index types (Synchronous)."""
        logger.warning("FAISS deletion is not implemented for the current index type. This is a NO-OP.")
        return False

    # ----------------------------------------------------
    # ASYNCHRONOUS CRUD OPERATIONS (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------

    async def async_add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Asynchronously adds vectors using asyncio.to_thread."""
        return await asyncio.to_thread(self.add, vectors, metadatas)

    async def async_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Asynchronously executes similarity search (CRITICAL for RAG Inference)."""
        return await asyncio.to_thread(self.search, query_vector, k)

    async def async_delete(self, ids: List[str]) -> bool:
        """Asynchronously deletes vectors by ID."""
        # Vẫn dùng to_thread để đảm bảo tính nhất quán của Async contract, dù hàm đồng bộ là NO-OP
        return await asyncio.to_thread(self.delete, ids)


    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def fit(self, data: Any):
        """Hardening 6: For IVFFlat, 'fit' is used to train the quantizer (Synchronous)."""
        if self._index_type == 'ivfflat' and self._index and not self._index.is_trained:
            logger.info("Training FAISS IVFFlat quantizer...")
            
            if not isinstance(data, np.ndarray) or data.ndim != 2:
                raise TypeError("IVFFlat training requires a 2D NumPy array of sample vectors.")
                
            try:
                self._index.train(data.astype('float32'))
                logger.info("FAISS IVFFlat training complete.")
            except Exception as e:
                 logger.critical(f"Critical failure during FAISS IVFFlat training: {e}", exc_info=True)
                 raise RuntimeError("FAISS IVFFlat training failed.") from e
        else:
            logger.info("FAISS fit method called (No-op or already trained).")
        pass


    def get_state(self) -> Dict[str, Any]:
        """Hardening 7: Saves the FAISS index and metadata for persistence (Synchronous I/O)."""
        if not self._is_fitted or self._index is None: return {}
        
        # Chiến lược: Lưu index ra file tạm, đọc nội dung file thành bytes, serialize bytes
        with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as tmp_file:
            faiss.write_index(self._index, tmp_file.name)
            tmp_path = tmp_file.name
            
        with open(tmp_path, 'rb') as f:
            # Dùng latin-1 để mã hóa/giải mã bytes thành string an toàn
            index_content = f.read().decode('latin-1') 
        
        os.remove(tmp_path)
        
        return {
            "index_content": index_content,
            "metadata": self._metadata, # Serialize the metadata dict
            "vector_dim": self._vector_dim,
            "index_type": self._index_type,
            "id_counter": self._id_counter
        }

    def set_state(self, state: Dict[str, Any]):
        """Hardening 8: Loads the FAISS index and metadata from the serialized content (Synchronous I/O)."""
        if "index_content" not in state:
            raise ValueError("Invalid state format: 'index_content' key missing.")
            
        # Chiến lược: Recreate the index file from serialized content and load it.
        with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as tmp_file:
            index_content_bytes = state["index_content"].encode('latin-1')
            tmp_file.write(index_content_bytes)
            tmp_path = tmp_file.name
        
        try:
            self._index = faiss.read_index(tmp_path)
            self._metadata = state.get("metadata", {})
            self._vector_dim = state.get("vector_dim", self._index.d)
            self._index_type = state.get("index_type", 'loaded')
            self._id_counter = state.get("id_counter", self._index.ntotal)
            self._is_fitted = True
            logger.info(f"FAISS state loaded successfully. Total vectors: {self._index.ntotal}")
        except Exception as e:
            logger.critical(f"Failed to load FAISS state: {e}", exc_info=True)
            raise RuntimeError("FAISS state loading failed.") from e
        finally:
            os.remove(tmp_path)