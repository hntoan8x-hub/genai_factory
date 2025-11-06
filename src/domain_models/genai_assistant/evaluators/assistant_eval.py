# domain_models/genai_assistant/evaluators/assistant_eval.py

import logging
from typing import Dict, Any, List
import asyncio
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.base.base_llm import BaseLLM
from shared_libs.atomic.evaluators.coherence_eval import CoherenceEvaluator # Giả định CoherenceEvaluator vẫn được dùng
from shared_libs.utils.eval_utils import calculate_bleu, calculate_rouge # Giả định các hàm này đã được định nghĩa
from shared_libs.utils.exceptions import GenAIFactoryError, LLMAPIError

# Import Schemas đã được Hardening
from domain_models.genai_assistant.schemas.eval_schema import EvaluationResult 
from domain_models.genai_assistant.schemas.config_schemas import LLMConfigSchema # Dùng để cấu hình LLM Judge

logger = logging.getLogger(__name__)

# Note: Chuyển các hàm tính score truyền thống vào utilities hoặc giữ nguyên
def calculate_bleu_score(reference: str, candidate: str) -> float:
    """Calculates a mock BLEU score for demonstration purposes."""
    return calculate_bleu(reference, candidate) 

def calculate_rouge_score(reference: str, candidate: str) -> float:
    """Calculates a mock ROUGE score for demonstration purposes."""
    return calculate_rouge(reference, candidate)

class AssistantEvaluator:
    """
    Evaluates the quality of assistant responses using traditional metrics and 
    LLM-as-a-Judge, returning results in a structured format (EvaluationResult Schema).
    """
    
    def __init__(self, llm_judge_config: LLMConfigSchema, coherence_threshold: float = 0.8):
        """
        Initializes the AssistantEvaluator with a validated LLM Judge configuration.
        
        Args:
            llm_judge_config (LLMConfigSchema): Cấu hình đã được xác thực cho LLM Judge.
            coherence_threshold (float): Ngưỡng chất lượng tối thiểu cho LLM-as-a-Judge.
        """
        self.llm_judge_config = llm_judge_config
        self.coherence_threshold = coherence_threshold
        
        # 1. Khởi tạo LLM Judge (dùng LLMFactory để đảm bảo resilience)
        self.llm_judge: BaseLLM = LLMFactory.build(self.llm_judge_config.dict())
        self.coherence_evaluator = CoherenceEvaluator(llm_instance=self.llm_judge) # Truyền LLM Judge vào Evaluator


    async def async_evaluate_response(self, input_text: str, output_text: str, reference_text: str) -> List[EvaluationResult]:
        """
        Runs a suite of evaluations asynchronously on a generated response, 
        enforcing EvaluationResult schema for all metrics. (HARDENING)

        Args:
            input_text (str): The original user query.
            output_text (str): The assistant's generated response.
            reference_text (str): A golden reference response for comparison.

        Returns:
            List[EvaluationResult]: A list of structured evaluation scores.
        """
        results: List[EvaluationResult] = []

        # --- 1. Traditional Metrics (Synchronous/Quick) ---
        bleu_score = calculate_bleu_score(reference_text, output_text)
        rouge_score = calculate_rouge_score(reference_text, output_text)
        
        results.append(EvaluationResult(
            evaluator="NgramMatch", metric_name="BLEU", score=bleu_score, is_pass=bleu_score > 0.3 # Giả định ngưỡng
        ))
        results.append(EvaluationResult(
            evaluator="NgramMatch", metric_name="ROUGE", score=rouge_score, is_pass=rouge_score > 0.4 # Giả định ngưỡng
        ))

        # --- 2. LLM-as-a-Judge (Asynchronous/Tốn thời gian) ---
        try:
            # CoherenceEvaluator sẽ gọi self.llm_judge.async_generate bên trong
            llm_judge_result: Dict[str, Any] = await self.coherence_evaluator.async_evaluate(
                input_data=input_text, 
                output=output_text
            )
            
            coherence_score = llm_judge_result.get("score", 0.0)
            
            # Thêm kết quả LLM Judge vào danh sách kết quả
            results.append(EvaluationResult(
                evaluator="CoherenceJudge", 
                metric_name="CoherenceScore", 
                score=coherence_score, 
                is_pass=coherence_score >= self.coherence_threshold, # Dùng ngưỡng từ config
                reasoning_llm=llm_judge_result.get("details")
            ))
            
        except LLMAPIError as e:
            logger.error(f"LLM Judge API failed: {e}. Skipping coherence evaluation.")
            # Hardening: Nếu đánh giá Judge thất bại, ghi nhận score 0 và thêm cảnh báo
            results.append(EvaluationResult(
                evaluator="CoherenceJudge", 
                metric_name="CoherenceScore", 
                score=0.0, 
                is_pass=False,
                details={"error": "LLM Judge API failure"}
            ))
        except Exception as e:
            logger.error(f"Coherence Evaluation failed: {e}")
            raise GenAIFactoryError(f"Assistant evaluation failed: {e}")

        return results