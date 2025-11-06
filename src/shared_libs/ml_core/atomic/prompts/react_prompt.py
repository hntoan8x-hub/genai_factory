# shared_libs/atomic/prompts/react_prompt.py

from typing import Any, Dict, List
from shared_libs.genai.base.base_prompt import BasePrompt
from typing import Any as TokenizerType

class ReActPrompt(BasePrompt):
    """
    A prompt template for the ReAct (Reasoning and Acting) pattern.

    This template guides the LLM to follow a structured loop of 'Thought',
    'Action', and 'Observation' to solve complex tasks using tools.
    """

    DEFAULT_TEMPLATE = """
You are an intelligent agent that can reason and act.
You have access to the following tools:
{tools_string}

To accomplish your task, you should think step-by-step and decide on an action.
Your response format must follow this sequence:

Thought: You should always think about what to do.
Action: the action to take, should be one of [{tool_names}].
Action Input: the input to the action.
Observation: the result of the action.
... (this Thought/Action/Action Input/Observation cycle can repeat)

When you have found the final answer, respond with the following format:
Thought: I have a plan to find the final answer.
Final Answer: the final answer to the original question.

Begin!

Question: {question}
{agent_history}
Thought:
"""

    def __init__(self, template: str = DEFAULT_TEMPLATE):
        """
        Initializes the ReAct prompt with a template.

        Args:
            template (str): The string template for the ReAct prompt.
        """
        self.template = template

    def render(self, context: Dict[str, Any]) -> str:
        """
        Renders the final ReAct prompt using the provided context.

        Args:
            context (Dict[str, Any]): A dictionary containing 'question', 'tools_string',
                                     'tool_names', and 'agent_history'.

        Returns:
            str: The fully-formatted ReAct prompt.
        """
        if not self.validate(context):
            raise ValueError("Context is missing one or more required keys: 'question', 'tools_string', 'tool_names', 'agent_history'.")

        return self.template.format(**context).strip()

    def validate(self, context: Dict[str, Any]) -> bool:
        """
        Validates the context to ensure it contains all required keys for the template.

        Args:
            context (Dict[str, Any]): The context to validate.

        Returns:
            bool: True if the context is valid, False otherwise.
        """
        required_keys = ['question', 'tools_string', 'tool_names', 'agent_history']
        return all(key in context for key in required_keys)

    def estimate_tokens(self, context: Dict[str, Any], tokenizer: TokenizerType) -> int:
        """
        Estimates the number of input tokens the rendered ReAct prompt will consume. (HARDENING ADDITION)
        
        Note: The prompt contains the full agent history, which drives the cost.
        """
        if not self.validate(context):
            return 0
            
        rendered_prompt = self.render(context)
        
        # Encode and count tokens
        return len(tokenizer.encode(rendered_prompt))