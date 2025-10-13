import mlflow
from typing import Dict, Any

class MLflowAdapter:
    """
    Adapts logging for MLflow, pushing training and evaluation metrics.
    
    This class simplifies logging runs, parameters, and metrics to MLflow,
    providing experiment tracking and reproducibility.
    """
    
    def __init__(self, experiment_name: str):
        """Initializes the MLflow experiment."""
        mlflow.set_experiment(experiment_name)
    
    def log_run(self, run_name: str, params: Dict[str, Any], metrics: Dict[str, Any]):
        """
        Logs a single run with its parameters and metrics.
        
        Args:
            run_name (str): The name for the MLflow run.
            params (Dict[str, Any]): A dictionary of parameters to log.
            metrics (Dict[str, Any]): A dictionary of metrics to log.
        """
        with mlflow.start_run(run_name=run_name):
            for key, value in params.items():
                mlflow.log_param(key, value)
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
