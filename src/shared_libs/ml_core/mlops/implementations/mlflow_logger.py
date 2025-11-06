# src/shared_libs/mlops/implementations/mlflow_logger.py (CẬP NHẬT)

import logging
from typing import Dict, Any, Union, Optional
import mlflow
import torch
# Thêm import cho Hugging Face (phổ biến trong GenAI)
try:
    import transformers
    import mlflow.transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    
# Import các thư viện khác (giả định)
try:
    import sklearn
    import mlflow.sklearn 
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from shared_libs.mlops.base.base_tracker import BaseTracker
from shared_libs.mlops.implementations.mlflow_client_wrapper import MLflowClientWrapper
from shared_libs.mlops.utils.mlflow_exceptions import MLflowServiceError

logger = logging.getLogger(__name__)

class MLflowLogger(BaseTracker):
    """
    Concrete implementation of BaseTracker for MLflow, supporting various model flavors,
    with special hardening for GenAI/Transformers models.
    """
    def __init__(self, tracking_uri: Optional[str] = None):
        self.client_wrapper = MLflowClientWrapper(tracking_uri=tracking_uri)

    def start_run(self, run_name: Optional[str] = None) -> mlflow.ActiveRun:
        try:
            # Hardening: Thêm check cho nested run nếu cần
            active_run = mlflow.start_run(run_name=run_name, nested=True)
            logger.info(f"Started MLflow run with ID: {active_run.info.run_id}")
            return active_run
        except Exception as e:
            raise MLflowServiceError(f"Failed to start MLflow run: {e}")

    def end_run(self, status: str = "FINISHED") -> None:
        try:
            mlflow.end_run(status)
            logger.info(f"Ended MLflow run with status: {status}")
        except Exception as e:
            # Hardening: Chỉ ghi log lỗi thay vì làm sập quá trình kết thúc run
            logger.error(f"Failed to cleanly end MLflow run: {e}")

    
    def log_param(self, key: str, value: Any) -> None:
        mlflow.log_param(key, value)

    def log_params(self, params: Dict[str, Any]) -> None:
        mlflow.log_params(params)

    def log_metric(self, key: str, value: float) -> None:
        mlflow.log_metric(key, value)

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        mlflow.log_metrics(metrics)

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        mlflow.log_artifact(local_path, artifact_path)
        
    def log_model(self, model: Any, artifact_path: str) -> None:
        """
        Hardening: Logs a model using the appropriate MLflow flavor, prioritizing GenAI/Transformer.
        """
        
        flavor = "Generic Python (Custom/Wrapper)" # Giá trị mặc định
        model_logged = False
        
        # 1. GenAI/Hugging Face Transformers Check (Highest Priority)
        if TRANSFORMERS_AVAILABLE and isinstance(model, (transformers.PreTrainedModel, transformers.Pipeline)):
            mlflow.transformers.log_model(transformers_model=model, artifact_path=artifact_path)
            flavor = "Hugging Face Transformers (GenAI/NLP)"
            model_logged = True
            
        # 2. PyTorch Check (Thường dùng cho mô hình Deep Learning tùy chỉnh)
        elif not model_logged and isinstance(model, torch.nn.Module):
            mlflow.pytorch.log_model(pytorch_model=model, artifact_path=artifact_path)
            flavor = "PyTorch (Deep Learning)"
            model_logged = True
            
        # 3. Scikit-learn Check (Thường dùng cho mô hình truyền thống)
        elif not model_logged and SKLEARN_AVAILABLE and 'sklearn' in model.__class__.__module__: 
            mlflow.sklearn.log_model(sk_model=model, artifact_path=artifact_path)
            flavor = "Scikit-learn"
            model_logged = True

        # 4. Fallback: Generic Python Function (CRITICAL HARDENING)
        # Sử dụng pyfunc làm fallback cho các wrapper API (như OpenAI Wrapper) hoặc custom logic
        if not model_logged:
            mlflow.pyfunc.log_model(python_model=model, artifact_path=artifact_path)
            
        logger.info(f"Model logged as artifact at '{artifact_path}' using {flavor} flavor.")