from typing import Dict, Any

class ToolConfig:
    """
    Configuration for the tools available to agents.

    This class stores connection details and API keys for external services
    that tools need to interact with.
    """
    SQL_TOOL_CONFIG: Dict[str, Any] = {
        "type": "sql",
        "db_connection_string": "sqlite:///data/my_database.db", # Database connection string
    }
    
    RISK_TOOL_CONFIG: Dict[str, Any] = {
        "type": "risk",
        "model_path": "/path/to/risk_model.h5", # Path to a local machine learning model
    }
    
    WEB_TOOL_CONFIG: Dict[str, Any] = {
        "type": "web",
        "api_key": "YOUR_SEARCH_API_KEY", # API key for a search service (e.g., Google Search API)
    }

    CALCULATOR_TOOL_CONFIG: Dict[str, Any] = {
        "type": "calculator",
        # No specific configuration needed for a simple calculator
    }

    EMAIL_TOOL_CONFIG: Dict[str, Any] = {
        "type": "email",
        "smtp_server": "smtp.gmail.com",
        "port": 587,
        "username": "your_email@gmail.com",
        "password": "YOUR_EMAIL_APP_PASSWORD",
    }
