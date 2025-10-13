from typing import Dict, Any, List
from shared_libs.genai.factory.agent_factory import AgentFactory
from shared_libs.genai.factory.tool_factory import ToolFactory
from shared_libs.genai.configs.agent_config import AgentConfig

class OrchestrationPipeline:
    """
    Orchestrates complex tasks using a multi-agent system.

    This pipeline selects and runs the appropriate agent (e.g., ReAct, CrewAI)
    to fulfill a user's request.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the OrchestrationPipeline with configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary for this pipeline.
        """
        self.config = config
        
        # Build the tools registry based on config
        self.tools = {
            tool_name: ToolFactory.build({"type": tool_name})
            for tool_name in config.get("tools", [])
        }
        
        self.agent = AgentFactory.build(config.get("agent", {}), tools=self.tools)

    def run(self, query: str) -> Dict[str, Any]:
        """
        Executes the orchestration pipeline by running the configured agent.

        Args:
            query (str): The user's input query.

        Returns:
            Dict[str, Any]: The final output from the agent's execution.
        """
        print(f"Executing orchestration pipeline with agent: {self.agent.__class__.__name__}")
        
        try:
            # The agent's `run` method will handle the plan-act-observe loop
            result = self.agent.run(query)
        except Exception as e:
            return {"error": str(e)}

        print("Orchestration pipeline completed.")
        return {"response": result}
