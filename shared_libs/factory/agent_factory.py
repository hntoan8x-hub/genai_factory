from typing import Dict, Any
from shared_libs.genai.base.base_agent import BaseAgent
from shared_libs.genai.base.base_llm import BaseLLM
from shared_libs.genai.base.base_tool import BaseTool
from shared_libs.genai.atomic.agents.react_agent import ReActAgent
from shared_libs.genai.atomic.agents.autogen_agent import AutoGenAgent
from shared_libs.genai.atomic.agents.crewai_agent import CrewAIAgent

class AgentFactory:
    """
    A factory class for creating Agent instances based on configuration.
    It encapsulates the logic for building different agent types.
    """

    def __init__(self):
        """Initializes the AgentFactory."""
        self._agent_types = {
            "react": ReActAgent,
            "autogen": AutoGenAgent,
            "crewai": CrewAIAgent,
        }

    def build(self, config: Dict[str, Any], llm: BaseLLM, tools: list[BaseTool] = []) -> BaseAgent:
        """
        Builds an Agent instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): A dictionary containing the agent configuration.
                                     Must have a 'type' key.
            llm (BaseLLM): The LLM instance the agent will use.
            tools (list[BaseTool]): A list of tools the agent can use.

        Returns:
            BaseAgent: An instance of the requested Agent type.

        Raises:
            ValueError: If the 'type' in the config is not supported.
        """
        agent_type = config.get("type")
        if not agent_type or agent_type not in self._agent_types:
            raise ValueError(f"Unsupported Agent type: {agent_type}. Supported types are: {list(self._agent_types.keys())}")
        
        agent_class = self._agent_types[agent_type]
        
        if agent_type == "react":
            return agent_class(llm=llm, tools=tools, max_loops=config.get("max_loops", 10))
        elif agent_type == "autogen":
            return agent_class(llm=llm, role=config.get("role"), name=config.get("name"), description=config.get("description"))
        elif agent_type == "crewai":
            return agent_class(llm=llm, role=config.get("role"), goal=config.get("goal"), backstory=config.get("backstory"), tools=tools)
        
        # Fallback for unexpected types
        raise ValueError(f"Could not build agent for type: {agent_type}")
