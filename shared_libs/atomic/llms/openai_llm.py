# shared_libs/atomic/llms/openai_llm.py

import os
from typing import Any, Dict, List, Optional, Union
import openai
from openai import AsyncOpenAI
from openai import APIStatusError, RateLimitError, APIError

# Import the resilient base wrapper and exceptions
from .base_llm_wrapper import BaseLLMWrapper, RETRY_STRATEGY 
from shared_libs.exceptions import LLMRateLimitError, LLMServiceError, LLMAPIError

class OpenAILLM(BaseLLMWrapper):
    """
    A wrapper class for the OpenAI API, implementing the BaseLLM interface 
    with built-in Resilience (Retry/Fallback).
    """

    def __init__(self, config: Dict[str, Any], is_fallback: bool = False):
        # config should contain 'model_name' and optionally 'api_key'
        super().__init__(config, is_fallback)
        
        model_name = config.get("model_name")
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key must be provided or set in environment variable OPENAI_API_KEY.")
        
        # Use AsyncOpenAI client for production readiness
        self.client = AsyncOpenAI(api_key=api_key) 
        self.model_name = model_name

    # --- Resilience Implementation (Core Logic) ---

    async def _protected_async_call(self, method_name: str, *args, **kwargs) -> Any:
        """
        Implements the actual asynchronous OpenAI API call logic 
        and maps OpenAI exceptions to the custom exceptions for resilience handling.
        """
        try:
            if method_name == 'generate':
                prompt = kwargs.pop('prompt')
                if isinstance(prompt, str):
                    messages = [{"role": "user", "content": prompt}]
                else:
                    messages = prompt
                
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **kwargs
                )
                return response.choices[0].message.content
            
            elif method_name == 'chat':
                messages = kwargs.pop('messages')
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **kwargs
                )
                return response.choices[0].message.content

            elif method_name == 'embed':
                text = kwargs.pop('text')
                embedding_model = "text-embedding-3-small"
                response = await self.client.embeddings.create(
                    model=embedding_model,
                    input=text
                )
                return response.data[0].embedding
            
            else:
                raise NotImplementedError(f"Method {method_name} not implemented for OpenAI.")

        except RateLimitError as e:
            # 429 errors should trigger a retry
            raise LLMRateLimitError(f"OpenAI Rate Limit Error: {e}") 
        except APIStatusError as e:
            # 5xx errors should trigger a retry (transient service errors)
            if 500 <= e.status_code < 600:
                raise LLMServiceError(f"OpenAI Service Error ({e.status_code}): {e}")
            # Other status errors (4xx) are generally fatal/not retryable, fail and trigger fallback
            raise LLMAPIError(f"OpenAI Client/API Error ({e.status_code}): {e}")
        except APIError as e:
            # Catch other general API errors
            raise LLMAPIError(f"OpenAI General API Error: {e}")