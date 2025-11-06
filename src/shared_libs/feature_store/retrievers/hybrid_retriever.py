# src/shared_libs/feature_store/retrievers/hybrid_retriever.py

from typing import List, Dict, Any, Tuple
import numpy as np
import logging
import asyncio # Thêm asyncio
from feature_store.base.base_retriever import BaseRetriever
from feature_store.base.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)

# Hardening 1: RRF (Reciprocal Rank Fusion) Constant
RRF_K = 60 

class HybridRetriever(BaseRetriever):
    
    def __init__(self, vector_store: BaseVectorStore):
        super().__init__(vector_store)
        logger.info(f"HybridRetriever initialized. Fusion algorithm: RRF (K={RRF_K}).")

    # ----------------------------------------------------
    # FUSION LOGIC (Giữ nguyên, logic này là CPU-bound, không cần async)
    # ----------------------------------------------------
    
    def _reciprocal_rank_fusion(self, ranked_lists: List[List[Dict[str, Any]]], k: int) -> List[Dict[str, Any]]:
        """Implements the Reciprocal Rank Fusion (RRF) algorithm."""
        fused_scores = {}
        
        for ranked_list in ranked_lists:
            for rank, item in enumerate(ranked_list):
                doc_id = item.get('id')
                if doc_id is None: continue

                score = 1.0 / (RRF_K + rank + 1)
                
                fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + score
        
        sorted_results = sorted(
            fused_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )
        
        minimal_fused_results = [{'id': doc_id, 'score': score} for doc_id, score in sorted_results[:k]]
        return minimal_fused_results


    # ----------------------------------------------------
    # CORE RETRIEVAL LOGIC (Đồng bộ)
    # ----------------------------------------------------

    def retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 3: Executes hybrid search by combining dense search and simulated sparse search (Synchronous)."""
        # NOTE: Trong môi trường đồng bộ, ta gọi phương thức đồng bộ của Vector Store
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        dense_results_tuple = self._vector_store.search(query_vector=query_vector, k=k * 5)
        
        # ... (Tạo sparse_results giả lập và logic RRF giữ nguyên)
        dense_results = [{'id': doc_id, 'score': score, 'metadata': metadata} 
                         for doc_id, score, metadata in dense_results_tuple]

        sparse_results: List[Dict[str, Any]] = [
            {'id': res['id'], 'score': np.random.rand(), 'metadata': res['metadata']} 
            for res in dense_results 
        ]
        
        fused_results_minimal = self._reciprocal_rank_fusion([dense_results, sparse_results], k)

        # 4. Final Formatting & Metadata Lookup (Giữ nguyên)
        final_results = []
        dense_map = {res['id']: res for res in dense_results} 

        for minimal_res in fused_results_minimal:
            doc_id = minimal_res['id']
            if doc_id in dense_map:
                final_results.append({
                    'id': doc_id,
                    'score': minimal_res['score'], 
                    'metadata': dense_map[doc_id]['metadata'] 
                })
                
        logger.info(f"Hybrid retrieval successful. Fused {len(final_results)} results.")
        return final_results
    
    # ----------------------------------------------------
    # ASYNCHRONOUS RETRIEVAL LOGIC (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------
    
    async def async_retrieve(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 4: Executes hybrid search asynchronously."""
        if not isinstance(query_vector, np.ndarray) or query_vector.ndim not in [1, 2]:
            raise TypeError("Query vector must be a 1D or 2D NumPy array.")
            
        # 1. Dense Search (GỌI PHƯƠNG THỨC ASYNC_SEARCH CỦA VECTOR STORE)
        dense_results_tuple = await self._vector_store.async_search(query_vector=query_vector, k=k * 5)
        
        dense_results = [{'id': doc_id, 'score': score, 'metadata': metadata} 
                         for doc_id, score, metadata in dense_results_tuple]

        # 2. Sparse Search (Simulated/Abstracted source - Vẫn cần chạy I/O nếu là ElasticSearch)
        # Giả sử mô phỏng này là CPU-bound (không blocking) hoặc I/O nhẹ, có thể chạy trực tiếp.
        sparse_results: List[Dict[str, Any]] = [
            {'id': res['id'], 'score': np.random.rand(), 'metadata': res['metadata']} 
            for res in dense_results 
        ]
        
        # 3. Fusion (RRF) - CPU-bound, chạy trực tiếp
        fused_results_minimal = self._reciprocal_rank_fusion([dense_results, sparse_results], k)

        # 4. Final Formatting & Metadata Lookup
        final_results = []
        dense_map = {res['id']: res for res in dense_results}

        for minimal_res in fused_results_minimal:
            doc_id = minimal_res['id']
            if doc_id in dense_map:
                final_results.append({
                    'id': doc_id,
                    'score': minimal_res['score'], 
                    'metadata': dense_map[doc_id]['metadata'] 
                })
                
        logger.info(f"Hybrid async retrieval successful. Fused {len(final_results)} results.")
        return final_results


    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Giữ nguyên)
    # ----------------------------------------------------

    def fit(self, data: Any):
        logger.info("Hybrid Retriever is stateless (logic-based). Skipping fit operation.")
        pass

    def get_state(self) -> Dict[str, Any]:
        return {}

    def set_state(self, state: Dict[str, Any]):
        if state:
            logger.warning("Attempted to set state on a stateless Hybrid Retriever. State ignored.")
        pass