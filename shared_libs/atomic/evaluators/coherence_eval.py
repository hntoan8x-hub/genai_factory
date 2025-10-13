# shared_libs/atomic/evaluators/coherence_eval.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
from shared_libs.base.base_evaluator import BaseEvaluator

class CoherenceEval(BaseEvaluator):
    """
    Evaluator to check the logical flow and consistency of an LLM's output.
    """
    
    # Sử dụng executor để offload tác vụ đồng bộ
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)

    def evaluate(self, input_data: str, output: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronously evaluates the output for coherence (simplified heuristic)."""
        input_len = len(input_data.split())
        output_len = len(output.split())
        
        plausible_starts = ["the answer is", "it seems that", "based on the information"]
        is_plausible_start = any(output.lower().startswith(p) for p in plausible_starts)

        if output_len < input_len * 0.1 or not is_plausible_start:
            score = 0.3
            reason = "Response is too short or lacks a clear starting point, suggesting low coherence."
        else:
            score = 0.8
            reason = "Response is logically structured and proportional to the input."
        
        return {"score": score, "reason": reason}

    async def async_evaluate(self, input_data: str, output: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Asynchronously evaluates the output for coherence. (HARDENING ADDITION)"""
        loop = asyncio.get_event_loop()
        # Chạy phương thức đồng bộ 'evaluate' trong thread riêng
        return await loop.run_in_executor(
            self.executor,
            self.evaluate,
            input_data,
            output,
            context
        )