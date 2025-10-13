from typing import Dict, Any, List
from shared_libs.genai.atomic.evaluators.coherence_eval import CoherenceEvaluator
from shared_libs.genai.factory.llm_factory import LLMFactory

# Note: A simple placeholder for BLEU/ROUGE score calculation
def calculate_bleu_score(reference: str, candidate: str) -> float:
    """Calculates a mock BLEU score for demonstration purposes."""
    ref_tokens = set(reference.lower().split())
    cand_tokens = set(candidate.lower().split())
    overlap = len(ref_tokens.intersection(cand_tokens))
    return (overlap / len(cand_tokens)) if cand_tokens else 0.0

def calculate_rouge_score(reference: str, candidate: str) -> float:
    """Calculates a mock ROUGE score for demonstration purposes."""
    ref_tokens = set(reference.lower().split())
    cand_tokens = set(candidate.lower().split())
    overlap = len(ref_tokens.intersection(cand_tokens))
    return (overlap / len(ref_tokens)) if ref_tokens else 0.0

class AssistantEvaluator:
    """
    Evaluates the quality of assistant responses using metrics like BLEU, ROUGE,
    and LLM-as-a-Judge.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMFactory.build(config.get("llm_judge", {}))
        self.coherence_evaluator = CoherenceEvaluator()

    def evaluate_response(self, input: str, output: str, reference: str) -> Dict[str, Any]:
        """
        Runs a suite of evaluations on a generated response.

        Args:
            input (str): The original user query.
            output (str): The assistant's generated response.
            reference (str): A golden reference response for comparison.

        Returns:
            Dict[str, Any]: A dictionary of evaluation scores.
        """
        scores = {}
        scores["bleu_score"] = calculate_bleu_score(reference, output)
        scores["rouge_score"] = calculate_rouge_score(reference, output)
        
        # Use LLM-as-a-Judge for a qualitative evaluation
        llm_judge_result = self.coherence_evaluator.evaluate(input, output)
        scores["llm_judge_score"] = llm_judge_result.get("score")
        scores["llm_judge_reasoning"] = llm_judge_result.get("details")

        return scores
