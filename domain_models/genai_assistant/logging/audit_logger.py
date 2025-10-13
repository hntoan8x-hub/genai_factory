import logging
import json
from typing import Dict, Any

# Set up a dedicated logger for audit events
audit_logger = logging.getLogger("audit_logger")
audit_logger.setLevel(logging.INFO)

# Create a handler for audit logs
file_handler = logging.FileHandler("audit_logs.jsonl")
file_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(file_handler)

def log_audit_event(event_type: str, user_id: str, details: Dict[str, Any]):
    """
    Logs an auditable event for compliance and security purposes.

    Args:
        event_type (str): The type of event (e.g., "prompt_denied", "access_granted").
        user_id (str): The ID of the user associated with the event.
        details (Dict[str, Any]): A dictionary with event-specific details.
    """
    log_entry = {
        "timestamp": json.dumps(json.JSONEncoder().default(None)),
        "event_type": event_type,
        "user_id": user_id,
        "details": details
    }
    audit_logger.info(json.dumps(log_entry))
