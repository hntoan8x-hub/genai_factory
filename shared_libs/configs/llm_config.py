from typing import Dict, Any
# Import the validation schemas
from .schemas import OpenAILLMConfig, AnthropicLLMConfig, HuggingFaceLLMConfig 

class LLMConfig:
    """
    Configuration for different LLM providers, validated at runtime. (HARDENING)
    """
    # Validate the data against the Pydantic schema
    OPENAI_CONFIG: Dict[str, Any] = OpenAILLMConfig(
        type="openai",
        api_key="YOUR_OPENAI_API_KEY",
        model_name="gpt-4o",
        temperature=0.7,
        max_tokens=1000,
    ).model_dump() # Store validated data as a dictionary

    ANTHROPIC_CONFIG: Dict[str, Any] = AnthropicLLMConfig(
        type="anthropic",
        api_key="YOUR_ANTHROPIC_API_KEY",
        model_name="claude-3-sonnet-20240229",
        temperature=0.6,
        max_tokens=800,
    ).model_dump()

    HUGGINGFACE_CONFIG: Dict[str, Any] = HuggingFaceLLMConfig(
        type="huggingface",
        model_path="/path/to/your/local/model",
        device="cuda",
        temperature=0.5,
    ).model_dump()