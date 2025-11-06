# src/shared_libs/feature_store/base/base_vector_store.py

from abc import abstractmethod
from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
# BỎ BaseTextComponent, import BaseComponent mới
from shared_libs.ml_core.base.base_component import BaseComponent 

logger = logging.getLogger(__name__)

# Kế thừa từ BaseComponent và ABC (được BaseComponent kế thừa)
class BaseVectorStore(BaseComponent): 
    """
    Abstract base class for all stateful Vector Database connectors.
    Enforces MLOps contract and async CRUD operations.
    """
    
    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (Giữ nguyên)
    # ----------------------------------------------------

    @abstractmethod
    def connect(self):
        """Establishes the connection."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Closes the connection cleanly."""
        pass

    # ----------------------------------------------------
    # CRUD / I/O OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    @abstractmethod
    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Adds new vectors (embeddings) and associated metadata."""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Performs a similarity search."""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Deletes vectors based on their unique IDs."""
        pass
    
    # ----------------------------------------------------
    # ASYNCHRONOUS CRUD OPERATIONS (Bất đồng bộ)
    # ----------------------------------------------------
    
    @abstractmethod
    async def async_add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Asynchronously adds new vectors."""
        pass

    @abstractmethod
    async def async_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Asynchronously performs a similarity search (Critical for RAG inference)."""
        pass

    @abstractmethod
    async def async_delete(self, ids: List[str]) -> bool:
        """Asynchronously deletes vectors."""
        pass

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Kế thừa từ BaseComponent)
    # ----------------------------------------------------
    
    def transform(self, data: Any) -> Any:
        # Vector Store không biến đổi dữ liệu; nó sẽ gọi BaseComponent.transform
        return super().transform(data)