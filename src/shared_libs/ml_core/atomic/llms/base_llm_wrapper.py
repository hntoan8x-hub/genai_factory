# shared_libs/atomic/llms/base_llm_wrapper.py (Conceptual)

import logging
from typing import Any, Dict, List, Optional, Union
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from shared_libs.base.base_llm import BaseLLM
# Assuming these exceptions are defined in shared_libs/exceptions.py
from shared_libs.utils.exceptions import LLMRateLimitError, LLMServiceError, LLMAPIError 

logger = logging.getLogger(__name__)

# --- Resilience Configuration (HARDENING) ---
# Retry Strategy: Exponential Backoff with Jitter
# Rationale: Max 5 attempts, waiting exponentially up to 60s. 
# Only retries on specific transient errors (Rate Limit, Server Errors).
RETRY_STRATEGY = retry(
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((LLMRateLimitError, LLMServiceError)),
    reraise=True # Reraise the exception if all 5 attempts fail
)

class BaseLLMWrapper(BaseLLM):
    """
    Base class providing automatic resilience (Retry) and Fallback functionality 
    to all concrete LLM implementations (e.g., OpenAI, Anthropic).
    
    Concrete classes must implement the synchronous methods and the abstract 
    _protected_async_call method.
    """

    def __init__(self, config: Dict[str, Any], is_fallback: bool = False):
        self.config = config
        self.is_fallback = is_fallback
        self._fallback_llm: Optional[BaseLLM] = None
        
        if self.is_fallback:
            logger.info(f"LLM Wrapper initialized as a FALLBACK model: {self.__class__.__name__}")
        else:
            logger.info(f"LLM Wrapper initialized as a PRIMARY model: {self.__class__.__name__}")

    def set_fallback_llm(self, llm: BaseLLM) -> None:
        """Assigns a secondary LLM instance for failover scenarios (Circuit Breaker)."""
        self._fallback_llm = llm

    # --- Abstract Protected Async Call (Retry Implementation) ---
    @RETRY_STRATEGY
    async def _protected_async_call(self, method_name: str, *args, **kwargs) -> Any:
        """
        This method is automatically wrapped by the RETRY_STRATEGY.
        Concrete wrappers must implement this to route the call to the actual API.
        If an API error occurs, they must raise the appropriate LLMRateLimitError/LLMServiceError 
        to trigger a retry, or LLMAPIError to fail and trigger fallback.
        """
        raise NotImplementedError("Concrete LLM wrapper must implement this protected call.")

    # --- Public Asynchronous Methods (Fallback Implementation) ---

    async def async_generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """Generates text, protected by Retry (in _protected_async_call) and Fallback."""
        try:
            return await self._protected_async_call('generate', prompt=prompt, **kwargs)
        except Exception as e:
            if self._fallback_llm:
                logger.error(f"Primary LLM failed after retries ({type(e).__name__}). Switching to fallback.")
                # Call fallback (synchronous or async)
                return await self._fallback_llm.async_generate(prompt, **kwargs)
            logger.critical(f"Primary LLM failed, and no fallback configured. Fatal error: {e}")
            raise e

    async def async_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Conducts a chat session, protected by Retry and Fallback."""
        try:
            return await self._protected_async_call('chat', messages=messages, **kwargs)
        except Exception as e:
            if self._fallback_llm:
                logger.error(f"Chat failed after retries ({type(e).__name__}). Switching to fallback.")
                return await self._fallback_llm.async_chat(messages, **kwargs)
            logger.critical(f"Chat failed, and no fallback configured. Fatal error: {e}")
            raise e

    async def async_embed(self, text: str) -> List[float]:
        """Embeds text, protected by Retry and Fallback."""
        try:
            return await self._protected_async_call('embed', text=text)
        except Exception as e:
            if self._fallback_llm:
                logger.error(f"Embedding failed after retries ({type(e).__name__}). Switching to fallback.")
                return await self._fallback_llm.async_embed(text)
            logger.critical(f"Embedding failed, and no fallback configured. Fatal error: {e}")
            raise e

    # --- Synchronous Methods (Required by BaseLLM) ---
    # Concrete wrappers must implement these, though they are discouraged in high-concurrency loops.
    def generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        raise NotImplementedError("Synchronous methods should be implemented but ASYNC methods are preferred.")

    def embed(self, text: str) -> List[float]:
        raise NotImplementedError("Synchronous methods should be implemented but ASYNC methods are preferred.")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Synchronous methods should be implemented but ASYNC methods are preferred.")