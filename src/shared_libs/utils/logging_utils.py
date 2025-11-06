import logging
import json
from typing import Dict, Any, Optional

# Cấu hình một format JSON tùy chỉnh
class JsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs logs as JSON strings. (HARDENING)
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            
            # --- CUSTOM METADATA (HARDENING ADDITIONS) ---
            "trace_id": getattr(record, 'trace_id', 'N/A'),
            "session_id": getattr(record, 'session_id', 'N/A'),
            "request_id": getattr(record, 'request_id', 'N/A'),
            "event_type": getattr(record, 'event_type', 'generic'), # Ví dụ: 'llm_call', 'tool_exec', 'security_event'
            "data": getattr(record, 'extra_data', {}),
        }
        # Nếu có exception, thêm thông tin stack trace
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(level=logging.INFO):
    """
    Sets up the application's logging with the structured JSON format.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # Thiết lập logging cho các thư viện khác (tắt verbose logging)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('aioredis').setLevel(logging.WARNING)
    
# Tiện ích để log với metadata
def get_structured_logger(name: str):
    """Returns a logger instance for structured logging."""
    return logging.getLogger(name)

# Hướng dẫn sử dụng:
# logger = get_structured_logger(__name__)
# logger.info("LLM response received", extra={'trace_id': 'xyz123', 'event_type': 'llm_call', 'extra_data': {'tokens': 500}})