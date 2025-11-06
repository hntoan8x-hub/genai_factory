# shared_libs/atomic/llms/huggingface_llm.py
import os
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Any, Dict, List, Optional, Union

# Import the resilient base wrapper and exceptions
from .base_llm_wrapper import BaseLLMWrapper 
from shared_libs.exceptions import LLMAPIError # Use LLMAPIError for fatal local errors

class HuggingFaceLLM(BaseLLMWrapper):
    """
    A wrapper class for a local Hugging Face model, implementing the BaseLLM interface
    and supporting the Async contract via a ThreadPoolExecutor.
    """

    def __init__(self, config: Dict[str, Any], is_fallback: bool = False):
        super().__init__(config, is_fallback)
        
        model_path = config.get("model_path")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path not found: {model_path}")

        # Use a ThreadPoolExecutor for offloading blocking synchronous calls
        self.executor = ThreadPoolExecutor(max_workers=1) 
        
        print(f"Loading model from {model_path}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            # Use Auto for flexible model loading
            self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
            print("Model loaded successfully.")
        except Exception as e:
            # Fatal error during initialization (e.g., missing GPU, corrupt files)
            raise LLMAPIError(f"Fatal error loading Hugging Face model: {e}")

    # --- Resilience Implementation (Async via Executor) ---
    
    # For local models, _protected_async_call simply executes the sync function 
    # in a thread and uses LLMAPIError for fatal local failures.
    async def _protected_async_call(self, method_name: str, *args, **kwargs) -> Any:
        loop = asyncio.get_event_loop()
        
        # Determine the synchronous method to call
        if method_name == 'generate':
            sync_method = self.generate
        elif method_name == 'chat':
            sync_method = self.chat
        elif method_name == 'embed':
            sync_method = self.embed
        else:
            raise NotImplementedError
            
        # Run the synchronous call in a separate thread
        try:
            return await loop.run_in_executor(self.executor, sync_method, *args, **kwargs)
        except Exception as e:
            # Treat any local error (OOM, CUDA failure) as a non-retryable API error 
            # to trigger the Fallback mechanism in BaseLLMWrapper.
            raise LLMAPIError(f"Hugging Face local execution failed: {e}")


    # --- Synchronous Methods (Implementations used by _protected_async_call) ---
    # These remain similar to the original provided code.
    
    def generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        # (Original synchronous implementation logic goes here)
        if isinstance(prompt, List):
            full_prompt = self.tokenizer.apply_chat_template(prompt, tokenize=False)
        else:
            full_prompt = prompt

        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, **kwargs)
        
        response_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return response_text

    def embed(self, text: str) -> List[float]:
        # (Original synchronous implementation logic goes here)
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.model.device)
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            hidden_states = outputs.hidden_states[-1]
            embeddings = torch.mean(hidden_states, dim=1).squeeze().tolist()
        return embeddings

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # (Original synchronous implementation logic goes here)
        chat_template = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return self.generate(chat_template, **kwargs)