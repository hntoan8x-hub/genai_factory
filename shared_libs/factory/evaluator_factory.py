from typing import Dict, Any, Union
from shared_libs.genai.base.base_evaluator import BaseEvaluator
from shared_libs.genai.atomic.evaluators.hallucination_eval import HallucinationEval
from shared_libs.genai.atomic.evaluators.safety_eval import SafetyEval
from shared_libs.genai.atomic.evaluators.coherence_eval import CoherenceEval

class EvaluatorFactory:
    """
    A factory class for creating Evaluator instances from configuration.
    It centralizes the creation logic for various evaluation types.
    """

    def __init__(self):
        """Initializes the EvaluatorFactory."""
        self._evaluator_types = {
            "hallucination": HallucinationEval,
            "safety": SafetyEval,
            "coherence": CoherenceEval,
        }

    def build(self, config: Dict[str, Any]) -> BaseEvaluator:
        """
        Builds an Evaluator instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): A dictionary containing the evaluator configuration.
                                     Must have a 'type' key.

        Returns:
            BaseEvaluator: An instance of the requested Evaluator type.

        Raises:
            ValueError: If the 'type' in the config is not supported.
        """
        evaluator_type = config.get("type")
        if not evaluator_type or evaluator_type not in self._evaluator_types:
            raise ValueError(f"Unsupported Evaluator type: {evaluator_type}. Supported types are: {list(self._evaluator_types.keys())}")
        
        evaluator_class = self._evaluator_types[evaluator_type]
        return evaluator_class()
