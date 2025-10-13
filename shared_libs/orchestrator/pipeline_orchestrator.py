from typing import Any, Dict
from .genai_orchestrator import GenAIOrchestrator

class PipelineOrchestrator:
    """
    Orchestrator for a multi-stage pipeline, composing GenAI with other
    modules like NLP or Computer Vision (CV).

    This class represents a higher level of orchestration, managing the flow of
    data between different processing stages.
    """

    def __init__(self, genai_orchestrator: GenAIOrchestrator, nlp_module: Any = None, cv_module: Any = None):
        """
        Initializes the Pipeline Orchestrator.

        Args:
            genai_orchestrator (GenAIOrchestrator): The GenAI component of the pipeline.
            nlp_module (Any, optional): A placeholder for an NLP module.
            cv_module (Any, optional): A placeholder for a Computer Vision module.
        """
        self.genai_orchestrator = genai_orchestrator
        self.nlp_module = nlp_module
        self.cv_module = cv_module

    def run_pipeline(self, input_data: Any) -> Dict[str, Any]:
        """
        Executes the entire pipeline.

        This method simulates a workflow where input data is processed by
        different modules in sequence. For example:
        1. NLP module processes text input.
        2. GenAI module generates a response.
        3. A final post-processing step is performed.

        Args:
            input_data (Any): The initial input to the pipeline.

        Returns:
            Dict[str, Any]: The final result of the entire pipeline.
        """
        print("Starting pipeline orchestration...")
        
        processed_data = input_data
        
        # Stage 1: Pre-processing with other modules (e.g., NLP)
        if self.nlp_module:
            print("Running NLP pre-processing stage...")
            processed_data = self.nlp_module.process(processed_data)
        
        # Stage 2: GenAI core processing
        print("Running GenAI core processing stage...")
        genai_result = self.genai_orchestrator.run_task(processed_data)
        
        # Stage 3: Post-processing (e.g., with CV)
        if self.cv_module:
            print("Running CV post-processing stage...")
            final_output = self.cv_module.enhance_output(genai_result["final_output"])
            genai_result["final_output"] = final_output

        print("Pipeline orchestration complete.")
        return genai_result
