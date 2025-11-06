# src/shared_libs/feature_store/connectors/milvus_connector.py

from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import logging
import uuid
import json
import asyncio # Thêm asyncio
from feature_store.base.base_vector_store import BaseVectorStore

try:
    from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
    from pymilvus.exceptions import MilvusException, ConnectionAborted
except ImportError:
    connections = None
    MilvusException = None

logger = logging.getLogger(__name__)

# Hardening 1: Define standard field names for Milvus schema consistency
MILVUS_PK_FIELD = "milvus_pk"
MILVUS_VECTOR_FIELD = "embedding"
MILVUS_METADATA_FIELD = "metadata_json" # Field to store all other metadata

class MilvusConnector(BaseVectorStore):
    """
    A stateful connector for the Milvus Vector Database service.
    
    Implements the BaseVectorStore contract, enhanced with ASYNCHRONOUS I/O.
    """
    
    def __init__(self, host: str, port: str, collection_name: str, vector_dim: int, **kwargs):
        """
        Initializes the Milvus Connector.
        """
        super().__init__(**kwargs)
        if connections is None:
            raise ImportError("The 'pymilvus' library is required for MilvusConnector.")
            
        self._host = host
        self._port = port
        self._collection_name = collection_name
        self._vector_dim = vector_dim
        self._alias = f"{host}:{port}_{collection_name}" # Unique connection identifier
        
        self._collection: Optional[Collection] = None
        self._is_fitted = False
        
        logger.info(f"MilvusConnector initialized. Collection: {collection_name}, Host: {host}")

    # ----------------------------------------------------
    # CONNECTION MANAGEMENT (BaseVectorStore Contract)
    # ----------------------------------------------------

    def connect(self):
        """Hardening 2: Establishes the network connection to the Milvus service."""
        try:
            # Connect to Milvus service
            connections.connect(alias=self._alias, host=self._host, port=self._port)
            
            # Check if collection exists and load it
            if utility.has_collection(self._collection_name, using=self._alias):
                self._collection = Collection(self._collection_name, using=self._alias)
                self._collection.load() # Load the collection into memory for searching
                self._is_fitted = self._collection.num_entities > 0
                logger.info(f"Milvus connected. Collection '{self._collection_name}' loaded. Entities: {self._collection.num_entities}")
            else:
                logger.warning(f"Milvus collection '{self._collection_name}' does not exist. Will create upon first fit/add.")
            
        except Exception as e:
            logger.critical(f"Critical failure connecting to Milvus at {self._host}:{self._port}: {e}", exc_info=True)
            raise RuntimeError("Milvus connection failed.") from e

    def disconnect(self):
        """Hardening 3: Releases the collection from memory and closes the network connection."""
        if self._collection:
            self._collection.release() # Release collection from memory
            self._collection = None
        
        if connections.has_connection(self._alias):
            connections.remove_connection(self._alias) # Close network connection
            logger.info("Milvus connection closed/released.")
            
    def _create_collection(self):
        """Internal method to create a Milvus Collection with a standard schema."""
        fields = [
            FieldSchema(name=MILVUS_PK_FIELD, dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=128),
            FieldSchema(name=MILVUS_VECTOR_FIELD, dtype=DataType.FLOAT_VECTOR, dim=self._vector_dim),
            FieldSchema(name=MILVUS_METADATA_FIELD, dtype=DataType.VARCHAR, max_length=4096) # Store metadata as JSON string
        ]
        schema = CollectionSchema(fields, description="Vector Store Collection")
        
        self._collection = Collection(
            name=self._collection_name,
            schema=schema,
            using=self._alias
        )
        logger.info(f"Milvus collection '{self._collection_name}' created with schema.")
        
        # Hardening: Create default index immediately after creation
        index_params = {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
        self._collection.create_index(MILVUS_VECTOR_FIELD, index_params)
        logger.info("Milvus default index created.")

    # ----------------------------------------------------
    # CRUD OPERATIONS (Đồng bộ)
    # ----------------------------------------------------

    def add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Hardening 4: Inserts vectors and JSON-serialized metadata (Synchronous)."""
        if self._collection is None:
            # Create collection if it doesn't exist
            if not utility.has_collection(self._collection_name, using=self._alias):
                 self._create_collection()
            else:
                 self.connect() # Reconnect to load the collection
                 
        if vectors.ndim != 2 or vectors.shape[1] != self._vector_dim:
            raise ValueError(f"Vectors must be 2D NumPy array (N x {self._vector_dim}).")
            
        try:
            num_vectors = vectors.shape[0]
            ids = [str(uuid.uuid4()) for _ in range(num_vectors)]
            
            # Prepare data for insertion (Milvus expects a list of columns)
            entities = [
                ids,
                vectors.tolist(),
                [json.dumps(m) for m in metadatas] if metadatas else [json.dumps({})] * num_vectors
            ]
            
            self._collection.insert(entities)
            self._collection.flush() # Ensure data is written
            self._is_fitted = True
            logger.debug(f"Inserted {num_vectors} entities into Milvus collection.")
            
            # Ensure the collection is loaded for immediate searching
            self._collection.load() 
            return ids
        except Exception as e:
            logger.error(f"Failed to add vectors to Milvus: {e}", exc_info=True)
            raise RuntimeError("Milvus insert operation failed.") from e

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Hardening 5: Executes vector similarity search (Synchronous)."""
        if self._collection is None or self._collection.num_entities == 0:
            logger.warning("Milvus collection not loaded or empty. Returning empty list.")
            return []
            
        if query_vector.ndim == 1: query_vector = query_vector.reshape(1, -1)
        
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            
            results = self._collection.search(
                data=query_vector.tolist(),
                anns_field=MILVUS_VECTOR_FIELD,
                param=search_params,
                limit=k,
                output_fields=[MILVUS_METADATA_FIELD]
            )
            
            formatted_results = []
            for hit in results[0]: # results[0] contains hits for the first query
                metadata = json.loads(hit.entity.get(MILVUS_METADATA_FIELD))
                formatted_results.append((
                    hit.id,
                    hit.distance, # Milvus returns distance (lower is better)
                    metadata
                ))
            
            logger.debug(f"Milvus search completed. Retrieved {len(formatted_results)} results.")
            return formatted_results
        except MilvusException as e:
             logger.error(f"Milvus search failed (API/Network error): {e}", exc_info=True)
             return []
        except Exception as e:
             logger.error(f"Failed to search Milvus: {e}", exc_info=True)
             return []

    def delete(self, ids: List[str]) -> bool:
        """Hardening 6: Deletes vectors by primary key (Synchronous)."""
        if self._collection is None:
            raise RuntimeError("Milvus is not connected. Call connect() first.")
        
        try:
            # Milvus delete requires a boolean expression
            expr = f"{MILVUS_PK_FIELD} in {ids}"
            self._collection.delete(expr)
            self._collection.flush()
            logger.info(f"Deleted entities from Milvus via expression: {expr}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete entities from Milvus: {e}", exc_info=True)
            return False

    # ----------------------------------------------------
    # ASYNCHRONOUS CRUD OPERATIONS (Nâng cấp Bất đồng bộ)
    # ----------------------------------------------------

    async def async_add(self, vectors: np.ndarray, metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Asynchronously adds vectors using asyncio.to_thread."""
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
        """Hardening 7: 'fit' is a no-op as schema is created on connection/add."""
        logger.info("Milvus fit method called. Indexing/Schema creation is handled internally/incrementally.")
        pass

    def get_state(self) -> Dict[str, Any]:
        """Hardening 8: Saves the state by saving connection config."""
        # For a remote Milvus service, the state is the connection configuration needed to reconnect.
        return {
            "collection_name": self._collection_name,
            "host": self._host,
            "port": self._port,
            "vector_dim": self._vector_dim,
            "alias": self._alias
        }

    def set_state(self, state: Dict[str, Any]):
        """Hardening 9: Loads the state by updating configuration parameters."""
        if "collection_name" not in state:
            raise ValueError("Invalid state format: 'collection_name' key missing.")
            
        self._collection_name = state["collection_name"]
        self._host = state["host"]
        self._port = state["port"]
        self._vector_dim = state["vector_dim"]
        self._alias = state["alias"]
        # Reconnecting verifies the connection and loads the collection
        self.connect() 
        logger.info("Milvus state loaded successfully (configuration re-established).")