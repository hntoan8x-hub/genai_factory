# shared_libs/atomic/evaluators/hallucination_eval.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict
from shared_libs.base.base_evaluator import BaseEvaluator

class HallucinationEval(BaseEvaluator):
    """
    Evaluator to detect if an LLM's output contains factual inconsistencies or information not
    present in the provided context.
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)

    def evaluate(self, input_data: str, output: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously evaluates the output for hallucination (simplified check)."""
        if 'ground_truth' not in context or not isinstance(context['ground_truth'], str):
            return {
                "score": 0.0,
                "reason": "Evaluation failed: Missing 'ground_truth' in context."
            }

        ground_truth = context['ground_truth']

        # Simple check for keyword overlap
        keywords_output = set(output.lower().split())
        keywords_truth = set(ground_truth.lower().split())
        
        # Prevent DivisionByZeroError
        if not keywords_output:
            score = 0.0
        else:
            common_keywords = keywords_output.intersection(keywords_truth)
            score = len(common_keywords) / len(keywords_output)
            
        if score < 0.5:
            final_score = 0.2
            reason = "Potential hallucination detected: Low keyword overlap with ground truth."
        else:
            final_score = 0.9
            reason = "Output appears consistent with ground truth."
        
        return {"score": final_score, "reason": reason}

    async def async_evaluate(self, input_data: str, output: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously evaluates the output for hallucination. (HARDENING ADDITION)"""
        loop = asyncio.get_event_loop()
        # Chạy phương thức đồng bộ 'evaluate' trong thread riêng
        return await loop.run_in_executor(
            self.executor,
            self.evaluate,
            input_data,
            output,
            context
        )