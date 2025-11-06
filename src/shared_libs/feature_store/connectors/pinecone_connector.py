# src/shared_libs/feature_store/connectors/pinecone_connector.py

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import uuid
import asyncio # Thêm asyncio
from feature_store.base.base_vector_store import BaseVectorStore

try:
    from pinecone import Pinecone, Index, InitFuture, PodType, Metric
    from pinecone.exceptions import PineconeException
    # Giả định security_utils.py đã được Hardening để tải secrets
    from data_ingestion.utils.security_utils import get_secret_from_env 
except ImportError:
    Pinecone = None
    PineconeException = None
    get_secret_from_env = None

logger = logging.getLogger(__name__)

# Hardening 1: Define environment variable keys for API Key and Environment
PINECONE_API_KEY_ENV = "PINECONE_API_KEY"
PINECONE_ENV_ENV = "PINECONE_ENVIRONMENT" 

class PineconeConnector(BaseVectorStore):
    """
    A stateful connector for the Pinecone Vector Database service (API-based).
    
    It implements the BaseVectorStore contract, enhanced with ASYNCHRONOUS I/O.
    """
    
    def __init__(self, index_name: str, vector_dim: int, metric: str = 'cosine', **kwargs):
        """
        Initializes the Pinecone Connector.
        """
        super().__init__(**kwargs)
        if Pinecone is None:
            raise ImportError("The 'pinecone-client' library is required for PineconeConnector.")
            
        self._index_name = index_name
        self._vector_dim = vector_dim
        self._metric = metric
        self._index_kwargs = kwargs
        
        self._client: Optional[Pinecone] = None
        self._index: Optional[Index] = None
        self._is_fitted = False
        
        logger.info(f"PineconeConnector initialized. Index: {index_name}, Dim: {vector_dim}")

    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def connect(self):
        """Hardening 2: Establishes the connection and ensures the index is ready (Synchronous)."""
        try:
            # Hardening 3: Securely load credentials
            api_key = get_secret_from_env(PINECONE_API_KEY_ENV)
            environment = get_secret_from_env(PINECONE_ENV_ENV)
            
            # Initialize the client
            self._client = Pinecone(api_key=api_key, environment=environment)
            
            # Create index if it does not exist (Idempotent operation)
            if self._index_name not in self._client.list_indexes().names:
                self._client.create_index(
                    name=self._index_name,
                    dimension=self._vector_dim,
                    metric=self._metric,
                    **self._index_kwargs
                )
                logger.warning(f"Pinecone index '{self._index_name}' created.")
            
            # Connect to the index
            self._index = self._client.Index(self._index_name)
            
            # Check status (optional, but good for resilience)
            index_status = self._client.describe_index(self._index_name).status.state
            if index_status != 'Ready':
                 logger.warning(f"Pinecone index status is '{index_status}'. Waiting is advised.")
                 
            self._is_fitted = True
            logger.info(f"Pinecone connected to index '{self._index_name}'. Status: {index_status}")
            
        except RuntimeError as e:
            logger.critical(f"CRITICAL: Missing Pinecone secrets. Error: {e}")
            raise RuntimeError("Pinecone connection failed due to missing secrets.") from e
        except PineconeException as e:
            logger.critical(f"Pinecone API error during connection/creation: {e}", exc_info=True)
            raise RuntimeError("Pinecone API connection failed.") from e
        except Exception as e:
            logger.critical(f"Unexpected error during Pinecone connection: {e}", exc_info=True)
            raise RuntimeError("Pinecone connection failed.") from e

    def disconnect(self):
        """Hardening 4: Closes the client (clears the reference)."""
        self._client = None
        self._index = None
        logger.info("Pinecone client disconnected/cleared.")
        
    # ----------------------------------------------------
    # CRUD OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 5: Upserts vectors and metadata (Synchronous)."""
        if self._index is None: self.connect()
        if vectors.ndim != 2 or vectors.shape[1] != self._vector_dim:
            raise ValueError(f"Vectors must be 2D NumPy array (N x {self._vector_dim}).")
            
        try:
            num_vectors = vectors.shape[0]
            ids = [str(uuid.uuid4()) for _ in range(num_vectors)]
            
            # Prepare data for upsert
            vectors_to_upsert = []
            for i in range(num_vectors):
                vectors_to_upsert.append(
                    (ids[i], vectors[i].tolist(), metadatas[i] if metadatas else {})
                )
            
            # Use upsert (Pinecone's method for add/update)
            self._index.upsert(vectors=vectors_to_upsert, namespace="") # Assuming default namespace
            
            self._is_fitted = True
            logger.debug(f"Upserted {num_vectors} vectors to Pinecone index.")
            return ids
        except PineconeException as e:
            logger.error(f"Pinecone API error during upsert: {e}", exc_info=True)
            raise RuntimeError("Pinecone add operation failed.") from e
        except Exception as e:
            logger.error(f"Failed to add vectors to Pinecone: {e}", exc_info=True)
            raise RuntimeError("Pinecone add operation failed.") from e


    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Hardening 6: Executes vector similarity search (Synchronous)."""
        if self._index is None: self.connect()
        if query_vector.ndim == 1: query_vector = query_vector.reshape(1, -1)
        
        try:
            results = self._index.query(
                vector=query_vector[0].tolist(), # Pinecone expects a single query vector
                top_k=k,
                include_values=False, 
                include_metadata=True,
                namespace=""
            )
            
            formatted_results = []
            for match in results.get('matches', []):
                # Pinecone returns score (higher is better)
                formatted_results.append((
                    match.id,
                    match.score,
                    match.metadata if match.metadata else {}
                ))
            
            logger.debug(f"Pinecone search completed. Retrieved {len(formatted_results)} results.")
            return formatted_results
        except PineconeException as e:
            logger.error(f"Pinecone API error during search: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}", exc_info=True)
            return []

    def delete(self, ids: List[str]) -> bool:
        """Hardening 7: Deletes vectors by ID (Synchronous)."""
        if self._index is None: self.connect()
        
        try:
            self._index.delete(ids=ids, namespace="")
            logger.info(f"Deleted {len(ids)} vectors from Pinecone.")
            return True
        except PineconeException as e:
            logger.error(f"Pinecone API error during delete: {e}", exc_info=True)
            return False

    # ----------------------------------------------------
    # ASYNCHRONOUS CRUD OPERATIONS (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------

    async def async_add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Asynchronously upserts vectors using asyncio.to_thread."""
        return await asyncio.to_thread(self.add, vectors, metadatas)

    async def async_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Asynchronously executes vector similarity search (CRITICAL for RAG Inference)."""
        return await asyncio.to_thread(self.search, query_vector, k)

    async def async_delete(self, ids: List[str]) -> bool:
        """Asynchronously deletes vectors by ID."""
        return await asyncio.to_thread(self.delete, ids)

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def fit(self, data: Any):
        """Hardening 8: 'fit' is a no-op as schema is created on connection/add."""
        logger.info("Pinecone fit method called. Index creation is handled upon connection.")
        pass

    def get_state(self) -> Dict[str, Any]:
        """Hardening 9: Saves the state by saving connection config."""
        return {
            "index_name": self._index_name,
            "vector_dim": self._vector_dim,
            "metric": self._metric,
        }

    def set_state(self, state: Dict[str, Any]):
        """Hardening 10: Loads the state by updating configuration parameters and reconnecting."""
        if "index_name" not in state:
            raise ValueError("Invalid state format: 'index_name' key missing.")
            
        self._index_name = state["index_name"]
        self._vector_dim = state["vector_dim"]
        self._metric = state["metric"]
        
        # Reconnecting verifies the connection and loads the index
        self.connect() 
        logger.info("Pinecone state loaded successfully (configuration re-established).")