# GenAI_Factory/src/domain_models/genai_assistant/pipelines/3_internal_utility/training_pipeline.py

import logging
from typing import Dict, Any, List
import asyncio
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.base.base_llm import BaseLLM
from shared_libs.utils.eval_utils import llm_as_a_judge, calculate_bleu # Giả định các hàm này có thể nhận BaseLLM
from shared_libs.utils.exceptions import GenAIFactoryError
from domain_models.genai_assistant.schemas.config_schemas import LLMConfigSchema # Schema LLM
from domain_models.genai_assistant.schemas.eval_schema import EvaluationResult # Schema Metric chuẩn
from domain_models.genai_assistant.logging.mlflow_adapter import MLflowAdapter # Adapter MLOps

logger = logging.getLogger(__name__)

class TrainingPipeline:
    """
    Manages the model fine-tuning and evaluation loop, designed to run as a 
    traceable MLOps job. Ensures evaluation components use Hardened LLM configuration.
    """

    def __init__(self, config: Dict[str, Any], eval_llm_config: LLMConfigSchema, mlflow_adapter: MLflowAdapter):
        """
        Initializes the TrainingPipeline with validated configuration and MLOps tools.
        
        Args:
            config: General training configuration (e.g., hyperparameters).
            eval_llm_config: Validated configuration for the LLM Judge.
            mlflow_adapter: MLflowAdapter instance for tracking.
        """
        self.config = config
        self.mlflow_adapter = mlflow_adapter
        
        # 1. Build LLM for evaluation (LLM-as-a-Judge), sử dụng config đã được Schema xác thực
        self.eval_llm: BaseLLM = LLMFactory.build(eval_llm_config.dict()) 
        
        # Giả định một mô hình để huấn luyện (sẽ được khởi tạo trong run_job)
        self.model_to_train = None 
        self.quality_threshold = config.get("quality_threshold", 0.75)


    async def _async_run_evaluation(self, dataset: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Runs the evaluation loop asynchronously and returns structured metrics."""
        
        results: List[EvaluationResult] = []
        
        # Tạo danh sách các task đánh giá bất đồng bộ
        evaluation_tasks = []
        for item in dataset:
            # Mô phỏng quá trình tạo sinh đầu ra từ mô hình vừa huấn luyện
            simulated_output = self._simulate_generation(item.get("input", ""))
            
            # 1. Đánh giá BLEU Score (có thể là đồng bộ)
            bleu_score = calculate_bleu(item.get("reference_output", ""), simulated_output)
            results.append(EvaluationResult(
                evaluator="TraditionalEval", metric_name="BLEU", score=bleu_score, is_pass=bleu_score > 0.5
            ))
            
            # 2. LLM-as-a-Judge (Bất đồng bộ)
            evaluation_tasks.append(
                llm_as_a_judge(
                    llm=self.eval_llm, 
                    prompt=None, 
                    output=simulated_output, 
                    context=item
                )
            )

        # Chạy tất cả các task LLM-as-a-Judge đồng thời
        judge_results = await asyncio.gather(*evaluation_tasks)
        
        # Chuẩn hóa kết quả Judge thành EvaluationResult Schema
        for result in judge_results:
             results.append(EvaluationResult(
                evaluator="LLM-as-a-Judge", 
                metric_name="CoherenceScore", 
                score=result.get("score", 0.0), 
                is_pass=result.get("score", 0.0) >= 0.8,
                reasoning_llm=result.get("details")
            ))
            
        return results


    def run_training_job(self, dataset_path: str, model_name: str, fine_tuning_params: Dict[str, Any]) -> str:
        """
        Runs the E2E Fine-Tuning and Evaluation cycle, logging results to MLflow.
        """
        run_name = f"finetune-{model_name}-{dataset_path.split('/')[-1]}"
        logger.info(f"Starting traceable training job: {run_name}.")
        
        output_model_path = ""
        
        try:
            # 1. MLflow Tracking Start (HARDENING: Context Manager đảm bảo run kết thúc)
            with self.mlflow_adapter.start_run(run_name=run_name) as run:
                
                # Log parameters
                self.mlflow_adapter.log_param("model_name", model_name)
                self.mlflow_adapter.log_param("dataset_path", dataset_path)
                self.mlflow_adapter.log_metrics({"initial_lr": fine_tuning_params.get("learning_rate", 1e-5)})
                
                # --- 2. Model Fine-Tuning (Placeholder) ---
                logger.info("Finetuning process started...")
                # self._fine_tune_model_api_call(...) 
                output_model_path = f"/tmp/models/ft_{run.info.run_id}.bin" # Liên kết model path với Run ID
                
                # --- 3. Evaluation (CRITICAL QUALITY CHECK) ---
                logger.info("Starting post-training evaluation...")
                test_data = [{"input": "q1", "reference_output": "a1"}, {"input": "q2", "reference_output": "a2"}] # Giả định dữ liệu
                
                # Chạy đánh giá bất đồng bộ
                evaluation_results_schemas = asyncio.run(self._async_run_evaluation(test_data))
                
                # Tính tổng hợp metrics
                total_bleu = sum(res.score for res in evaluation_results_schemas if res.metric_name == "BLEU")
                avg_bleu = total_bleu / (len(test_data) or 1)
                
                # 4. Log Metrics and Artifacts
                self.mlflow_adapter.log_metrics({"avg_bleu_score": avg_bleu, "total_eval_count": len(test_data)})
                self.mlflow_adapter.log_artifact(output_model_path, "model") 
                
                # 5. Deployment Decision Logic (HARDENING: Quality Gate)
                if avg_bleu < self.quality_threshold:
                     logger.critical(f"Model failed quality gate. Avg BLEU Score ({avg_bleu:.4f}) < Threshold ({self.quality_threshold}).")
                     # Không gọi end_run(FINISHED) - để mặc định context manager kết thúc với FAILED
                     raise GenAIFactoryError("Model failed the mandatory quality threshold.")
                
                logger.info("Model passed quality gate and is ready for promotion.")
                return output_model_path

        except Exception as e:
            logger.critical(f"FATAL Training Job failure: {e.__class__.__name__}: {e}")
            raise GenAIFactoryError(f"Trainer failed during MLOps cycle: {e}") from e


    def _simulate_generation(self, input_text: str) -> str:
        """Simulates a model's generation process for demonstration."""
        return f"Simulated response to '{input_text}'"