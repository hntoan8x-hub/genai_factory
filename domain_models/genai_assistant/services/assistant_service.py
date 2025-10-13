# domain_models/genai_assistant/services/assistant_service.py

import logging
from typing import Any
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import ValidationError
from redis import Redis # Import Redis client for rate limiting backend

# Import dependencies for Rate Limiting (Requires `fastapi-limiter` or similar setup)
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter 

# Import necessary domain schemas and services
from domain_models.genai_assistant.schemas.assistant_schema import AssistantInputSchema, AssistantOutputSchema
from .assistant_inference import AssistantInferenceService 
from shared_libs.exceptions import SecurityError, GenAIFactoryError 

logger = logging.getLogger(__name__)

# --- APPLICATION SETUP ---
app = FastAPI(title="GenAI Assistant Production API", version="1.0.0")

# --- GLOBAL LIFESPAN EVENTS (HARDENING: Initialize/Shutdown Resources) ---

# Replace with your actual Redis connection details from infra/
REDIS_HOST = "localhost" 
REDIS_PORT = 6379

@app.on_event("startup")
async def startup_event():
    """Initializes Rate Limiter and core services."""
    try:
        # 1. Initialize Rate Limiter using Redis as the backend
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_client)
        logger.info("Rate Limiter initialized successfully with Redis.")
        
        # 2. Initialize the core inference service
        global inference_service
        inference_service = AssistantInferenceService()
        logger.info("Assistant Inference Service initialized.")
        
    except Exception as e:
        logger.critical(f"Failed to initialize critical services: {e}")
        # In a real app, this should crash the startup for safety
        

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    # (Add any necessary cleanup code here)
    pass


# --- API ENDPOINTS (HARDENING: Rate Limiting and Error Handling) ---

# Rate Limiter Configuration (5 requests per client IP every 30 seconds)
# This protects against sudden traffic spikes and DoW attacks.
LIMIT_PER_CLIENT = Depends(RateLimiter(times=5, seconds=30))

@app.post("/generate", 
          response_model=AssistantOutputSchema, 
          status_code=status.HTTP_200_OK,
          # Apply the Hardening dependency
          dependencies=[LIMIT_PER_CLIENT]) 
async def process_request(request_data: AssistantInputSchema):
    """
    Handles user requests, enforcing Rate Limiting and strict error contracts.
    """
    try:
        # Use the hardened asynchronous pipeline runner
        response_data = await inference_service.async_run_pipeline(request_data)
        
        return AssistantOutputSchema(**response_data)
        
    except ValidationError as e:
        # Handle Pydantic validation failures explicitly (e.g., if JSON body is malformed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request format: {e.errors()}"
        )
        
    except SecurityError as e:
        # Handle blocking errors from SafetyPipeline (Input Injection)
        logger.warning(f"Security event blocked request: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Request blocked due to security policy violation: {e}"
        )
        
    except GenAIFactoryError as e:
        # Handle internal framework errors (LLM failure, Tool timeout, etc.)
        logger.error(f"Internal GenAI framework error: {e.__class__.__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, # Use 503 for transient service issues
            detail="The GenAI service is temporarily unavailable or encountered a failure."
        )
        
    except Exception as e:
        # Catch all unexpected errors
        logger.critical(f"Unhandled critical error: {e.__class__.__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected critical error occurred."
        )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Standard health check endpoint. (Used by k8s liveness and readiness probes)
    """
    # A full check would also verify Redis, VectorDB, and LLM API status.
    # We return a 200 OK for basic readiness.
    return {"status": "ok", "service": "assistant"}