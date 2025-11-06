from abc import abstractmethod
from typing import Any, List, Dict, Tuple
import logging

# Giả định BaseComponent nằm ở shared_libs/base/
from shared_libs.base.base_component import BaseComponent 

logger = logging.getLogger(__name__)

class BaseChunker(BaseComponent):
    """
    Abstract base class for text chunking strategies.
    It takes raw text and applies a segmentation algorithm (e.g., recursive split, markdown split) 
    to create smaller, meaningful overlapping chunks.
    """
    
    def __init__(self, chunk_size: int, chunk_overlap: int, **kwargs):
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Chunker là stateless
        pass

    # ----------------------------------------------------
    # CORE CHUNKING LOGIC
    # ----------------------------------------------------
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Hardening: Splits the input text into smaller, optimized chunks based on the configured strategy.
        
        Args:
            text: Văn bản thô đã được trích xuất từ Loader.
            metadata: Metadata gốc của tài liệu (ví dụ: source_id, document_type).
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: Danh sách các cặp (chunk_content, chunk_metadata).
        """
        pass
    
    # NOTE: Chunking là CPU-bound, không cần async_chunk trừ khi có I/O nặng bên trong.
    # Ta giữ phương thức đồng bộ để đơn giản hóa quá trình điều phối.

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Stateless - Fulfilling Contract)
    # ----------------------------------------------------
    
    def fit(self, data: Any):
        """Chunker is stateless (no-op)."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Returns empty state."""
        return {}

    def set_state(self, state: Dict[str, Any]):
        """No-op."""
        pass