import re
from typing import Any, Dict, List
from shared_libs.base.base_prompt import BasePrompt
from typing import Any as TokenizerType 


class FewShotPrompt(BasePrompt):
    """
    A prompt template that incorporates a few-shot learning pattern.

    This template structures a prompt by providing a set of example
    input-output pairs to guide the language model's response for a new input.
    """

    def __init__(self, instruction: str, examples: List[Dict[str, str]], example_format: str = "Input: {input}\nOutput: {output}"):
        """
        Initializes the few-shot prompt with instructions and examples.

        Args:
            instruction (str): The main instruction for the LLM.
            examples (List[Dict[str, str]]): A list of example dictionaries, where each
                                             dictionary must contain 'input' and 'output' keys.
            example_format (str): A string template for rendering each example.
                                  Defaults to "Input: {input}\nOutput: {output}".
        """
        self.instruction = instruction
        self.examples = examples
        self.example_format = example_format
        
        # Validate that the example format matches the keys in the examples
        required_keys = re.findall(r'\{(\w+)\}', self.example_format)
        for example in self.examples:
            if not all(key in example for key in required_keys):
                raise ValueError(f"All examples must contain keys matching the format string: {required_keys}")

    def render(self, context: Dict[str, Any]) -> str:
        """
        Renders the final prompt by combining the instruction, examples, and new input.

        Args:
            context (Dict[str, Any]): A dictionary containing the new 'input' for the prompt.

        Returns:
            str: The fully-formatted few-shot prompt.
        """
        if not self.validate(context):
            raise ValueError("Context is missing the required 'input' key.")
        
        rendered_examples = "\n\n".join(
            [self.example_format.format(**ex) for ex in self.examples]
        )
        
        prompt_parts = [
            self.instruction,
            "---",
            rendered_examples,
            "---",
            self.example_format.split("{output}")[0].format(input=context['input'])
        ]
        
        return "\n".join(prompt_parts)

    def validate(self, context: Dict[str, Any]) -> bool:
        """
        Validates the context to ensure it contains the necessary 'input' key.

        Args:
            context (Dict[str, Any]): The context to validate.

        Returns:
            bool: True if the context is valid, False otherwise.
        """
        return 'input' in context

    def estimate_tokens(self, context: Dict[str, Any], tokenizer: TokenizerType) -> int:
        """
        Estimates the number of input tokens the rendered prompt will consume. (HARDENING ADDITION)

        Args:
            context (Dict[str, Any]): The context variables for the prompt ('input').
            tokenizer (TokenizerType): A tokenizer instance (e.g., Tiktoken).

        Returns:
            int: The estimated token count.
        """
        if not self.validate(context):
            return 0 # Cannot estimate if context is invalid
            
        # 1. Render the full prompt string
        rendered_prompt = self.render(context)
        
        # 2. Encode and count tokens
        # Assuming the tokenizer object has an encode method that returns a list of token IDs
        return len(tokenizer.encode(rendered_prompt))
