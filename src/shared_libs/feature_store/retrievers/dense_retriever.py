# src/shared_libs/feature_store/retrievers/dense_retriever.py

from typing import List, Dict, Any, Tuple
import numpy as np
import logging
import asyncio # Thêm asyncio
from feature_store.base.base_retriever import BaseRetriever
from feature_store.base.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)

class DenseRetriever(BaseRetriever):
        
    def __init__(self, vector_store: BaseVectorStore):
        super().__init__(vector_store)
        logger.info("DenseRetriever initialized. Ready for raw vector search.")

    # ----------------------------------------------------
    # CORE RETRIEVAL LOGIC (Đồng bộ)
    # ----------------------------------------------------

    def retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 1: Executes raw search using the underlying Vector Store (Synchronous)."""
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        try:
            # Gọi phương thức search đồng bộ của Vector Store
            results_tuple = self._vector_store.search(query_vector=query_vector, k=k)
            
            formatted_results = []
            for doc_id, score, metadata in results_tuple:
                formatted_results.append({
                    "id": doc_id,
                    "score": float(score),
                    "metadata": metadata
                })
            
            logger.debug(f"Dense retrieval successful. Found {len(formatted_results)} results.")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Critical error during dense retrieval search: {e}", exc_info=True)
            raise RuntimeError("Dense retrieval search failed due to Vector Store error.") from e

    # ----------------------------------------------------
    # ASYNCHRONOUS RETRIEVAL LOGIC (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------
    
    async def async_retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 5: Executes raw search using the underlying Vector Store (Asynchronous)."""
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        try:
            # GỌI PHƯƠNG THỨC ASYNC_SEARCH CỦA VECTOR STORE
            results_tuple = await self._vector_store.async_search(query_vector=query_vector, k=k)
            
            formatted_results = []
            for doc_id, score, metadata in results_tuple:
                formatted_results.append({
                    "id": doc_id,
                    "score": float(score),
                    "metadata": metadata
                })
            
            logger.debug(f"Dense async retrieval successful. Found {len(formatted_results)} results.")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Critical error during dense async retrieval search: {e}", exc_info=True)
            raise RuntimeError("Dense async retrieval search failed due to Vector Store error.") from e

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Giữ nguyên)
    # ----------------------------------------------------

    def fit(self, data: Any):
        logger.info("Dense Retriever is stateless. Skipping fit operation.")
        pass

    def get_state(self) -> Dict[str, Any]:
        return {}

    def set_state(self, state: Dict[str, Any]):
        if state:
            logger.warning("Attempted to set state on a stateless Dense Retriever. State ignored.")
        pass