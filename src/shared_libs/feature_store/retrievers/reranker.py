# src/shared_libs/feature_store/retrievers/reranker.py

from typing import List, Dict, Any, Tuple
import numpy as np
import logging
import joblib 
import tempfile
import os
import asyncio # Thêm asyncio

from feature_store.base.base_retriever import BaseRetriever
from feature_store.base.base_vector_store import BaseVectorStore

try:
    from sklearn.linear_model import LogisticRegression 
    from sklearn.exceptions import NotFittedError
except ImportError:
    LogisticRegression = None
    NotFittedError = None

logger = logging.getLogger(__name__)

class Reranker(BaseRetriever):
    """
    A stateful retriever component that reranks initial search results using a trained machine 
    learning model (the Reranker model).
    
    It adheres to the BaseRetriever contract and manages the Reranker model's state, enhanced with Async I/O.
    """
    
    def __init__(self, vector_store: BaseVectorStore, top_k_initial: int = 50, **kwargs):
        super().__init__(vector_store)
        if LogisticRegression is None:
            raise ImportError("Scikit-learn is required for Reranker (using LogisticRegression).")
            
        self._top_k_initial = top_k_initial
        self._reranker_model = LogisticRegression(**kwargs) 
        self._is_fitted = False
        
        logger.info(f"Reranker initialized. Initial retrieval size: {top_k_initial}.")
        
    def _rerank_logic(self, initial_results_tuple: List[Tuple[str, float, Dict[str, Any]]], k: int) -> List[Dict[str, Any]]:
        """
        Internal CPU-bound logic to perform feature extraction and model prediction.
        """
        initial_scores = np.array([score for _, score, _ in initial_results_tuple]).reshape(-1, 1)
        # Tạo feature giả: [score_ban_dau, 1/score_ban_dau]
        rerank_features = np.hstack([initial_scores, 1/initial_scores]) 
        
        try:
            # Dự đoán xác suất
            rerank_probabilities = self._reranker_model.predict_proba(rerank_features)[:, 1] 
            
            reranked_results = []
            for (doc_id, initial_score, metadata), new_score in zip(initial_results_tuple, rerank_probabilities):
                reranked_results.append({
                    "id": doc_id,
                    "score": float(new_score), 
                    "initial_score": float(initial_score),
                    "metadata": metadata
                })
            
            # Final Sorting and Truncation
            final_sorted_results = sorted(
                reranked_results,
                key=lambda x: x['score'],
                reverse=True
            )[:k]
            
            return final_sorted_results
            
        except Exception as e:
            logger.error(f"Critical error during Reranking logic: {e}", exc_info=True)
            # Trả về kết quả ban đầu (chưa sắp xếp lại) để đảm bảo tính sẵn sàng
            return [{'id': doc_id, 'score': score, 'metadata': metadata} for doc_id, score, metadata in initial_results_tuple[:k]]


    # ----------------------------------------------------
    # CORE RETRIEVAL LOGIC (Đồng bộ)
    # ----------------------------------------------------

    def retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 1: Performs initial retrieval, applies the Reranker model, and returns top K (Synchronous)."""
        if not self._is_fitted:
            raise RuntimeError("Reranker model is not fitted. Cannot retrieve.")
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        # 1. Initial Retrieval (Blocking I/O)
        initial_results_tuple = self._vector_store.search(query_vector=query_vector, k=self._top_k_initial)
        
        if not initial_results_tuple:
            return []

        # 2. Reranking (CPU-bound logic)
        return self._rerank_logic(initial_results_tuple, k)
        

    # ----------------------------------------------------
    # ASYNCHRONOUS RETRIEVAL LOGIC (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------
    
    async def async_retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 7: Performs initial retrieval and reranking asynchronously."""
        if not self._is_fitted:
            raise RuntimeError("Reranker model is not fitted. Cannot retrieve.")
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        # 1. Initial Retrieval (GỌI PHƯƠNG THỨC ASYNC_SEARCH CỦA VECTOR STORE)
        initial_results_tuple = await self._vector_store.async_search(query_vector=query_vector, k=self._top_k_initial)
        
        if not initial_results_tuple:
            return []

        # 2. Reranking (CPU-bound logic - Chạy trong thread để không chặn luồng chính)
        reranked_results = await asyncio.to_thread(self._rerank_logic, initial_results_tuple, k)
        
        return reranked_results


    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Giữ nguyên)
    # ----------------------------------------------------

    def fit(self, data: Tuple[np.ndarray, np.ndarray]):
        if not isinstance(data, tuple) or len(data) != 2:
             raise ValueError("Fit data must be a tuple (X, y) for supervised training.")
             
        X, y = data
        
        try:
            self._reranker_model.fit(X, y)
            self._is_fitted = True
            logger.info("Reranker model fitting complete.")
        except Exception as e:
            logger.critical(f"Critical failure during Reranker fitting: {e}", exc_info=True)
            raise RuntimeError("Reranker model fitting failed.") from e

    def get_state(self) -> Dict[str, Any]:
        if not self._is_fitted: return {}
            
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp_file:
            joblib.dump(self._reranker_model, tmp_file.name)
            tmp_path = tmp_file.name
            
        with open(tmp_path, 'rb') as f:
            model_content = f.read().decode('latin-1') 
        
        os.remove(tmp_path)
        
        return {
            "model_content": model_content,
            "top_k_initial": self._top_k_initial
        }

    def set_state(self, state: Dict[str, Any]):
        if "model_content" not in state:
            raise ValueError("Invalid state format: 'model_content' key missing.")
            
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp_file:
            model_content_bytes = state["model_content"].encode('latin-1')
            tmp_file.write(model_content_bytes)
            tmp_path = tmp_file.name
        
        try:
            self._reranker_model = joblib.load(tmp_path)
            self._is_fitted = True
            self._top_k_initial = state.get("top_k_initial", self._top_k_initial)
            logger.info("Reranker model state loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load Reranker model state: {e}", exc_info=True)
            raise RuntimeError("Reranker model state loading failed.") from e
        finally:
            os.remove(tmp_path)