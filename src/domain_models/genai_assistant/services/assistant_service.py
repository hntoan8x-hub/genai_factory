# src/domain_models/genai_assistant/services/assistant_service.py

import logging
from typing import Any, Union, Dict, Optional
from uuid import uuid4
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import ValidationError
from redis import Redis 
import asyncio 

# Import Hardening dependencies for Rate Limiting
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter 

# Import necessary domain schemas and services
from domain_models.genai_assistant.schemas.assistant_schema import AssistantInputSchema, AssistantOutputSchema 
from domain_models.genai_assistant.schemas.config_schemas import LLMConfigSchema, SafetyConfigSchema, AssistantConfigSchema 
from .assistant_inference import AssistantInferenceService 
from .memory_service import MemoryService 
from .tool_service import ToolService 
from shared_libs.utils.exceptions import SecurityError, GenAIFactoryError 

# 🚨 CẬP NHẬT: Import Factory và BaseTracker/MLflow Adapter
from shared_libs.factory.llm_factory import LLMFactory
from shared_libs.mlops.base.base_tracker import BaseTracker
# Giả định MLflowTracker là triển khai cụ thể của BaseTracker
from shared_libs.mlops.mlflow.mlflow_tracker import MLflowTracker 

# Import Hardening Modules
from .auth_middleware import auth_middleware
from src.shared_libs.logging.audit_logger import AuditLogger 

logger = logging.getLogger(__name__)

# --- CONFIGURATION (MOCK Loader for Production Setup) ---
def load_and_validate_configs() -> Dict[str, Any]:
    """Mô phỏng việc tải và xác thực cấu hình bằng Pydantic Schemas."""
    
    # 1. Dữ liệu cấu hình thô (Trong Production, sẽ tải từ YAML/ENV)
    raw_llm_config = {"model_name": "gpt-4o", "endpoint": "openai_api", "retry_attempts": 3, "timeout_seconds": 60}
    raw_safety_config = {"toxicity_threshold": 0.85, "input_injection_check": True, "blocklist": ["delete table"], "pii_patterns": ["\d{3}-\d{2}-\d{4}"]}
    raw_assistant_config = {"persona": "finance_analyst", "default_pipeline": "conversation", "max_history_tokens": 1500, "welcome_message": "Hello!"}
    raw_tool_configs = {"sql_tool": {"type": "sql_query_executor"}}
    raw_mlflow_config = {"tracking_uri": "http://mlflow-server:5000", "experiment_name": "GenAI_Assistant_Inference"} # 🚨 MOCK MLflow Config
    
    # 2. XÁC THỰC BẰNG SCHEMA (CRITICAL HARDENING)
    try:
        validated_configs = {
            'llm_config': LLMConfigSchema(**raw_llm_config),
            'safety_config': SafetyConfigSchema(**raw_safety_config),
            'assistant_config': raw_assistant_config, 
            'tool_configs': raw_tool_configs,
            'mlflow_config': raw_mlflow_config # 🚨 Thêm config MLflow
        }
        logger.info("Configuration successfully loaded and validated.")
        return validated_configs
    except ValidationError as e:
        logger.critical(f"FATAL: Configuration validation failed during startup: {e}")
        raise RuntimeError("System configuration failed Pydantic validation.") from e

# --- APPLICATION SETUP ---
app = FastAPI(title="GenAI Assistant Production API", version="1.0.0")

# Khởi tạo dịch vụ
inference_service: AssistantInferenceService = None 
redis_client: Redis = None
mlflow_tracker: Optional[BaseTracker] = None # 🚨 GLOBAL: Biến lưu trữ MLflow Tracker

REDIS_HOST = "localhost" 
REDIS_PORT = 6379

