from abc import abstractmethod
from typing import Any, List, Dict
import logging

# Giả định BaseComponent nằm ở shared_libs/base/
from shared_libs.base.base_component import BaseComponent 

logger = logging.getLogger(__name__)

class BaseLoader(BaseComponent):
    """
    Abstract base class for document loaders (PDF, DOCX, JSON).
    It defines the contract for asynchronously loading and extracting raw text and metadata 
    from a specific file source or type.
    """
    
    def __init__(self, **kwargs):
        super().__init__()
        # Loaders thường là stateless, nhưng tuân thủ BaseComponent contract.
        pass

    @property
    @abstractmethod
    def supported_file_type(self) -> str:
        """Returns the file extension this loader supports (e.g., 'pdf', 'docx')."""
        pass

    # ----------------------------------------------------
    # CORE LOADING LOGIC (ASYNC - HARDENING)
    # ----------------------------------------------------
    
    @abstractmethod
    async def async_load(self, file_path_or_data: Any) -> Dict[str, Any]:
        """
        Hardening: Asynchronously loads a single file/data chunk and extracts its content 
        and initial metadata.
        
        Args:
            file_path_or_data: Đường dẫn cục bộ, S3 key, hoặc raw bytes của tệp.
            
        Returns:
            Dict: {'content': str, 'metadata': Dict[str, Any]}
        """
        pass
    
    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (Stateless - Fulfilling Contract)
    # ----------------------------------------------------
    
    def fit(self, data: Any):
        """Loader is stateless (no-op)."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Returns empty state."""
        return {}

    def set_state(self, state: Dict[str, Any]):
        """No-op."""
        pass