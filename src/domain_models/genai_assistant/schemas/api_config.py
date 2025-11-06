# Ví dụ: Thêm vào shared_libs/configs/schemas/agent_config.py hoặc utility_config.py

class RootConfigSchema(BaseModel):
    """Schema tổng hợp kiểm tra tất cả các dependencies mà AssistantService cần."""
    
    # 1. Cấu hình Runtime/Server
    server_host: str = Field("0.0.0.0")
    server_port: int = Field(8000)
    redis_url: str = Field(..., description="URL kết nối Redis cho Rate Limiting và Memory.")

    # 2. Cấu hình Hardening
    rate_limit_requests: PositiveInt = Field(5)
    rate_limit_seconds: PositiveInt = Field(30)

    # 3. Tham chiếu đến các Config Files khác (Glue)
    llm_service_key: str = Field(..., description="Key cấu hình LLM Service.")
    safety_config_key: str = Field(..., description="Key cấu hình Safety Pipeline.")
    tool_config_key: str = Field(..., description="Key cấu hình Tool Registry.")
    
    # 4. Cấu hình MLOps (cho khởi tạo Tracker)
    mlflow_tracking_uri: str = Field(..., description="URI để theo dõi MLflow.")
    mlflow_experiment_name: str = Field("GenAI_Factory_Inference")