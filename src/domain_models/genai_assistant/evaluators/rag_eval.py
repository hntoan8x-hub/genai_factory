# domain_models/genai_assistant/evaluators/rag_eval.py

import logging
from typing import Dict, Any, List
import asyncio
from shared_libs.utils.exceptions import GenAIFactoryError
# Import Schema Metric chuẩn
from domain_models.genai_assistant.schemas.eval_schema import EvaluationResult 

logger = logging.getLogger(__name__)

class RAGEvaluator:
    """
    Evaluates the performance of a Retrieval-Augmented Generation (RAG) pipeline.
    
    Metrics focus on retrieval precision/recall and how well the generation
    is grounded in the retrieved context, returning structured EvaluationResult Schemas.
    """
    
    def __init__(self, grounding_threshold: float = 0.5):
        """
        Initializes the RAG evaluator.
        
        Args:
            grounding_threshold (float): Ngưỡng tối thiểu cho điểm Grounding.
        """
        self.grounding_threshold = grounding_threshold

    def _calculate_retrieval(self, retrieved_docs: List[str], relevant_docs: List[str]) -> Dict[str, float]:
        """
        Calculates the Precision and Recall of retrieved documents. (Synchronous/Quick)
        """
        retrieved_set = set(retrieved_docs)
        relevant_set = set(relevant_docs)
        
        intersection = retrieved_set.intersection(relevant_set)
        
        precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
        recall = len(intersection) / len(relevant_set) if relevant_set else 0.0
        
        return {"precision": precision, "recall": recall}

    def _calculate_grounding(self, generated_output: str, retrieved_context: str) -> float:
        """
        Calculates a simple score for how well the generated output is grounded 
        in the provided context (e.g., keyword overlap).
        """
        output_tokens = set(generated_output.lower().split())
        context_tokens = set(retrieved_context.lower().split())
        
        # Grounding Score: Tỷ lệ từ đầu ra có trong ngữ cảnh truy xuất
        if not output_tokens:
             return 0.0
             
        overlap_score = len(output_tokens.intersection(context_tokens)) / len(output_tokens) 
        return overlap_score

    async def async_evaluate_rag(self, 
                                 generated_output: str, 
                                 retrieved_context: str, 
                                 relevant_docs: List[str], 
                                 retrieved_docs: List[str]) -> List[EvaluationResult]:
        """
        Runs a full suite of RAG-specific evaluations asynchronously. (HARDENING)
        
        Args:
            generated_output (str): The final output from the LLM.
            retrieved_context (str): The context (documents) actually fed to the LLM.
            relevant_docs (List[str]): Documents known to be relevant (Ground Truth).
            retrieved_docs (List[str]): Documents retrieved by the Retriever.

        Returns:
            List[EvaluationResult]: Structured evaluation scores for RAG.
        """
        logger.info("Starting RAG evaluation suite.")
        results: List[EvaluationResult] = []
        
        # 1. Retrieval Quality (Precision/Recall)
        retrieval_scores = self._calculate_retrieval(retrieved_docs, relevant_docs)
        
        results.append(EvaluationResult(
            evaluator="RAGEval", 
            metric_name="RetrievalPrecision", 
            score=retrieval_scores['precision'], 
            is_pass=retrieval_scores['precision'] > 0.6 # Giả định ngưỡng
        ))
        results.append(EvaluationResult(
            evaluator="RAGEval", 
            metric_name="RetrievalRecall", 
            score=retrieval_scores['recall'], 
            is_pass=retrieval_scores['recall'] > 0.6 # Giả định ngưỡng
        ))

        # 2. Grounding (Factual Consistency Check)
        grounding_score = self._calculate_grounding(generated_output, retrieved_context)
        is_grounded = grounding_score >= self.grounding_threshold
        
        results.append(EvaluationResult(
            evaluator="RAGEval", 
            metric_name="GroundingScore", 
            score=grounding_score, 
            is_pass=is_grounded, # So sánh với ngưỡng đã khởi tạo
            details={"is_grounded_flag": is_grounded, "context_size": len(retrieved_context)}
        ))
        
        # 3. (Placeholder for LLM-as-a-Judge on Answer Faithfulness)
        # Trong production, bạn sẽ gọi một LLM Judge async tại đây để đánh giá 'Answer Faithfulness' (Tính trung thực của câu trả lời so với ngữ cảnh).
        
        await asyncio.sleep(0.01) # Mô phỏng công việc bất đồng bộ
        
        logger.info("RAG evaluation completed.")
        return results