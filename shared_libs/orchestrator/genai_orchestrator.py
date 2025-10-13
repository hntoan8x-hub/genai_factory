from typing import Any, Dict, List
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_memory import BaseMemory
from shared_libs.base.base_evaluator import BaseEvaluator

class GenAIOrchestrator:
    """
    The central orchestrator for a single GenAI agentic loop.

    This class manages the lifecycle of a task, coordinating the agent's
    thought process (plan, act, observe) and integrating memory and evaluation.
    """

    def __init__(
        self,
        agent: BaseAgent,
        memory: BaseMemory,
        evaluators: List[BaseEvaluator] = None,
    ):
        """
        Initializes the GenAI Orchestrator.

        Args:
            agent (BaseAgent): The primary agent instance to be run.
            memory (BaseMemory): The memory component to manage context.
            evaluators (List[BaseEvaluator], optional): A list of evaluators to
                                                        assess agent outputs.
        """
        self.agent = agent
        self.memory = memory
        self.evaluators = evaluators if evaluators else []

    def run_task(self, query: str) -> Dict[str, Any]:
        """
        Executes a task from start to finish using the agentic loop.

        Args:
            query (str): The user's initial query or task.

        Returns:
            Dict[str, Any]: A dictionary containing the final output and evaluation results.
        """
        print(f"Starting GenAI orchestration for query: {query}")

        # The core agentic loop is delegated to the agent itself
        try:
            final_output = self.agent.loop(query)
            
            # Optionally store the final output in memory
            self.memory.store(session_id="default_session", data={"query": query, "response": final_output})

            # Run evaluation on the final output
            evaluation_results = self._run_evaluators(query, final_output)
            
            print("Orchestration complete.")
            return {
                "final_output": final_output,
                "evaluations": evaluation_results
            }

        except Exception as e:
            print(f"An error occurred during orchestration: {e}")
            return {
                "final_output": "An error occurred.",
                "evaluations": {}
            }

    def _run_evaluators(self, input_data: str, output: str) -> Dict[str, Any]:
        """
        Executes all configured evaluators on the agent's output.

        Args:
            input_data (str): The original input to the agent.
            output (str): The agent's generated output.

        Returns:
            Dict[str, Any]: A dictionary of evaluation results.
        """
        results = {}
        for evaluator in self.evaluators:
            eval_name = evaluator.__class__.__name__
            try:
                result = evaluator.evaluate(input_data=input_data, output=output, context={})
                results[eval_name] = result
            except Exception as e:
                print(f"Error running evaluator '{eval_name}': {e}")
                results[eval_name] = {"error": str(e)}
        return results
