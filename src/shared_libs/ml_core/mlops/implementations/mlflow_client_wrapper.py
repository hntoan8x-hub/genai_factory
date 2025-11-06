# src/shared_libs/mlops/implementations/mlflow_client_wrapper.py

import logging
from typing import Optional
import mlflow
from shared_libs.mlops.utils.retry_utils import retry
# Hardening: Import Security Utils và Utilities
from data_ingestion.utils.security_utils import get_secret_from_env, mask_sensitive_info 

logger = logging.getLogger(__name__)

# Hardening 1: Define environment variable key for tracking URI
MLFLOW_TRACKING_URI_ENV = "MLFLOW_TRACKING_URI"

class MLflowClientWrapper:
    """
    A Hardened wrapper class for the MLflow client to handle secure connection, 
    resilience (retry), and singleton pattern.
    """
    _instance = None
    _client_instance = None

    def __new__(cls, tracking_uri: Optional[str] = None):
        """Singleton pattern to ensure only one client wrapper instance exists."""
        if cls._instance is None:
            cls._instance = super(MLflowClientWrapper, cls).__new__(cls)
            # Hardening 2: Bỏ qua tham số đầu vào và buộc phải load từ ENV
            cls._instance.tracking_uri = get_secret_from_env(MLFLOW_TRACKING_URI_ENV, required=False)
            cls._instance._init_client()
        return cls._instance

    @retry(retries=3)
    def _init_client(self) -> None:
        """Initializes the MLflow client and sets the tracking URI with retry logic."""
        if self._client_instance is None:
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
            
            self._client_instance = mlflow.tracking.MlflowClient()
            
            # Hardening 3: Log an toàn URI (che đi credentials nếu có)
            current_uri = mlflow.get_tracking_uri()
            safe_uri = mask_sensitive_info({"uri": current_uri}).get("uri", current_uri)
            
            logger.info(f"MLflow client initialized with URI: {safe_uri}")

    @property
    def client(self) -> mlflow.tracking.MlflowClient:
        """Returns the MLflow client instance, attempting to re-initialize if necessary."""
        if self._client_instance is None:
            # Hardening 4: Thử khởi tạo lại nếu client bị mất (Resilience)
            self._init_client() 
        
        if self._client_instance is None:
            # Nếu retry thất bại, raise lỗi runtime
             raise RuntimeError("MLflow client failed to initialize after all retries. Check tracking URI.")
             
        return self._client_instance