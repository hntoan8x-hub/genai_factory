# shared_libs/utils/tracing_utils.py
import logging
import asyncio
from opentelemetry import trace
from opentelemetry.trace import Span
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)

# --- OPEN TELEMETRY SETUP (Giả định đã được cấu hình trong main/startup) ---
# Trong một ứng dụng thực tế, tracer sẽ được khởi tạo trong startup event
tracer = trace.get_tracer("genai.factory.tracer") 

class TracingUtils:
    """
    Utility class for handling asynchronous distributed tracing using OpenTelemetry.
    Provides an async context manager for creating traceable spans.
    """

    @staticmethod
    async def _start_span(span_name: str, span_type: str, context: Dict[str, Any]) -> Span:
        """
        Internal method to start a new OpenTelemetry Span.
        """
        # Bắt đầu một span mới, tự động lấy context từ thread/task hiện tại
        span = tracer.start_span(span_name)
        
        # Thêm các thuộc tính (attributes) để dễ dàng truy vấn trong Grafana/Jaeger
        span.set_attribute("span.type", span_type)
        for k, v in context.items():
            # Chỉ lưu trữ các giá trị không quá lớn
            if isinstance(v, (str, int, float, bool)):
                span.set_attribute(k, v)
        
        return span

    @staticmethod
    @asynccontextmanager
    async def async_span(span_name: str, span_type: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Span, None]:
        """
        An asynchronous context manager that creates and ends a tracing span.
        
        Usage:
        async with TracingUtils.async_span("llm_call", "api", {"model": "gpt-4o"}):
            await client.call()
        """
        if context is None:
            context = {}
            
        span = await TracingUtils._start_span(span_name, span_type, context)
        
        try:
            yield span
        except Exception as e:
            # Ghi lại ngoại lệ vào span nếu có lỗi
            span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, description=str(e)))
            raise
        finally:
            # Đảm bảo span luôn được kết thúc (End)
            span.end()


# --- VÍ DỤ SỬ DỤNG (Áp dụng cho LLM Wrapper) ---

# Giả định:
# from shared_libs.atomic.llms.base_llm_wrapper import BaseLLMWrapper

# class OpenAILLM(BaseLLMWrapper):
#     async def _protected_async_call(self, method_name: str, *args, **kwargs) -> Any:
#         async with TracingUtils.async_span("openai_chat_completion", "llm_api", {"method": method_name, "model": self.model_name}):
#             # Đây là nơi logic gọi API OpenAI thực sự xảy ra
#             response = await self.client.chat.completions.create(...)
#             return response.choices[0].message.content