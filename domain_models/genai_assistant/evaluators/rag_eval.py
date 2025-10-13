from typing import Dict, Any, List

class RAGEvaluator:
    """
    Evaluates the performance of a Retrieval-Augmented Generation (RAG) pipeline.

    Metrics include retrieval precision, recall, and how well the generation
    is grounded in the retrieved context.
    """
    def __init__(self):
        # No specific config needed for this simplified version
        pass

    def evaluate_retrieval(self, retrieved_docs: List[str], relevant_docs: List[str]) -> Dict[str, float]:
        """
        Evaluates the precision and recall of retrieved documents.

        Args:
            retrieved_docs (List[str]): The documents retrieved by the RAG pipeline.
            relevant_docs (List[str]): The documents that are known to be relevant.

        Returns:
            Dict[str, float]: A dictionary containing precision and recall scores.
        """
        retrieved_set = set(retrieved_docs)
        relevant_set = set(relevant_docs)
        
        intersection = retrieved_set.intersection(relevant_set)
        
        precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
        recall = len(intersection) / len(relevant_set) if relevant_set else 0.0
        
        return {"retrieval_precision": precision, "retrieval_recall": recall}

    def evaluate_grounding(self, generated_output: str, retrieved_context: str) -> Dict[str, Any]:
        """
        Evaluates how well the generated output is grounded in the provided context.

        Args:
            generated_output (str): The output from the LLM.
            retrieved_context (str): The context used by the LLM.

        Returns:
            Dict[str, Any]: A dictionary containing a grounding score and reasoning.
        """
        # A simple check for keyword overlap as a proxy for grounding
        output_tokens = set(generated_output.lower().split())
        context_tokens = set(retrieved_context.lower().split())
        
        overlap_score = len(output_tokens.intersection(context_tokens)) / len(output_tokens) if output_tokens else 0.0
        
        is_grounded = overlap_score > 0.5 # A simple threshold
        
        return {
            "grounding_score": overlap_score,
            "is_grounded": is_grounded,
            "reasoning": "Output shares common keywords with the retrieved context." if is_grounded else "Output does not appear to be well-grounded in the context."
        }
