# src/shared_libs/orchestrator/evaluation_orchestrator.py (HARDENED VERSION)

from typing import Any, Dict, List
import asyncio
from shared_libs.base.base_evaluator import BaseEvaluator
from shared_libs.utils.exceptions import GenAIFactoryError
from shared_libs.factory.evaluator_factory import EvaluatorFactory # Cần thiết cho các job Trainer

class EvaluationOrchestrator:
    """
    A dedicated asynchronous orchestrator for running a suite of evaluations on a model's output.
    Used for both real-time inference checks and MLOps training quality gates.
    """

    def __init__(self, evaluators: List[BaseEvaluator]):
        self.evaluators = evaluators

    async def async_evaluate_output(self, input_data: str, output: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs all configured evaluators on a given output and aggregates the results asynchronously. (HARDENING)
        """
        if context is None:
            context = {}

        results = {}
        tasks = []
        
        for evaluator in self.evaluators:
            tasks.append(evaluator.async_evaluate(input_data=input_data, output=output, context=context))
        
        # HARDENING: Chạy song song các Evaluator
        eval_results_list = await asyncio.gather(*tasks, return_exceptions=True) 

        for evaluator, result in zip(self.evaluators, eval_results_list):
            eval_name = evaluator.__class__.__name__
            if isinstance(result, Exception):
                results[eval_name] = {"error": f"Evaluation failed: {result}"}
            else:
                results[eval_name] = result
        
        return results
        
    # Giữ lại phương thức đồng bộ cho các môi trường Job/Testing đồng bộ nếu cần
    def evaluate_output(self, input_data: str, output: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementation should ideally run: asyncio.run(self.async_evaluate_output(...))
        raise NotImplementedError("Use async_evaluate_output for production environment.")