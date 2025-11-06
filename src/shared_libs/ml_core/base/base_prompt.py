# shared_libs/base/base_prompt.py

from abc import ABC, abstractmethod
from typing import Any, Dict

class BasePrompt(ABC):
    """
    Interface for prompt templates.
    Each template can be rendered with a specific context.
    Enforces token estimation for cost control and monitoring. (HARDENING)
    """

    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        """
        Renders the prompt template into a completed text string.
        """
        pass

    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> bool:
        """
        Checks the validity of the context for the prompt template.
        """
        pass

    # --- Cost Control Method (HARDENING ADDITION) ---
    @abstractmethod
    def estimate_tokens(self, context: Dict[str, Any], tokenizer: Any) -> int:
        """
        Estimates the number of input tokens the rendered prompt will consume.

        Args:
            context: The context variables for the prompt.
            tokenizer: A specific tokenizer instance (e.g., Tiktoken) required for accurate estimation.

        Returns:
            The estimated token count.
        """
        pass