from typing import Dict, Any, Union
from shared_libs.genai.base.base_prompt import BasePrompt
from shared_libs.genai.atomic.prompts.fewshot_prompt import FewShotPrompt
from shared_libs.genai.atomic.prompts.react_prompt import ReActPrompt
from shared_libs.genai.atomic.prompts.rag_prompt import RAGPrompt

class PromptFactory:
    """
    A factory class for creating Prompt instances from configuration.
    It provides a centralized way to build different prompt templates.
    """

    def __init__(self):
        """Initializes the PromptFactory."""
        self._prompt_types = {
            "fewshot": FewShotPrompt,
            "react": ReActPrompt,
            "rag": RAGPrompt,
        }

    def build(self, config: Dict[str, Any]) -> BasePrompt:
        """
        Builds a Prompt instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): A dictionary containing the prompt configuration.
                                     Must have a 'type' key.

        Returns:
            BasePrompt: An instance of the requested Prompt type.

        Raises:
            ValueError: If the 'type' in the config is not supported.
        """
        prompt_type = config.get("type")
        if not prompt_type or prompt_type not in self._prompt_types:
            raise ValueError(f"Unsupported Prompt type: {prompt_type}. Supported types are: {list(self._prompt_types.keys())}")
        
        prompt_class = self._prompt_types[prompt_type]
        # In a real scenario, this would pass template strings from the config
        return prompt_class()
