# src/shared_libs/telemetry/tracer_utils.py

import logging
from opentelemetry import trace
from functools import wraps
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)
# Giả định TracerProvider đã được thiết lập ở Composition Root (assistant_service.py)
TRACER = trace.get_tracer(__name__)

class TracerUtils:
    """
    Utility class for integrating OpenTelemetry tracing with asynchronous functions.
    """

    @staticmethod
    def trace_async(span_name: str, attributes: Optional[Dict[str, Any]] = None) -> Callable:
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                
                # Hardening: Lấy request_id từ kwargs hoặc args (thường là tham số đầu tiên)
                # Đây là một MOCK để minh họa logic
                inferred_attrs = {}
                request_id = kwargs.get('request_id') or (args[0] if args and isinstance(args[0], str) else None)
                if request_id:
                    inferred_attrs["request.id"] = request_id
                
                final_attributes = {**(attributes or {}), **inferred_attrs}
                
                with TRACER.start_as_current_span(span_name, attributes=final_attributes) as span:
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("status.code", "OK")
                        return result
                    except Exception as e:
                        # ... (xử lý lỗi không đổi) ...
                        span.set_attribute("status.code", "ERROR")
                        span.set_attribute("error.message", str(e))
                        raise
            return wrapper
        return decorator

    @staticmethod
    async def async_span(span_name: str, component: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Asynchronous context manager to manually create a span.
        """
        # Đây là phiên bản context manager cơ bản, tương tự như trong genai_orchestrator
        # Nó đảm bảo logic tracing vẫn được hỗ trợ
        
        span = TRACER.start_span(span_name, attributes={**(attributes or {}), "component": component})
        
        try:
            yield span
        finally:
            span.end()