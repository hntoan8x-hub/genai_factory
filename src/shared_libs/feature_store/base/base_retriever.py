# src/shared_libs/feature_store/base/base_retriever.py

from abc import abstractmethod
from typing import List, Dict, Any, Union
import numpy as np
import logging
# BỎ BaseTextComponent, import BaseComponent mới
from shared_libs.ml_core.base.base_component import BaseComponent
from feature_store.base.base_vector_store import BaseVectorStore # Dependency

logger = logging.getLogger(__name__)

# Kế thừa từ BaseComponent
class BaseRetriever(BaseComponent): 
    """
    Abstract base class for all feature retrieval components.
    ENHANCEMENT: Inherits MLOps contract from BaseComponent and defines async retrieval.
    """
    
    def __init__(self, vector_store: BaseVectorStore):
        """Initializes the retriever, establishing a dependency on a BaseVectorStore."""
        super().__init__()
        if not isinstance(vector_store, BaseVectorStore):
            raise TypeError("Retriever must be initialized with an instance of BaseVectorStore.")
        self._vector_store = vector_store #

    # ----------------------------------------------------
    # CORE RETRIEVAL LOGIC (Đồng bộ)
    # ----------------------------------------------------

    @abstractmethod
    def retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Executes the retrieval logic synchronously."""
        pass #
    
    # ----------------------------------------------------
    # CORE RETRIEVAL LOGIC (Bất đồng bộ)
    # ----------------------------------------------------

    @abstractmethod
    async def async_retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Asynchronously executes the retrieval logic (Critical for RAG inference)."""
        pass
    
    # OVERRIDE: transform (Giữ nguyên logic transform)
    def transform(self, data: Union[np.ndarray, List[np.ndarray]], k: int = 5) -> List[List[Dict[str, Any]]]:
        # Logic transform đồng bộ
        if not isinstance(data, list) or not all(isinstance(item, np.ndarray) for item in data):
            raise TypeError("Input to Retriever.transform must be List[np.ndarray].") #
        
        # Hardening: Gọi phương thức đồng bộ
        return [self.retrieve(query_vector=vec, k=k) for vec in data]