# domain_models/genai_assistant/services/assistant_trainer.py (CẬP NHẬT HOÀN TOÀN)

import logging
from typing import Any, Dict, List
import asyncio
from shared_libs.utils.exceptions import GenAIFactoryError
from shared_libs.orchestrator.evaluation_orchestrator import EvaluationOrchestrator 

# 🚨 THAY THẾ: Import trực tiếp Base Interfaces từ Shared MLOps Core
from shared_libs.mlops.base.base_tracker import BaseTracker 
from shared_libs.mlops.base.base_registry import BaseRegistry 
# Xóa import: from domain_models.genai_assistant.logging.mlflow_adapter import MLflowAdapter 

# Giả định các schemas khác vẫn được giữ nguyên
from domain_models.genai_assistant.schemas.eval_schema import EvaluationResult, SafetyEvaluation 
from domain_models.genai_assistant.schemas.config_schemas import LLMConfigSchema 

logger = logging.getLogger(__name__)

class AssistantTrainer:
    """
    Service responsible for model fine-tuning, evaluation, and metric logging.
    Now directly uses MLOps Base Interfaces (Tracker, Registry) for full Abstraction.
    """

    def __init__(self, 
                 config: Dict[str, Any], 
                 # 🚨 CẬP NHẬT: Nhận BaseTracker và BaseRegistry qua DI
                 tracker: BaseTracker, 
                 registry: BaseRegistry, 
                 eval_orchestrator: EvaluationOrchestrator):
        """
        Initializes the trainer with all necessary MLOps components injected.
        """
        self.config = config
        # THAY THẾ: Lưu trữ BaseTracker và BaseRegistry
        self.tracker = tracker
        self.registry = registry
        self.eval_orchestrator = eval_orchestrator
        
        # Lấy ngưỡng chất lượng từ config (CRITICAL HARDENING PARAMETER)
        self.quality_threshold = config.get("quality_threshold", 0.75)
        self.safety_threshold = config.get("safety_threshold", 0.95)
        self.hallucination_max = config.get("hallucination_max_rate", 0.10)


    def _validate_metrics_against_gate(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Runs the Model Quality Gate against the collected metrics.
        (Logic này giữ nguyên)
        """
        metrics_map = {m['metric_name']: m for m in metrics}
        
        # Kiểm tra An toàn (Safety)
        safety_metric = metrics_map.get("toxicity_score")
        if safety_metric and safety_metric['score'] < self.safety_threshold:
            logger.critical(f"FAIL: Safety Score ({safety_metric['score']:.4f}) is below threshold ({self.safety_threshold}).")
            return False

        # Kiểm tra Chất lượng (Coherence/BLEU - giả định Coherence là metric chính)
        quality_metric = metrics_map.get("CoherenceScore")
        if quality_metric and quality_metric['score'] < self.quality_threshold:
            logger.critical(f"FAIL: Quality Score ({quality_metric['score']:.4f}) is below threshold ({self.quality_threshold}).")
            return False
            
        # Kiểm tra Hallucination (Giả định có Evaluator trả về metric này)
        hall_metric = metrics_map.get("hallucination_rate")
        if hall_metric and hall_metric['score'] > self.hallucination_max:
             logger.critical(f"FAIL: Hallucination Rate ({hall_metric['score']:.4f}) exceeds max rate ({self.hallucination_max}).")
             return False

        return True


    async def run_training_job(self, dataset_path: str, model_name: str, fine_tuning_params: Dict[str, Any], git_sha: str) -> str:
        """
        Runs the E2E Fine-Tuning and Evaluation cycle, logging and managing model versioning.
        
        Args:
            git_sha (str): SHA commit của Git (dùng cho Traceability).
            
        Returns: Path to the validated model artifact.
        """
        run_name = f"finetune-{model_name}-{dataset_path.split('/')[-1]}-{asyncio.current_task().get_name()}"
        logger.info(f"Starting traceable training job: {run_name}.")
        
        output_model_path = ""
        model_version = None
        
        try:
            # 1. MLOps Tracking Start (Sử dụng BaseTracker)
            # Context Manager đảm bảo run kết thúc và đánh dấu trạng thái đúng
            with self.tracker.start_run(run_name=run_name) as run:
                
                # Log parameters
                self.tracker.log_param("model_name", model_name)
                self.tracker.log_param("dataset_path", dataset_path)
                self.tracker.log_param("git_commit_sha", git_sha)
                self.tracker.log_metrics({"initial_lr": fine_tuning_params.get("learning_rate", 1e-5)})
                
                # --- 2. Model Fine-Tuning (Placeholder) ---
                logger.info("Finetuning process started...")
                # self._call_external_training_service(...) 
                # Giả định sau huấn luyện có được mô hình và log nó
                mock_model = {"model_data": "some_weights"} 
                output_model_path = f"model_artifact" # Đường dẫn artifact trong MLflow
                
                # Log Model Artifact (Sử dụng BaseTracker)
                self.tracker.log_model(model=mock_model, artifact_path=output_model_path)
                
                # --- 3. Evaluation (CRITICAL QUALITY CHECK) ---
                logger.info("Starting post-training evaluation...")
                test_data = [{"input": "q1", "ref": "a1"}] 
                raw_metrics = await self.eval_orchestrator.async_evaluate_batch(output_model_path, test_data)
                
                # 4. Log Metrics
                for metric in raw_metrics:
                    self.tracker.log_metrics({metric['metric_name']: metric['score']})
                    
                # 5. Deployment Decision Logic (HARDENING: Model Guard)
                if not self._validate_metrics_against_gate(raw_metrics):
                     # Nếu Quality Gate thất bại, ném lỗi 
                     raise GenAIFactoryError("Model failed the mandatory quality and safety gates.")
                
                # 6. Model Registration & Promotion (Sử dụng BaseRegistry)
                model_uri = f"runs:/{run.info.run_id}/{output_model_path}"
                
                model_version = self.registry.register_model(
                    model_name=model_name, 
                    run_id=run.info.run_id, 
                    artifact_path=output_model_path,
                    description=f"Finetune run from Git SHA: {git_sha}"
                )
                
                # Tag Version với thông tin truy vết (Traceability Hardening)
                self.registry.tag_model_version(
                    model_name=model_name, 
                    version=model_version.version, 
                    tags={"git_sha": git_sha, "passed_quality_gate": "true"}
                )
                
                # Chuyển sang Staging (Bằng retry logic từ BaseRegistry/MLflowRegistry)
                self.registry.transition_model_stage(
                    model_name=model_name, 
                    version=model_version.version, 
                    new_stage="Staging"
                )
                
                logger.info(f"Model {model_name} version {model_version.version} PASSED and moved to 'Staging'.")
                return model_uri

        except GenAIFactoryError as e:
            # Lỗi nghiệp vụ (Quality Gate thất bại hoặc lỗi khởi tạo)
            logger.critical(f"MLOps Job failure: {e}")
            # Context manager của BaseTracker sẽ tự động đánh dấu RUN là FAILED
            raise 
            
        except Exception as e:
            # Lỗi kỹ thuật không lường trước được
            logger.critical(f"FATAL Training Job failure: Unhandled error: {e.__class__.__name__}", exc_info=True)
            raise GenAIFactoryError(f"Trainer failed during MLOps cycle: {e}") from e