class GenAIFactoryError(Exception):
    """Base exception for all GenAI Factory custom errors."""
    pass

# --- LLM API Errors (Used for Resilience Logic) ---
class LLMAPIError(GenAIFactoryError):
    """Base exception for errors originating from external LLM API calls."""
    pass

class LLMRateLimitError(LLMAPIError):
    """Raised when the LLM API returns a 429 status code (Too Many Requests)."""
    pass

class LLMServiceError(LLMAPIError):
    """Raised for transient 5xx errors from the LLM service (e.g., server overload)."""
    pass

# --- Tool Errors (Used for Tool Hardening) ---
class ToolExecutionError(GenAIFactoryError):
    """Base exception for errors that occur during tool execution."""
    pass

class ToolInputValidationError(ToolExecutionError):
    """Raised when the input to a tool does not match its Pydantic schema."""
    pass

class SecurityError(ToolExecutionError):
    """Raised for security violations (e.g., detected SQL Injection attempts)."""
    pass