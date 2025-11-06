# shared_libs/atomic/agents/react_agent.py

import re
import json
import asyncio
from typing import Any, Dict, List, Optional
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool
from shared_libs.atomic.prompts.react_prompt import ReActPrompt
from shared_libs.utils.exceptions import ToolExecutionError, GenAIFactoryError

class ReActAgent(BaseAgent):
    """
    An agent that implements the ReAct (Reasoning and Acting) pattern.
    It includes resource control (max_steps, timeout) and uses asynchronous 
    operations for production stability.
    """

    # --- BaseAgent Properties (HARDENING) ---
    @property
    def name(self) -> str:
        return "react_research_agent"

    @property
    def description(self) -> str:
        return "An agent that uses ReAct pattern to reason, act with tools, and observe results for multi-step tasks."

    def __init__(self, llm: BaseLLM, tools: List[BaseTool], max_loops: int = 10):
        self.llm = llm
        # Using tool.name as the key for robustness
        self.tools = {tool.name: tool for tool in tools} 
        self.max_loops = max_loops
        self.history: List[str] = []
        self.react_prompt = ReActPrompt()
    
    def _parse_action_input(self, action_input: str) -> Dict[str, Any]:
        """
        Safely parses the Action Input string into a dictionary. (HARDENING FIX: Replaces unsafe eval())
        """
        try:
            # Use json.loads for safe parsing of the LLM-generated dictionary/JSON string
            # LLM must be instructed to output valid JSON for the Action Input
            return json.loads(action_input)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"LLM generated malformed JSON input for tool: {e}")

    # --- Asynchronous Action/Execution ---

    async def _async_act(self, action_string: str) -> str:
        """
        Asynchronously parses the action string and executes the corresponding tool.
        """
        action_match = re.search(r'Action: (\w+)\nAction Input: (.+)', action_string, re.DOTALL)
        if not action_match:
            return "Observation: Error: Could not parse Action or Action Input from LLM response."
            
        action_name = action_match.group(1).strip()
        action_input_str = action_match.group(2).strip()

        if action_name not in self.tools:
            return f"Observation: Error: Tool '{action_name}' not found."
            
        tool = self.tools[action_name]
        
        try:
            input_dict = self._parse_action_input(action_input_str)
            # Use the preferred asynchronous run method of the tool
            observation = await tool.async_run(input_dict) 
            return f"Observation: {observation}"
        except Exception as e:
            # Catch ToolExecutionError, SecurityError, etc. from tool's run method
            return f"Observation: Error executing tool '{action_name}': {e.__class__.__name__}: {str(e)}"

    async def _execute_stepped_loop(self, query: str, max_steps: int, cycle_fn):
        """Helper to run the loop with step limits, handling initial thought."""
        
        # 1. Generate initial context and thought
        context = {
            "question": query,
            "tools_string": "\n".join([f"- {name}: {tool.description}" for name, tool in self.tools.items()]),
            "tool_names": ", ".join(self.tools.keys()),
            "agent_history": ""
        }
        initial_thought = await self.llm.async_generate(self.react_prompt.render(context))
        self.history.append(initial_thought)
        
        # 2. Run the main loop
        for i in range(1, max_steps + 1):
            result = await cycle_fn()
            if result is not None:
                return result
        
        # 3. If max steps reached
        return f"Max steps ({max_steps}) reached without a final answer. Current history: {self.history[-2:]}"

    async def _run_agent_cycle(self, query: str):
        """Runs one full cycle (Thought, Act, Observe) and updates history."""
        # 1. Check for termination from the previous step
        if "Final Answer:" in self.history[-1]:
            return self.history[-1].split("Final Answer:")[1].strip()

        # 2. Act (Tool Execution)
        current_thought = self.history[-1]
        observation = await self._async_act(current_thought)
        self.history.append(observation)

        # 3. Next Thought (LLM.async_generate)
        context = {
            "question": query,
            "tools_string": "\n".join([f"- {name}: {tool.description}" for name, tool in self.tools.items()]),
            "tool_names": ", ".join(self.tools.keys()),
            "agent_history": "\n".join(self.history)
        }
        next_thought = await self.llm.async_generate(self.react_prompt.render(context))
        self.history.append(next_thought)
        
        return None

    # --- Asynchronous Loop (HARDENING: Resource Control) ---
    async def async_loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """
        Runs the main ReAct agent loop asynchronously, respecting max_steps (cost) and timeout (latency).
        """
        self.history = []
        
        try:
            # Use asyncio.wait_for to enforce the time limit
            if timeout is not None:
                return await asyncio.wait_for(
                    self._execute_stepped_loop(user_input, max_steps, lambda: self._run_agent_cycle(user_input)),
                    timeout=timeout
                )
            else:
                return await self._execute_stepped_loop(user_input, max_steps, lambda: self._run_agent_cycle(user_input))
                
        except asyncio.TimeoutError:
            # When timeout occurs, log the event and return a clear error message.
            return f"Agent failed: Timeout of {timeout} seconds reached after {len(self.history)//2} steps. Max cost averted."
        except GenAIFactoryError as e:
            return f"Agent failed due to internal error: {e}"
        except Exception as e:
            return f"Agent failed due to unhandled exception: {e}"

    # --- Synchronous Loop (Kept for contract but discouraged) ---
    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        """Synchronous loop implementation. Discouraged in production APIs."""
        # A proper implementation would run the async loop blocking the thread.
        try:
            return asyncio.run(self.async_loop(user_input, max_steps, timeout))
        except Exception as e:
            return f"Synchronous loop failed: {e}"
            
    # --- Remaining Abstract Methods (Placeholder for contract completion) ---
    def plan(self, user_input: str, context: Dict[str, Any]) -> str:
        # In ReAct, 'plan' is often integrated into the 'loop' thinking process.
        raise NotImplementedError("Plan is primarily handled inside the async_loop logic.")

    def act(self, action: str, **kwargs) -> Any:
        raise NotImplementedError("Use the asynchronous method '_async_act' instead.")

    def observe(self, observation: Any) -> None:
        # Observation is handled by appending to history list.
        pass