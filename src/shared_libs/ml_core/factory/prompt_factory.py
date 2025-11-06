# shared_libs/factory/prompt_factory.py (FINAL HARDENED VERSION)

from typing import Dict, Any, Union, Type
from shared_libs.base.base_prompt import BasePrompt
from shared_libs.atomic.prompts.fewshot_prompt import FewShotPrompt
from shared_libs.atomic.prompts.react_prompt import ReActPrompt
from shared_libs.atomic.prompts.rag_prompt import RAGPrompt
from shared_libs.configs.schemas import PromptBaseConfig, RAGPromptConfig # HARDENING: Import Schemas

# Định nghĩa Union cho các loại Prompt Config Models được chấp nhận
PromptConfigModel = Union[PromptBaseConfig, RAGPromptConfig]

class PromptFactory:
    """
    A factory class for creating Prompt instances from validated configuration schemas. (HARDENING)
    """

    def __init__(self):
        self._prompt_types: Dict[str, Type[BasePrompt]] = {
            "fewshot": FewShotPrompt,
            "react": ReActPrompt,
            "rag": RAGPrompt,
        }

    def build(self, config_model: PromptConfigModel) -> BasePrompt:
        """
        Builds a Prompt instance from a validated Pydantic configuration model.
        """
        prompt_type = config_model.type
        if not prompt_type or prompt_type not in self._prompt_types:
            raise ValueError(f"Unsupported Prompt type: {prompt_type}.")
        
        prompt_class = self._prompt_types[prompt_type]
        
        # Truyền các tham số (template, variables) từ model đã được validate để khởi tạo Prompt
        return prompt_class(**config_model.model_dump())