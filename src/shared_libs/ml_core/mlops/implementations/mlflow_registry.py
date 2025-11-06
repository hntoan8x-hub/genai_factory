# src/shared_libs/mlops/implementations/mlflow_registry.py

import logging
from typing import Dict, Any, List, Optional
import mlflow
from mlflow.exceptions import MlflowException # Thêm import cho Exception

from shared_libs.mlops.base.base_registry import BaseRegistry
from shared_libs.mlops.implementations.mlflow_client_wrapper import MLflowClientWrapper
from shared_libs.mlops.utils.mlflow_exceptions import MLflowServiceError, MLflowAPIError
from shared_libs.mlops.utils.retry_utils import retry # Import cho resilience

logger = logging.getLogger(__name__)

class MLflowRegistry(BaseRegistry):
    """
    Concrete implementation of BaseRegistry for MLflow Model Registry,
    handling versioning, tagging, and stage transitions.
    """
    def __init__(self, tracking_uri: Optional[str] = None):
        self.client_wrapper = MLflowClientWrapper(tracking_uri=tracking_uri)
        self.client = self.client_wrapper.client

    # ... (register_model và get_latest_version giữ nguyên logic) ...
    def register_model(self, model_name: str, run_id: str, artifact_path: str, description: Optional[str] = None) -> Any:
        try:
            model_uri = f"runs:/{run_id}/{artifact_path}"
            # Sử dụng create_registered_model, nhưng bao bọc trong try/except để tránh lỗi nếu đã tồn tại
            try:
                 self.client.create_registered_model(model_name)
            except MlflowException:
                 logger.debug(f"Registered model '{model_name}' already exists.")
            
            model_version = self.client.create_model_version(
                name=model_name,
                source=model_uri,
                run_id=run_id,
                description=description
            )
            logger.info(f"Registered model '{model_name}' (version {model_version.version}) from run '{run_id}'.")
            return model_version
        except Exception as e:
            raise MLflowServiceError(f"Failed to register model: {e}")

    def get_latest_version(self, model_name: str, stage: str = "Production") -> Optional[Any]:
        try:
            return self.client.get_latest_versions(model_name, stages=[stage])
        except Exception as e:
            logger.error(f"Failed to get latest version for model '{model_name}' at stage '{stage}': {e}")
            return None
    
    @retry(retries=3)
    def tag_model_version(self, model_name: str, version: int, tags: Dict[str, str]) -> None:
        """
        Hardening 1: Tags a specific version of a registered model with custom metadata.
        (Crucial for linking model version to Git SHA, Config Hash, etc.)
        """
        try:
            for key, value in tags.items():
                self.client.set_model_version_tag(
                    name=model_name,
                    version=version,
                    key=key,
                    value=value
                )
            logger.info(f"Tagged model '{model_name}' version {version} with {len(tags)} tags.")
        except Exception as e:
            raise MLflowServiceError(f"Failed to tag model version: {e}")

    @retry(retries=3)
    def transition_model_stage(self, model_name: str, version: int, new_stage: str) -> None:
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=new_stage
            )
            logger.info(f"Transitioned model '{model_name}' version {version} to stage '{new_stage}'.")
        except Exception as e:
            raise MLflowServiceError(f"Failed to transition model stage: {e}")

    @retry(retries=3)
    def get_model_uri(self, model_name: str, stage: str = "Production") -> Optional[str]:
        """
        Hardening 2: Retrieves the standard MLflow loading URI (models:/<name>/<stage>).
        """
        try:
            # We don't need to resolve the full run ID path here.
            # Returning the standard Stage URI ensures consistency for load functions.
            versions = self.client.get_latest_versions(model_name, stages=[stage])
            if versions:
                return f"models:/{model_name}/{stage}" 
            return None
        except Exception as e:
            logger.error(f"Failed to get model URI for '{model_name}' at stage '{stage}': {e}")
            return None