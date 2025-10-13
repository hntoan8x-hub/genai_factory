from typing import Any, Dict, List
from shared_libs.base.base_evaluator import BaseEvaluator
from shared_libs.factory.evaluator_factory import EvaluatorFactory

class EvaluationOrchestrator:
    """
    A dedicated orchestrator for running a suite of evaluations on a model's output.

    This class provides a clean, centralized interface for judging a GenAI output
    using multiple evaluators and aggregating the results.
    """

    def __init__(self, evaluators: List[BaseEvaluator]):
        """
        Initializes the Evaluation Orchestrator.

        Args:
            evaluators (List[BaseEvaluator]): A list of evaluator instances.
        """
        self.evaluators = evaluators

    def evaluate_output(self, input_data: str, output: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs all configured evaluators on a given output and aggregates the results.

        Args:
            input_data (str): The original input or query.
            output (str): The output to be evaluated.
            context (Dict[str, Any], optional): A dictionary of contextual information
                                                (e.g., ground truth) for evaluation.

        Returns:
            Dict[str, Any]: A dictionary where keys are evaluator names and values are
                            their respective results.
        """
        if context is None:
            context = {}

        results = {}
        print("Starting evaluation orchestration...")
        for evaluator in self.evaluators:
            eval_name = evaluator.__class__.__name__
            try:
                eval_result = evaluator.evaluate(
                    input_data=input_data,
                    output=output,
                    context=context
                )
                results[eval_name] = eval_result
            except Exception as e:
                print(f"Error running evaluator '{eval_name}': {e}")
                results[eval_name] = {"error": str(e)}
        
        print("Evaluation orchestration complete.")
        return results
