# shared_libs/factory/evaluator_factory.py (FINAL HARDENED VERSION)

from typing import Dict, Any, Union, Type
from shared_libs.base.base_evaluator import BaseEvaluator
from shared_libs.atomic.evaluators.hallucination_eval import HallucinationEval
from shared_libs.atomic.evaluators.safety_eval import SafetyEval
from shared_libs.atomic.evaluators.coherence_eval import CoherenceEval
from shared_libs.configs.schemas import EvaluatorEntry # HARDENING: Import Schema

class EvaluatorFactory:
    """
    A factory class for creating Evaluator instances from validated configuration schemas. (HARDENING)
    """

    def __init__(self):
        self._evaluator_types: Dict[str, Type[BaseEvaluator]] = {
            "hallucination": HallucinationEval,
            "safety": SafetyEval,
            "coherence": CoherenceEval,
        }

    def build(self, config_model: EvaluatorEntry) -> BaseEvaluator:
        """
        Builds an Evaluator instance from a single validated Pydantic EvaluatorEntry model.
        
        Args:
            config_model (EvaluatorEntry): The validated Pydantic model for a single evaluator entry.
        """
        evaluator_type = config_model.type
        if not evaluator_type or evaluator_type not in self._evaluator_types:
            raise ValueError(f"Unsupported Evaluator type: {evaluator_type}.")
        
        evaluator_class = self._evaluator_types[evaluator_type]
        
        # Truyền toàn bộ dữ liệu (bao gồm 'context' cho HallucinationEval)
        return evaluator_class(**config_model.model_dump())