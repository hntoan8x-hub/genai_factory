# shared_libs/atomic/prompts/rag_prompt.py

from typing import Any, Dict, List
from shared_libs.base.base_prompt import BasePrompt
from typing import Any as TokenizerType 

class RAGPrompt(BasePrompt):
    """
    A prompt template for Retrieval-Augmented Generation (RAG).

    This template is designed to incorporate retrieved documents or information
    from an external knowledge base to help the language model generate a
    more accurate and grounded response.
    """

    def __init__(self, instruction: str):
        """
        Initializes the RAG prompt with a main instruction.

        Args:
            instruction (str): The main instruction for the LLM. It should explain the
                               task and how to use the provided context.
        """
        self.instruction = instruction

    def render(self, context: Dict[str, Any]) -> str:
        """
        Renders the final RAG prompt.

        Args:
            context (Dict[str, Any]): A dictionary containing 'query' and a list of
                                     'retrieved_docs', where each doc is a string.

        Returns:
            str: The fully-formatted RAG prompt.
        """
        if not self.validate(context):
            raise ValueError("Context is missing one or more required keys: 'query', 'retrieved_docs'.")

        retrieved_docs_str = "\n\n".join(
            [f"Document {i+1}:\n{doc}" for i, doc in enumerate(context['retrieved_docs'])]
        )

        prompt_parts = [
            self.instruction,
            "---",
            "Retrieved Documents:",
            retrieved_docs_str,
            "---",
            f"Question: {context['query']}",
            "Answer:"
        ]

        return "\n".join(prompt_parts)

    def validate(self, context: Dict[str, Any]) -> bool:
        """
        Validates the context to ensure it contains the 'query' and 'retrieved_docs' keys.

        Args:
            context (Dict[str, Any]): The context to validate.

        Returns:
            bool: True if the context is valid, False otherwise.
        """
        return 'query' in context and 'retrieved_docs' in context and isinstance(context['retrieved_docs'], list)


    def estimate_tokens(self, context: Dict[str, Any], tokenizer: TokenizerType) -> int:
        """
        Estimates the number of input tokens the rendered RAG prompt will consume. (HARDENING ADDITION)

        Note: RAG cost is dominated by the 'retrieved_docs'.
        """
        if not self.validate(context):
            return 0
            
        rendered_prompt = self.render(context)
        
        # Encode and count tokens
        return len(tokenizer.encode(rendered_prompt))
