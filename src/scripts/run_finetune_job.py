# src/scripts/run_finetune_job.py

import sys
import argparse
import logging
from typing import Dict, Any

from shared_libs.factory.llm_factory import LLMFactory
# Import Services and Factories đã Hardening
from domain_models.genai_assistant.configs.config_loader import ConfigLoader
from domain_models.genai_assistant.services.assistant_trainer import AssistantTrainer
from shared_libs.orchestrator.evaluation_orchestrator import EvaluationOrchestrator
from domain_models.genai_assistant.services.tool_service import ToolService
from shared_libs.exceptions import GenAIFactoryError 

# 🚨 CẬP NHẬT: Import các Adapter MLflow (Composition Root)
from shared_libs.mlops.mlflow.mlflow_tracker import MLflowTracker 
from shared_libs.mlops.mlflow.mlflow_registry import MLflowRegistry 

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FINETUNE_JOB_RUNNER")

def parse_args() -> Dict[str, Any]:
    """Parses command line arguments for the training job."""
    parser = argparse.ArgumentParser(description="Runs the GenAI Assistant Fine-Tuning Job.")
    parser.add_argument("--config-path", type=str, default="configs/mlops/trainer_config.yaml", help="Path to the Trainer YAML configuration file.")
    parser.add_argument("--model-version-tag", type=str, default="latest", help="Tag for the new model version in MLflow.")
    return vars(parser.parse_args())

def main():
    args = parse_args()
    
    try:
        # 1. Tải và xác thực cấu hình 
        config_loader = ConfigLoader()
        trainer_config_data = config_loader.load_yaml(args['config_path'])
        trainer_conf = trainer_config_data['MLOPS_CONFIG']
        
        # 2. Khởi tạo Dependencies dựa trên Cấu hình
        mlflow_uri = trainer_conf.get("mlflow_tracking_uri")
        dataset_path = trainer_conf['finetuning_params']['dataset_uri']
        model_name = trainer_conf['finetuning_params']['base_model_name']
        experiment_name = trainer_conf.get("mlflow_experiment_name", "genai_finetuning")

        # 🚨 CẬP NHẬT: Khởi tạo MLflow Adapters
        mlflow_tracker = MLflowTracker(tracking_uri=mlflow_uri, experiment_name=experiment_name)
        mlflow_registry = MLflowRegistry(tracking_uri=mlflow_uri)

        # Khởi tạo Evaluation Orchestrator 
        eval_orchestrator = EvaluationOrchestrator(
            config_loader.get_evaluator_config(), 
            LLMFactory.create_llm(config_loader.get_llm_config('evaluation_llm'))
        )
        
        # Khởi tạo Tool Service 
        tool_service_config = config_loader.load_yaml('configs/shared/tool_config.yaml')
        tool_service = ToolService(tool_service_config['TOOL_REGISTRY'])

        # 3. Khởi tạo và chạy Trainer Service (INJECT DEPENDENCIES)
        trainer = AssistantTrainer(
            config=trainer_conf,
            # 🚨 CẬP NHẬT: Sử dụng DI cho Tracker và Registry
            tracker=mlflow_tracker,
            registry=mlflow_registry,
            eval_orchestrator=eval_orchestrator,
            tool_service=tool_service
        )

        logger.info(f"Starting Fine-Tuning job for base model: {model_name}")
        
        trainer.run_training_job(
            dataset_path=dataset_path, 
            model_name=model_name,
            fine_tuning_params=trainer_conf['finetuning_params'],
            model_version_tag=args['model_version_tag'] # Thêm tag
        )
        
        logger.info("MLOps Finetune Job completed successfully and traceable via MLflow.")

    except GenAIFactoryError as e:
        logger.critical(f"MLOps Job failed due to Factory error: {e}", exc_info=True)
        sys.exit(1) 
    except Exception as e:
        logger.critical(f"Unhandled system failure during Fine-Tuning: {e}", exc_info=True)
        sys.exit(1) 

if __name__ == "__main__":
    main()