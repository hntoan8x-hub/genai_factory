import json
import logging
from typing import Dict, Any

# Set up a dedicated logger for user interactions
interaction_logger = logging.getLogger("interaction_logger")
interaction_logger.setLevel(logging.INFO)

# Create a handler to write to a file (or stdout in a containerized environment)
# In a real-world scenario, this would write to a log aggregation service.
file_handler = logging.FileHandler("interaction_logs.jsonl")
file_handler.setFormatter(logging.Formatter('%(message)s'))
interaction_logger.addHandler(file_handler)

def log_interaction(user_id: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
    """
    Logs a single user-assistant interaction in a structured format.

    Args:
        user_id (str): A unique identifier for the user.
        input_data (Dict[str, Any]): The raw input from the user.
        output_data (Dict[str, Any]): The full output from the assistant.
    """
    log_entry = {
        "timestamp": json.dumps(json.JSONEncoder().default(None)),  # Use a time library for production
        "user_id": user_id,
        "input": input_data,
        "output": output_data
    }
    interaction_logger.info(json.dumps(log_entry))
