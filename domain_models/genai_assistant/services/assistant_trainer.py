from typing import Dict, Any, List
from domain_models.genai_assistant.pipelines.training_pipeline import TrainingPipeline
from shared_libs.genai.configs.rlhf_config import rlhf_config

class AssistantTrainer:
    """
    Service for managing the training and fine-tuning of the assistant model.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the trainer service with a training pipeline.
        
        Args:
            config (Dict[str, Any]): The training configuration.
        """
        self.config = config
        self.training_pipeline = TrainingPipeline(config=config)
        
    def train_model(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Starts the training process for the assistant model.
        
        Args:
            dataset (List[Dict[str, Any]]): The training dataset.
            
        Returns:
            Dict[str, Any]: The results of the training and evaluation loop.
        """
        print("Starting training process...")
        try:
            results = self.training_pipeline.run(dataset)
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}
