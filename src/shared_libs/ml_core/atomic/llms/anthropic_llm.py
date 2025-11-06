# src/shared_libs/atomic/llms/anthropic_llm.py

import os
import asyncio
from typing import Any, Dict, List, Optional, Union
from anthropic import AsyncAnthropic, APIStatusError, APITimeoutError, RateLimitError

# Import the resilient base wrapper and exceptions
from .base_llm_wrapper import BaseLLMWrapper, RETRY_STRATEGY 
from shared_libs.utils.exceptions import LLMRateLimitError, LLMServiceError, LLMAPIError, LLMTimeoutError

class AnthropicLLM(BaseLLMWrapper):
    """
    A wrapper class for the Anthropic API, implementing the BaseLLM interface 
    with built-in Resilience (Retry/Fallback).
    """

    def __init__(self, config: Dict[str, Any], is_fallback: bool = False):
        super().__init__(config, is_fallback)
        
        self.model_name = config.get("model_name")
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key must be provided or set in environment variable ANTHROPIC_API_KEY.")

        # Sử dụng AsyncAnthropic client cho Production
        self.client = AsyncAnthropic(api_key=api_key) 
        
        # Bổ sung timeout từ config (giả định)
        self._api_timeout = config.get('timeout', 60) 
        
        logger.info(f"AnthropicLLM initialized for model: {self.model_name}.")

    # ----------------------------------------------------
    # CORE PROTECTED ASYNC CALL (Implementing BaseLLMWrapper Contract)
    # ----------------------------------------------------

    async def _protected_async_call(self, method_name: str, *args, **kwargs) -> Any:
        """
        Routes the call to the appropriate Anthropic API and maps errors 
        to the Retry/Fallback mechanism.
        """
        try:
            # 1. GENERATE/CHAT (Anthropic gộp thành messages.create)
            if method_name == 'generate' or method_name == 'chat':
                prompt = kwargs.pop('prompt', kwargs.pop('messages', None))
                if isinstance(prompt, str):
                    messages = [{"role": "user", "content": prompt}]
                else:
                    messages = prompt
                
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=self.model_name,
                        messages=messages,
                        **kwargs
                    ),
                    timeout=self._api_timeout
                )
                return response.content[0].text
            
            # 2. EMBED
            elif method_name == 'embed':
                 # Anthropic không có endpoint nhúng native
                 raise NotImplementedError("The Anthropic API does not provide a native embedding endpoint.")

            else:
                raise NotImplementedError(f"Method {method_name} not implemented for Anthropic.")

        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Anthropic call timed out after {self._api_timeout}s.")
        except RateLimitError as e:
            # Rate Limit (429) -> Gây ra RETRY
            raise LLMRateLimitError(f"Anthropic Rate Limit Error: {e}") 
        except APIStatusError as e:
            # 5xx errors -> Gây ra RETRY
            if 500 <= e.status_code < 600:
                raise LLMServiceError(f"Anthropic Server Error ({e.status_code}): {e}")
            # Các lỗi khác (4xx) -> Gây ra FALLBACK/FAILURE
            raise LLMAPIError(f"Anthropic Client/API Error ({e.status_code}): {e}")
        except Exception as e:
            raise LLMAPIError(f"Unexpected error during Anthropic call: {e}")

    # ----------------------------------------------------
    # SYNCHRONOUS METHODS (DISCOURAGED - Fulfilling BaseLLM contract)
    # ----------------------------------------------------
    # Ta bỏ các phương thức đồng bộ cũ và thay bằng NotImplementedError
    
    def generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        raise NotImplementedError("Synchronous methods are discouraged in GenAI Factory.")

    def embed(self, text: str) -> List[float]:
        raise NotImplementedError("Synchronous methods are discouraged in GenAI Factory.")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Synchronous methods are discouraged in GenAI Factory.")