from typing import Dict, Any
from shared_libs.genai.factory.tool_factory import ToolFactory
from GenAI_Factory.domain_models.genai_assistant.configs.tool_config import tool_config

class ToolService:
    """
    Service for dynamically registering and routing calls to tools.
    
    This service acts as a central hub for all available tools, providing a
    registry and a method for executing them based on a tool name.
    """
    
    def __init__(self):
        """Initializes the tool registry from configuration."""
        self.tool_registry = self._build_tools_from_config()
        
    def _build_tools_from_config(self) -> Dict[str, Any]:
        """Builds all tools defined in the tool configuration."""
        tools = {}
        for tool_name, tool_config in tool_config.items():
            try:
                tools[tool_name] = ToolFactory.build(tool_config)
            except Exception as e:
                print(f"Error building tool '{tool_name}': {e}")
        return tools
    
    def execute_tool(self, tool_name: str, input_data: Any) -> Any:
        """
        Executes a specific tool with the given input data.
        
        Args:
            tool_name (str): The name of the tool to execute.
            input_data (Any): The input data for the tool.
            
        Returns:
            Any: The output of the executed tool.
            
        Raises:
            ValueError: If the tool name is not found in the registry.
        """
        tool = self.tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        
        print(f"Executing tool '{tool_name}'...")
        return tool.run(input=input_data)
        
