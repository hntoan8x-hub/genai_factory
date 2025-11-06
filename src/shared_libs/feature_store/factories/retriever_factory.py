# src/shared_libs/feature_store/factories/retriever_factory.py

from typing import Dict, Any, Type
from feature_store.base.base_retriever import BaseRetriever
from feature_store.base.base_vector_store import BaseVectorStore
from feature_store.retrievers.dense_retriever import DenseRetriever
from feature_store.retrievers.hybrid_retriever import HybridRetriever
from feature_store.retrievers.reranker import Reranker
import logging

logger = logging.getLogger(__name__)

class RetrieverFactory:
    """
    A production-grade factory for creating stateful/stateless BaseRetriever instances.
    
    It handles the necessary dependency injection of the Vector Store connector.
    """
    _registry: Dict[str, Type[BaseRetriever]] = {
        "dense": DenseRetriever,
        "hybrid": HybridRetriever,
        "reranker": Reranker,
    }

    @classmethod
    def create_retriever(cls, config: Dict[str, Any], vector_store: BaseVectorStore) -> BaseRetriever:
        """
        Hardening 1: Creates a retriever instance, injecting the required BaseVectorStore dependency.
        
        Args:
            config: A dictionary with 'type' and 'params' keys.
            vector_store: The fully initialized BaseVectorStore object (Dependency Injection).
            
        Returns:
            An instance of a class inheriting from BaseRetriever.
        """
        retriever_type = config.get("type")
        # Hardening 2: Separate params that are NOT the dependency
        params = config.get("params", {}) 

        if not retriever_type or not isinstance(retriever_type, str):
             logger.error("Configuration missing 'type' key or key is invalid.")
             raise ValueError("Retriever configuration must contain a valid 'type' key.")

        if not isinstance(vector_store, BaseVectorStore):
             logger.error("Dependency injection failed: 'vector_store' is not a valid BaseVectorStore instance.")
             raise TypeError("Retriever creation requires a valid BaseVectorStore instance for injection.")

        if retriever_type not in cls._registry:
            logger.error(f"Unsupported retriever type: '{retriever_type}'. Available: {list(cls._registry.keys())}")
            raise ValueError(f"Unsupported retriever type: '{retriever_type}'")
            
        retriever_class = cls._registry[retriever_type]
        
        try:
            logger.info(f"Creating retriever: {retriever_type}, injecting VectorStore dependency.")
            # Hardening 3: Inject the dependency first, then pass other parameters
            return retriever_class(vector_store=vector_store, **params) 
        except TypeError as e:
            error_msg = f"Failed to create retriever '{retriever_type}': Missing/invalid parameters. Check if 'vector_store' was passed."
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Details: {e}") from e
        except Exception as e:
            error_msg = f"Failed to create retriever '{retriever_type}'. Critical error during instantiation."
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Critical error: {e}") from e