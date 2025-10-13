import os
from typing import Any, Dict, List, Optional, Union

from anthropic import Anthropic, APIStatusError, APITimeoutError

from shared_libs.genai.base.base_llm import BaseLLM

class AnthropicLLM(BaseLLM):
    """
    A wrapper class for the Anthropic API, implementing the BaseLLM interface.
    This class uses models like Claude 3 for text generation and chat.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Initializes the Anthropic client.

        Args:
            model_name (str): The name of the Anthropic model to use (e.g., "claude-3-haiku-20240307").
            api_key (Optional[str]): The API key for authentication. If not provided,
                                     it will be read from the ANTHROPIC_API_KEY environment variable.
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key must be provided or set in environment variable ANTHROPIC_API_KEY.")

        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name

    def generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """
        Generates text from a given prompt using the Anthropic API.
        This method formats a simple string prompt into a chat-compatible message
        and calls the chat method.

        Args:
            prompt (Union[str, List[Dict[str, Any]]]): The input prompt.
            **kwargs: Additional parameters for the API call.

        Returns:
            str: The generated text.
        """
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        return self.chat(messages, **kwargs)

    def embed(self, text: str) -> List[float]:
        """
        Anthropic does not have a native embedding endpoint. This method is not
        implemented and will raise an error.
        
        Args:
            text (str): The text to embed.
            
        Raises:
            NotImplementedError: As Anthropic API does not support this functionality.
        """
        raise NotImplementedError("The Anthropic API does not provide a native embedding endpoint.")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Performs a multi-turn chat conversation using the Anthropic API.

        Args:
            messages (List[Dict[str, str]]): A list of messages in the conversation history.
            **kwargs: Additional parameters for the API call.

        Returns:
            str: The model's response.
        """
        response = self.client.messages.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        return response.content[0].text
