# src/shared_libs/feature_store/configs/feature_store_config_schema.py

from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
import logging

logger = logging.getLogger(__name__)

# --- BASE CONFIGS ---

class BaseComponentConfig(BaseModel):
    # Hardening 1: Cấm các tham số thừa (typos)
    model_config = ConfigDict(extra='forbid') 
    type: str = Field(..., description="The unique type identifier for the component.")
    enabled: bool = Field(True, description="Flag to enable or disable the component.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameters passed to the component's constructor.")

# --- 1. VECTOR STORE SCHEMAS (Connectors) ---

class BaseVectorStoreConfig(BaseComponentConfig):
    # Validation cơ bản cho kích thước vector
    @field_validator('params', mode='before')
    def check_vector_dim(cls, params):
        if params and 'vector_dim' in params and not params['vector_dim'] > 0:
            raise ValueError("Vector store 'vector_dim' must be a positive integer.")
        return params

class ChromaDBConfig(BaseVectorStoreConfig):
    type: Literal["chromadb"]
    params: Dict[str, Any] = Field(..., description="Must contain 'collection_name' and 'vector_dim'.")

    @model_validator(mode='after')
    def validate_chroma_params(self) -> 'ChromaDBConfig':
        if not all(key in self.params for key in ['collection_name', 'vector_dim']):
            raise ValueError("ChromaDB requires 'collection_name' and 'vector_dim'.")
        return self

class FAISSConfig(BaseVectorStoreConfig):
    type: Literal["faiss"]
    params: Dict[str, Any] = Field(..., description="Must contain 'vector_dim'.")

    @model_validator(mode='after')
    def validate_faiss_params(self) -> 'FAISSConfig':
        if 'vector_dim' not in self.params:
            raise ValueError("FAISS requires 'vector_dim'.")
        return self

class MilvusConfig(BaseVectorStoreConfig):
    type: Literal["milvus"]
    params: Dict[str, Any] = Field(..., description="Must contain 'host', 'port', 'collection_name', and 'vector_dim'.")

    @model_validator(mode='after')
    def validate_milvus_params(self) -> 'MilvusConfig':
        if not all(key in self.params for key in ['host', 'port', 'collection_name', 'vector_dim']):
            raise ValueError("Milvus requires 'host', 'port', 'collection_name', and 'vector_dim'.")
        return self

class PineconeConfig(BaseVectorStoreConfig):
    type: Literal["pinecone"]
    params: Dict[str, Any] = Field(..., description="Must contain 'index_name' and 'vector_dim'.")

    @model_validator(mode='after')
    def validate_pinecone_params(self) -> 'PineconeConfig':
        if not all(key in self.params for key in ['index_name', 'vector_dim']):
            raise ValueError("Pinecone requires 'index_name' and 'vector_dim'.")
        if self.params.get('metric') not in ['cosine', 'dotproduct', 'euclidean', None]:
            raise ValueError("Pinecone 'metric' must be one of: cosine, dotproduct, or euclidean.")
        return self
        
class WeaviateConfig(BaseVectorStoreConfig):
    type: Literal["weaviate"]
    params: Dict[str, Any] = Field(..., description="Must contain 'url', 'class_name', and 'vector_dim'.")

    @model_validator(mode='after')
    def validate_weaviate_params(self) -> 'WeaviateConfig':
        if not all(key in self.params for key in ['url', 'class_name', 'vector_dim']):
            raise ValueError("Weaviate requires 'url', 'class_name', and 'vector_dim'.")
        return self

# --- 2. RETRIEVER SCHEMAS (Logic) ---

class BaseRetrieverConfig(BaseComponentConfig):
    pass

class DenseRetrieverConfig(BaseRetrieverConfig):
    type: Literal["dense"]
    params: Dict[str, Any] = Field(default_factory=dict, description="No specific parameters required.")

class HybridRetrieverConfig(BaseRetrieverConfig):
    type: Literal["hybrid"]
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for fusion (e.g., RRF_K).")

class RerankerConfig(BaseRetrieverConfig):
    type: Literal["reranker"]
    params: Dict[str, Any] = Field(..., description="Must contain 'top_k_initial' and model parameters.")
    
    @model_validator(mode='after')
    def validate_reranker_params(self) -> 'RerankerConfig':
        if not self.params.get('top_k_initial', 1) > 0:
            raise ValueError("Reranker 'top_k_initial' must be positive.")
        return self

# --- ROOT CONFIG (Quality Gate) ---

class FeatureStoreConfig(BaseModel):
    """
    The main configuration schema for the Feature Store (Vector Database) Pipeline.
    """
    model_config = ConfigDict(extra='forbid') 
    
    vector_store: Union[ChromaDBConfig, FAISSConfig, MilvusConfig, PineconeConfig, WeaviateConfig] = Field(
        ...,
        description="Configuration for the vector database connector."
    )
    
    retriever: Union[DenseRetrieverConfig, HybridRetrieverConfig, RerankerConfig] = Field(
        ...,
        description="Configuration for the retrieval logic (Dense, Hybrid, or Reranker)."
    )
    
    @model_validator(mode='after')
    def validate_dependencies_and_state(self) -> 'FeatureStoreConfig':
        # Hardening 2: Đảm bảo cả hai thành phần đều được enabled (mô hình kiến trúc đơn giản)
        if not self.vector_store.enabled:
            raise ValueError("Vector Store must be enabled.")
        if not self.retriever.enabled:
            raise ValueError("Retriever must be enabled.")
        
        # Hardening 3: Validation logic that requires checking the consistency between components
        # Ví dụ: Kích thước vector phải khớp giữa các mô hình nếu có nhiều hơn 1 nguồn.
        vector_dim_store = self.vector_store.params.get('vector_dim')
        # Giả định: Nếu có Reranker, nó có thể cần biết kích thước vector ban đầu.
        # Tuy nhiên, kiểm tra quan trọng nhất là đảm bảo các mô hình khác sử dụng kích thước này.
        
        if vector_dim_store is None:
            # Lỗi này đã được các validator riêng bắt, nhưng kiểm tra lần cuối.
            raise ValueError("Vector dimension is missing from the Vector Store config.")

        # (Lưu ý: Logic kiểm tra với Embedding Model nằm ở lớp trên gọi ConfigLoader)

        return self
        