# --- GLOBAL LIFESPAN EVENTS ---
@app.on_event("startup")
async def startup_event():
    """Initializes Rate Limiter and core services (Dependency Injection)."""
    try:
        configs = load_and_validate_configs() # Tải và xác thực Config

        # 1. Initialize Redis for Rate Limiting & Memory Service
        global redis_client
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_client)
        logger.info("Rate Limiter initialized.")
        
        # 2. Initialize MLflow Tracker (CRITICAL MLOPS COMPONENT) 🚨
        global mlflow_tracker
        mlflow_config = configs.get('mlflow_config', {})
        if mlflow_config:
            # Khởi tạo MLflowTracker Adapter, chuyển config vào
            mlflow_tracker = MLflowTracker(
                tracking_uri=mlflow_config['tracking_uri'],
                experiment_name=mlflow_config['experiment_name']
            )
            logger.info(f"MLflow Tracker initialized with URI: {mlflow_config['tracking_uri']}.")
        
        # 3. Initialize Hardened Services
        llm_for_memory = LLMFactory.build(configs['llm_config'].dict()) 
        memory_service = MemoryService(configs['llm_config'], f"redis://{REDIS_HOST}:{REDIS_PORT}/0", llm_for_memory)
        tool_service = ToolService(configs['tool_configs'])
        
        # 4. Initialize Central Inference Service (INJECT DEPENDENCIES)
        global inference_service
        inference_service = AssistantInferenceService(
            configs=configs,
            memory_service=memory_service,
            tool_service=tool_service,
            tracker=mlflow_tracker # 🚨 INJECT MLflow Tracker vào Inference Service
        )
        logger.info("All Production Services initialized.")
        
    except Exception as e:
        logger.critical(f"Failed to initialize critical services: {e.__class__.__name__}: {e}")
        # THROW LỖI STARTUP NẾU CÁC DỊCH VỤ CỐT LÕI THẤT BẠI
        raise


# ----------------------------------------------------
# MIDDLEWARE VÀ DEPENDENCIES (CRITICAL HARDENING)
# ----------------------------------------------------
# ... (Phần này giữ nguyên) ...

# 1. Áp dụng AuthN/AuthZ Middleware
app.router.dependencies.append(Depends(auth_middleware))

# 2. Rate Limiter Configuration (5 requests per client IP every 30 seconds)
LIMIT_PER_CLIENT = Depends(RateLimiter(times=5, seconds=30))


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """ Standard health check endpoint (Used by k8s liveness/readiness probes). """
    return {"status": "ok", "service": "assistant"}


@app.post("/generate", 
          response_model=AssistantOutputSchema, 
          status_code=status.HTTP_200_OK,
          dependencies=[LIMIT_PER_CLIENT]) 
async def process_request(request: Request, request_data: AssistantInputSchema):
    """
    Handles user requests, enforcing AuthZ, Rate Limiting, and Audit Logging.
    """
    # 1. Khởi tạo Audit & Tracing Context
    request_id = str(uuid4()) 
    user_id = getattr(request.state, 'user_id', 'anonymous')
    user_role = getattr(request.state, 'user_role', 'guest')
    
    # Ghi lại sự kiện bắt đầu vào Audit Trail
    AuditLogger.log_request_start(request_id, user_id, request_data.query)

    llm_cost = 0.0
    final_status = "FAILED"
    
    try:
        # 2. Thực thi Logic Nghiệp vụ (Truyền thông tin AuthZ vào Inference Service)
        response_data = await inference_service.async_run_pipeline(
            request_data=request_data,
            user_role=user_role
        )
        
        # 3. Trích xuất thông tin Audit/Metrics (sử dụng Schemas)
        llm_cost = response_data.get("llm_cost_usd", 0.0)
        final_status = "SUCCESS"
        
        # Buộc trả về AssistantOutputSchema đã được điền đầy đủ
        return AssistantOutputSchema(
            response=response_data['response'],
            pipeline=response_data['pipeline'],
            request_id=request_id,
            llm_cost_usd=llm_cost,
            tokens_used=response_data.get('tokens_used', {}),
            metadata=response_data.get('metadata', {})
        )
        
    except ValidationError as e:
        final_status = "INPUT_VALIDATION_ERROR"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid request format: {e.errors()}")
        
    except SecurityError as e:
        # Lỗi bảo mật từ SafetyPipeline hoặc ToolService (Access Denied/Injection Block)
        final_status = "SECURITY_VIOLATION"
        AuditLogger.log_security_event(request_id, f"Blocked by Security Pipeline: {e}", severity="HIGH")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Policy violation: {e}")
        
    except GenAIFactoryError as e:
        # Lỗi framework nội bộ (LLM Fallback/Retry thất bại, Tool execution)
        final_status = "SERVICE_UNAVAILABLE"
        logger.error(f"Internal GenAI framework error: {e.__class__.__name__} for {request_id}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The GenAI service is temporarily unavailable.")
        
    except Exception as e:
        # Lỗi không xác định
        final_status = "UNHANDLED_CRITICAL"
        logger.critical(f"Unhandled critical error for {request_id}: {e.__class__.__name__}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected critical error occurred.")
        
    finally:
        # Ghi lại kết quả cuối cùng vào Audit Trail (luôn luôn chạy)
        AuditLogger.log_final_response(request_id, user_id, final_status, llm_cost)