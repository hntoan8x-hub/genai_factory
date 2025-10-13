import logging
import json
from datetime import datetime
from typing import Dict, Any

def setup_logger(name: str, level: int = logging.INFO, log_format: str = 'json') -> logging.Logger:
    """
    Sets up a logger with a specified name, level, and format.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        log_format (str): The format of the log output ('json' or 'text').

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevents adding duplicate handlers if the function is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        
        if log_format == 'json':
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

class JSONFormatter(logging.Formatter):
    """A custom logging formatter that outputs logs as JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
            
        # In a production system, this could be sent to MLflow or a JSONL file
        return json.dumps(log_entry, ensure_ascii=False)

def log_event(logger: logging.Logger, event: str, payload: Dict[str, Any]) -> None:
    """
    Logs a structured event with an associated payload.

    Args:
        logger (logging.Logger): The logger instance to use.
        event (str): The name of the event (e.g., 'agent_step', 'tool_call').
        payload (Dict[str, Any]): The data to log for the event.
    """
    log_data = {
        "event": event,
        **payload
    }
    logger.info(json.dumps(log_data))
