from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class BaseComponent(ABC):
    """
    The fundamental abstract base class for all stateful components in the GenAI Factory 
    (Feature Store Connectors, Retrievers, some LLM wrappers, etc.).
    
    It enforces the MLOps contract for persistence and state management.
    """
    
    def __init__(self):
        # Trạng thái ban đầu: chưa sẵn sàng/chưa được huấn luyện
        self._is_fitted: bool = False
        
    @property
    def is_fitted(self) -> bool:
        """Returns True if the component has been fitted/initialized with data."""
        return self._is_fitted

    # ----------------------------------------------------
    # MLOPS STATE MANAGEMENT (HARDENING: State Contract)
    # ----------------------------------------------------

    @abstractmethod
    def fit(self, data: Any):
        """
        Hardening: Used to train/initialize stateful components 
        (e.g., training a FAISS IVFFlat index or initializing a Reranker model).
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Hardening: Serializes the component's internal state for saving (persistence).
        """
        pass

    @abstractmethod
    def set_state(self, state: Dict[str, Any]):
        """
        Hardening: Loads the component's internal state from a saved dictionary.
        """
        pass
    
    def transform(self, data: Any) -> Any:
        """
        A generic transformation method. Can be a no-op or used for data processing.
        NOTE: For stateless components, this can default to simply returning the data.
        """
        logger.warning(f"Component {self.__class__.__name__} transform method called (Default No-op).")
        return data

# --- VAI TRÒ CỦA LỚP BASE NÀY ---
# 1. BaseVectorStore sẽ kế thừa từ BaseComponent.
# 2. BaseRetriever cũng sẽ kế thừa từ BaseComponent.
# Điều này giúp thống nhất cách quản lý Indexing (fit/get_state/set_state) trong MLOps.