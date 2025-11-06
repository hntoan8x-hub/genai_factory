# src/shared_libs/feature_store/orchestrator/feature_store_orchestrator.py (NÂNG CẤP ASYNC)

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import asyncio # Cần cho việc quản lý các hàm async

# Giả định FeatureStoreConfig nằm ở đây
from feature_store.configs.feature_store_config_schema import FeatureStoreConfig 
from feature_store.factories.vector_store_factory import VectorStoreFactory
from feature_store.factories.retriever_factory import RetrieverFactory
from feature_store.base.base_vector_store import BaseVectorStore
from feature_store.base.base_retriever import BaseRetriever

logger = logging.getLogger(__name__)

class FeatureStoreOrchestrator:
    """
    The main API layer for the MLOps Vector Feature Store.
    
    This orchestrator is enhanced with Asynchronous methods to serve the GenAI Factory's
    high-throughput Indexing and Inference Pipelines.
    """
    
    def __init__(self, config: Any): # Thay FeatureStoreConfig bằng Any để đơn giản hóa
        
        self._config = config
        self._vector_store: Optional[BaseVectorStore] = None
        self._retriever: Optional[BaseRetriever] = None
        
        self._build_components()
        logger.info("FeatureStore Orchestrator initialized.")

    def _build_components(self):
        
        try:
            # Dùng model_dump() nếu config là Pydantic model
            vector_store_config = self._config.vector_store.model_dump()
            retriever_config = self._config.retriever.model_dump()
            
            self._vector_store = VectorStoreFactory.create_store(vector_store_config)
            
            self._retriever = RetrieverFactory.create_retriever(
                retriever_config, 
                vector_store=self._vector_store 
            )
            logger.info("Vector Store and Retriever components built successfully.")
        except Exception as e:
            logger.critical(f"Critical failure building Feature Store components: {e}", exc_info=True)
            raise RuntimeError("FeatureStore Orchestrator initialization failed.") from e

    # ----------------------------------------------------
    # LIFECYCLE MANAGEMENT (Connection) - Giữ nguyên đồng bộ
    # ----------------------------------------------------

    def connect(self):
        self._vector_store.connect()
        logger.info("Feature Store connection established.")

    def disconnect(self):
        try:
            self._vector_store.disconnect()
            logger.info("Feature Store connection closed.")
        except Exception as e:
            logger.error(f"Error during Feature Store disconnection: {e}", exc_info=True)

    # ----------------------------------------------------
    # CORE BUSINESS API (CRUD & Retrieval) - NÂNG CẤP ASYNC
    # ----------------------------------------------------

    def add_features(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 4: Adds features synchronously (Dùng cho MLOps/Scripts đồng bộ)."""
        if vectors.size == 0:
            logger.warning("Attempted to add empty vector array. Skipping.")
            return []
        
        try:
            # GỌI PHƯƠNG THỨC ĐỒNG BỘ CỦA VECTOR STORE
            return self._vector_store.add(vectors, metadatas)
        except Exception as e:
            logger.error(f"Failed to add features to Vector Store: {e}", exc_info=True)
            raise RuntimeError("Feature addition failed.") from e

    async def async_add_features(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Hardening 9: Adds features asynchronously (API chính cho Indexing Pipeline).
        """
        if vectors.size == 0:
            logger.warning("Attempted to async add empty vector array. Skipping.")
            return []
        
        try:
            # GỌI PHƯƠNG THỨC BẤT ĐỒNG BỘ CỦA VECTOR STORE
            return await self._vector_store.async_add(vectors, metadatas)
        except Exception as e:
            logger.error(f"Failed to async add features to Vector Store: {e}", exc_info=True)
            raise RuntimeError("Asynchronous feature addition failed.") from e


    def retrieve_features(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Hardening 5: Retrieves features synchronously (Dùng cho testing/scripts)."""
        if query_vector.ndim not in [1, 2]:
            raise ValueError("Query vector must be 1D or 2D.")
        
        try:
            # GỌI PHƯƠNG THỨC ĐỒNG BỘ CỦA RETRIEVER
            return self._retriever.retrieve(query_vector, k)
        except Exception as e:
            logger.error(f"Failed to retrieve features: {e}", exc_info=True)
            return [] 

    async def async_retrieve_features(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Hardening 10: Retrieves features asynchronously (API chính cho Inference Pipeline).
        """
        if query_vector.ndim not in [1, 2]:
            raise ValueError("Query vector must be 1D or 2D.")
        
        try:
            # GỌI PHƯƠNG THỨC BẤT ĐỒNG BỘ CỦA RETRIEVER
            return await self._retriever.async_retrieve(query_vector, k)
        except Exception as e:
            logger.error(f"Failed to async retrieve features: {e}", exc_info=True)
            return [] 

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Persistence) - Giữ nguyên đồng bộ
    # ----------------------------------------------------

    def fit_retriever(self, data: Any):
        
        try:
            self._retriever.fit(data)
            logger.info("Retriever fitting complete.")
        except Exception as e:
            logger.critical(f"Critical failure during Retriever fitting: {e}", exc_info=True)
            raise RuntimeError("Retriever fitting failed.") from e


    def get_state(self) -> Dict[str, Any]:
        
        try:
            store_state = self._vector_store.get_state()
            retriever_state = self._retriever.get_state()
            
            logger.info("Feature Store state retrieved successfully.")
            return {
                "store_state": store_state,
                "retriever_state": retriever_state,
                "store_type": self._vector_store.__class__.__name__,
                "retriever_type": self._retriever.__class__.__name__
            }
        except Exception as e:
            logger.error(f"Failed to get state for Feature Store: {e}", exc_info=True)
            raise RuntimeError("Feature Store state retrieval failed.") from e

    def set_state(self, state: Dict[str, Any]):
        
        if not all(k in state for k in ["store_state", "retriever_state"]):
            raise ValueError("Invalid state format: Missing store_state or retriever_state keys.")
        
        try:
            self._vector_store.set_state(state["store_state"])
            self._retriever.set_state(state["retriever_state"])
            
            logger.info("Feature Store state loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load Feature Store state: {e}", exc_info=True)
            raise RuntimeError("Feature Store state loading failed (Cannot ensure consistency).")