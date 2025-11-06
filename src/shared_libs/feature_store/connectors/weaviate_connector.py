# src/shared_libs/feature_store/connectors/weaviate_connector.py

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import uuid
import json
import asyncio # Thêm asyncio
from feature_store.base.base_vector_store import BaseVectorStore

try:
    import weaviate
    from weaviate.util import generate_uuid5
    from weaviate.exceptions import UnexpectedStatusCodeException, RequestsConnectionError
except ImportError:
    weaviate = None

logger = logging.getLogger(__name__)

# Hardening 1: Define standard field names for Weaviate schema consistency
WEAVIATE_ID_FIELD = "feature_id"
WEAVIATE_TEXT_FIELD = "text_source" 

class WeaviateConnector(BaseVectorStore):
    """
    A stateful connector for the Weaviate Vector Database service.
    
    Implements the BaseVectorStore contract, enhanced with ASYNCHRONOUS I/O.
    """
    
    def __init__(self, url: str, class_name: str, vector_dim: int, **kwargs):
        """
        Initializes the Weaviate Connector.
        """
        super().__init__(**kwargs)
        if weaviate is None:
            raise ImportError("The 'weaviate-client' library is required for WeaviateConnector.")
            
        self._url = url
        self._class_name = class_name
        self._vector_dim = vector_dim
        self._client: Optional[weaviate.Client] = None
        self._is_fitted = False
        
        logger.info(f"WeaviateConnector initialized. Class: {class_name}, URL: {url}")

    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def connect(self):
        """Hardening 2: Establishes the network connection to the Weaviate service (Synchronous)."""
        try:
            if self._client is None:
                self._client = weaviate.Client(url=self._url)
            
            # Check connection status
            if not self._client.is_live():
                raise RequestsConnectionError("Weaviate service is not live or reachable.")
                
            # Create or validate the schema (Class)
            self._create_or_update_schema()
            
            # Check for data existence
            self._is_fitted = self._client.query.get(self._class_name, ["_id"]).with_limit(1).do().get("data", {}).get("Get", {}).get(self._class_name) != None
            logger.info(f"Weaviate connected and class '{self._class_name}' ready. Live: {self._client.is_live()}.")
        except Exception as e:
            logger.critical(f"Critical failure connecting to Weaviate at {self._url}: {e}", exc_info=True)
            raise RuntimeError("Weaviate connection failed.") from e

    def disconnect(self):
        """Hardening 3: Releases the client instance."""
        self._client = None
        logger.info("Weaviate client disconnected/cleared.")
        
    def _create_or_update_schema(self):
        """Internal method to ensure the Weaviate schema (Class) exists."""
        schema = {
            "class": self._class_name,
            "vectorizer": "none", # Vectors are provided externally (by our encoder)
            "properties": [
                {"name": WEAVIATE_ID_FIELD, "dataType": ["text"]},
                {"name": WEAVIATE_TEXT_FIELD, "dataType": ["text"]} # Optional text field for display/debugging
            ]
        }
        
        try:
            if not self._client.schema.exists(self._class_name):
                self._client.schema.create_class(schema)
                logger.info(f"Weaviate class '{self._class_name}' created.")
            else:
                logger.debug(f"Weaviate class '{self._class_name}' already exists.")
        except Exception as e:
            logger.critical(f"Failed to create/validate Weaviate schema: {e}", exc_info=True)
            raise RuntimeError("Weaviate schema management failed.")

    # ----------------------------------------------------
    # CRUD OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 4: Inserts vectors and metadata into the Weaviate class (Synchronous)."""
        if self._client is None: self.connect()
        if vectors.ndim != 2 or vectors.shape[1] != self._vector_dim:
            raise ValueError(f"Vectors must be 2D NumPy array (N x {self._vector_dim}).")
            
        try:
            num_vectors = vectors.shape[0]
            ids = []
            
            with self._client.batch.simple_batch_request() as batch:
                for i in range(num_vectors):
                    # Hardening: Use UUID V5 for deterministic ID generation based on content/metadata
                    doc_id = str(generate_uuid5(str(vectors[i]) + json.dumps(metadatas[i] if metadatas else {})))
                    
                    data_properties = {
                        WEAVIATE_ID_FIELD: doc_id,
                        WEAVIATE_TEXT_FIELD: metadatas[i].get('text_source', '') if metadatas else ''
                    }
                    
                    # Add all extra metadata properties
                    if metadatas and metadatas[i]:
                        data_properties.update(metadatas[i])
                        
                    batch.add_data_object(
                        data_properties,
                        self._class_name,
                        vector=vectors[i].tolist(),
                        uuid=doc_id
                    )
                    ids.append(doc_id)
            
            self._is_fitted = True
            logger.debug(f"Batch added {num_vectors} vectors to Weaviate.")
            return ids
        except Exception as e:
            logger.error(f"Failed to add vectors to Weaviate: {e}", exc_info=True)
            raise RuntimeError("Weaviate add operation failed.") from e

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Hardening 5: Performs vector similarity search (Synchronous)."""
        if self._client is None: self.connect()
        if query_vector.ndim == 1: query_vector = query_vector.reshape(1, -1)
        
        try:
            # Query Weaviate using nearVector and return all properties
            response = (
                self._client.query
                .get(self._class_name, ["_additional {id, certainty, distance}", "*"])
                .with_near_vector({
                    "vector": query_vector[0].tolist()
                })
                .with_limit(k)
                .do()
            )
            
            formatted_results = []
            results = response.get("data", {}).get("Get", {}).get(self._class_name, [])
            
            for item in results:
                meta = item.pop("_additional")
                doc_id = meta.get("id")
                # Weaviate returns 'certainty' (score) or 'distance' (lower is better)
                score = meta.get("certainty", 1.0 - meta.get("distance", 1.0)) 
                
                formatted_results.append((
                    doc_id,
                    float(score),
                    item # Remaining item is the metadata
                ))
            
            logger.debug(f"Weaviate search completed. Retrieved {len(formatted_results)} results.")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search Weaviate: {e}", exc_info=True)
            return [] # Return empty list on search failure

    def delete(self, ids: List[str]) -> bool:
        """Hardening 6: Deletes objects by UUID (Synchronous)."""
        if self._client is None: self.connect()
        
        try:
            for doc_id in ids:
                 # Sử dụng ALL consistency level để đảm bảo xóa thành công
                 self._client.data_object.delete(doc_id, self._class_name, consistency_level=weaviate.data.replication.ConsistencyLevel.ALL)
            logger.info(f"Deleted {len(ids)} entities from Weaviate.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete entities from Weaviate: {e}", exc_info=True)
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
        return await asyncio.to_thread(self.delete, ids)

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def fit(self, data: Any):
        """Hardening 7: 'fit' is a no-op as indexing is handled internally."""
        logger.info("Weaviate fit method called. Indexing/Schema creation is handled internally.")
        pass

    def get_state(self) -> Dict[str, Any]:
        """Hardening 8: Saves the state by saving connection config."""
        return {
            "url": self._url,
            "class_name": self._class_name,
            "vector_dim": self._vector_dim,
        }

    def set_state(self, state: Dict[str, Any]):
        """Hardening 9: Loads the state by updating configuration parameters and reconnecting."""
        if "url" not in state:
            raise ValueError("Invalid state format: 'url' key missing.")
            
        self._url = state["url"]
        self._class_name = state["class_name"]
        self._vector_dim = state["vector_dim"]
        
        # Reconnecting verifies the connection and loads the collection
        self.connect() 
        logger.info("Weaviate state loaded successfully (configuration re-established).")