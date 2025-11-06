# src/shared_libs/feature_store/factories/vector_store_factory.py

from typing import Dict, Any, Type
from feature_store.base.base_vector_store import BaseVectorStore
from feature_store.connectors.chromadb_connector import ChromaDBConnector
from feature_store.connectors.faiss_connector import FAISSConnector
from feature_store.connectors.milvus_connector import MilvusConnector
from feature_store.connectors.weaviate_connector import WeaviateConnector 
from feature_store.connectors.pinecone_connector import PineconeConnector
import logging

logger = logging.getLogger(__name__)

# --- Utility for Security Hardening (Reused) ---
def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Redacts sensitive connection parameters for secure logging."""
    sanitized = params.copy()
    # Keys that might contain network details or secrets
    sensitive_keys = ['host', 'port', 'path', 'persist_path', 'api_key', 'token', 'uri'] 
    
    for key in sanitized:
        if any(sk in key.lower() for sk in sensitive_keys):
            sanitized[key] = '***REDACTED_CONNECTION***'
    return sanitized
# -----------------------------------------------

class VectorStoreFactory:
    """
    A production-grade factory for creating stateful BaseVectorStore connector instances.
    
    Ensures secure logging and robust instantiation of vector storage components.
    """
    _registry: Dict[str, Type[BaseVectorStore]] = {
        "chromadb": ChromaDBConnector,
        "faiss": FAISSConnector,
        "milvus": MilvusConnector,
        "weaviate": WeaviateConnector,
        "pinecone": PineconeConnector
    }

    @classmethod
    def create_store(cls, config: Dict[str, Any]) -> BaseVectorStore:
        """
        Creates a vector store connector instance based on the configuration.
        """
        store_type = config.get("type")
        params = config.get("params", {})
        
        # Hardening 1: Initial Validation
        if not store_type or not isinstance(store_type, str):
             logger.error("Configuration missing 'type' key or key is invalid.")
             raise ValueError("Vector Store configuration must contain a valid 'type' key.")

        if store_type not in cls._registry:
            logger.error(f"Unsupported store type: '{store_type}'. Available: {list(cls._registry.keys())}")
            raise ValueError(f"Unsupported store type: '{store_type}'")
            
        store_class = cls._registry[store_type]
        sanitized_params = _sanitize_params(params)
        
        try:
            logger.info(f"Creating vector store connector: {store_type}")
            # Hardening 2: Instantiate the connector (connection is done by Orchestrator later)
            return store_class(**params)
        except TypeError as e:
            error_msg = f"Failed to create store '{store_type}': Missing/invalid parameters. Sanitized params: {sanitized_params}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Details: {e}") from e
        except Exception as e:
            error_msg = f"Failed to create store '{store_type}'. Sanitized params: {sanitized_params}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Critical error: {e}") from e