# shared_libs/base/base_evaluator.py

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseEvaluator(ABC):
    """
    Interface for evaluation tools.
    These tools assess the output of an LLM or agent.
    Enforces asynchronous execution for performance in evaluation pipelines. (HARDENING)
    """

    @abstractmethod
    def evaluate(self, input_data: Any, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronously evaluates a specific output.
        """
        pass
    
    @abstractmethod
    async def async_evaluate(self, input_data: Any, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously evaluates a specific output. 
        This is the preferred method for use in high-throughput evaluation orchestrators. (HARDENING ADDITION)
        """
        pass