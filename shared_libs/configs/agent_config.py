from typing import Dict, Any, List

class AgentConfig:
    """
    Configuration for different agent types.

    This class defines the parameters required to set up agents, including their
    type, behavioral settings, and the tools they have access to.
    """
    REACT_AGENT_CONFIG: Dict[str, Any] = {
        "type": "react",
        "llm_config_key": "openai", # Key mapping to LLMFactory configuration
        "tools": ["sql", "web", "calculator"], # List of tool keys
        "max_loops": 10,
        "verbose": True,
    }

    CREWAI_AGENT_CONFIG: Dict[str, Any] = {
        "type": "crewai",
        "llm_config_key": "anthropic",
        "role": "Financial Analyst",
        "goal": "Analyze Q3 earnings report for Google",
        "backstory": "A seasoned analyst with a keen eye for detail and market trends.",
        "tools": ["web", "email"],
    }
