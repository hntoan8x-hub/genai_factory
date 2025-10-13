import yaml
import logging

from shared_libs.genai.factory.llm_factory import LLMFactory
from shared_libs.genai.factory.tool_factory import ToolFactory
from shared_libs.genai.orchestrator.genai_orchestrator import GenAIOrchestrator
from GenAI_Factory.domain_models.genai_assistant.pipelines.conversation_pipeline import ConversationPipeline
from GenAI_Factory.domain_models.genai_assistant.services.memory_service import MemoryService
from GenAI_Factory.domain_models.genai_assistant.services.assistant_inference import AssistantInference
from GenAI_Factory.domain_models.genai_assistant.services.assistant_service import AssistantService
from GenAI_Factory.domain_models.genai_assistant.logging.interaction_logger import log_interaction

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def load_config(filepath):
    """Loads a YAML configuration file."""
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def main():
    """Main function to run the GenAI assistant application."""
    print("Initializing GenAI Assistant...")
    
    # Load configurations
    llm_config = load_config("GenAI_Factory/domain_models/genai_assistant/configs/llm_config.yaml")
    tool_config = load_config("GenAI_Factory/domain_models/genai_assistant/configs/tool_config.yaml")
    assistant_config = load_config("GenAI_Factory/domain_models/genai_assistant/configs/assistant_config.yaml")

    # --- Use Factories to create components ---
    try:
        llm = LLMFactory.build_llm(llm_config["llm"])
        tools = [ToolFactory.build_tool(tool_cfg) for tool_cfg in tool_config["tools"]]
    except KeyError as e:
        logging.error(f"Failed to build components from config: Missing key {e}")
        return
    except NotImplementedError as e:
        logging.error(f"Failed to build component: {e}")
        return

    # --- Initialize Services and Pipelines ---
    memory_service = MemoryService()
    assistant_inference = AssistantInference(llm, memory_service, tools)
    assistant_service = AssistantService(assistant_config, assistant_inference, memory_service)
    
    print("GenAI Assistant is ready. Type 'exit' to quit.")
    
    user_id = "user-123" # Hardcoded user for this example

    while True:
        user_input = input(f"User({user_id}): ")
        if user_input.lower() == 'exit':
            break
        
        # Invoke the assistant service
        response = assistant_service.invoke({
            "user_id": user_id,
            "text": user_input
        })

        # Log the interaction
        log_interaction(user_id, {"text": user_input}, response)
        
        print(f"Assistant: {response['text']}")

if __name__ == "__main__":
    main()
