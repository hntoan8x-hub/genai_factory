# src/shared_libs/ingestion/configs/rag_ingestion_config_schema.py

from typing import Optional, Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import logging
import os

logger = logging.getLogger(__name__)

# --- 1. CONFIGS CẤP THÀNH PHẦN (Component Configuration) ---

class ChunkingConfig(BaseModel):
    """Cấu hình cho chiến lược chia đoạn văn bản (Chunking)."""
    model_config = ConfigDict(extra='forbid')
    
    chunk_size: int = Field(512, gt=0, description="Kích thước tối đa của một đoạn (token hoặc ký tự). Phải lớn hơn 0.")
    chunk_overlap: int = Field(50, ge=0, description="Số lượng token/ký tự chồng lấn giữa các đoạn. Phải lớn hơn hoặc bằng 0.")
    strategy: Literal["recursive_text", "markdown", "html", "semantic"] = Field(
        "recursive_text", 
        description="Chiến lược chia đoạn văn bản (Recursive, Markdown, HTML, Semantic)."
    )

    @field_validator('chunk_overlap')
    def validate_overlap_vs_size(cls, v, info):
        # Hardening 1: Đảm bảo độ chồng lấn nhỏ hơn kích thước đoạn
        chunk_size = info.data.get('chunk_size')
        if chunk_size is not None and v >= chunk_size:
            raise ValueError("Chunk overlap must be strictly less than chunk size.")
        return v
    
class EmbeddingModelRef(BaseModel):
    """Tham chiếu và cấu hình cơ bản cho mô hình nhúng (Embedding LLM)."""
    model_config = ConfigDict(extra='forbid')
    
    config_key: str = Field(..., description="Key trong llm_config.yaml trỏ đến Embedding Model.")
    vector_dim: int = Field(..., gt=0, description="Kích thước vector đầu ra (D). Phải khớp với FeatureStoreConfig.")

# --- 2. CONFIG GỐC (ROOT CONFIG - Quality Gate) ---

class RAGIngestionConfig(BaseModel):
    """
    Schema cấu hình chính cho RAG Ingestion Pipeline (Data Loading, Chunking, Embedding).
    Hoạt động như một Quality Gate toàn cục cho quá trình tiền xử lý và nhúng.
    """
    model_config = ConfigDict(extra='forbid') 
    
    # Cấu hình Data Source
    source_uri: str = Field(..., description="S3 URI hoặc đường dẫn thư mục cục bộ chứa tài liệu thô.")
    file_types: List[Literal["pdf", "docx", "xlsx", "txt", "html", "json", "xml"]] = Field(
        ["pdf", "docx", "txt"], 
        description="Danh sách các loại file được hỗ trợ để tải và xử lý."
    )
    
    # Cấu hình Chunking
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    
    # Cấu hình Embedding
    embedding_model: EmbeddingModelRef = Field(..., description="Tham chiếu và thông số của mô hình nhúng.")

    # -----------------------------------------------------------------
    # HARDENING: GLOBAL CONSISTENCY CHECKS
    # -----------------------------------------------------------------
    
    @model_validator(mode='after')
    def validate_global_consistency(self) -> 'RAGIngestionConfig':
        """
        Hardening 2: Kiểm tra tính nhất quán (Consistency) của các cấu hình.
        """
        # Kiểm tra tính hợp lệ của URI (Mô phỏng)
        uri = self.source_uri
        if not uri.startswith("s3://") and not os.path.isdir(uri):
            # Lưu ý: Cần import os
            logger.warning(f"Ingestion URI '{uri}' is not an S3 path or a local directory. Proceeding with caution.")
        
        # NOTE: Trong hệ thống hoàn chỉnh, cần kiểm tra RAGIngestionConfig.embedding_model.vector_dim
        # có khớp với FeatureStoreConfig.vector_store.params.vector_dim.
        # Tuy nhiên, kiểm tra chéo này sẽ diễn ra tại tầng cao hơn (ví dụ: Service Factory),
        # nơi cả hai config được tải đồng thời. Ở đây, ta chỉ kiểm tra tính hợp lệ nội bộ.
        
        return self