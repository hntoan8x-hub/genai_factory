# domain_models/genai_assistant/agents/compliance_critic_agent.py

from typing import Any, Dict, List, Optional, Union
from shared_libs.base.base_agent import BaseAgent
from shared_libs.base.base_llm import BaseLLM
from shared_libs.utils.exceptions import SecurityError, GenAIFactoryError
import asyncio

class ComplianceCriticAgent(BaseAgent):
    """
    A specialized agent that acts as a quality gate, reviewing the final output 
    of a task for compliance, PII exposure, and safety against internal policies.
    (CRITICAL HARDENING COMPONENT for high-compliance environments).
    """

    @property
    def name(self) -> str:
        return "compliance_critic_agent"

    @property
    def description(self) -> str:
        return "Reviews final risk analysis reports for compliance with internal policies, PII violations, and regulatory alignment. Can reject non-compliant answers."

    def __init__(self, llm: BaseLLM):
        self.llm = llm
        
    async def async_review(self, final_answer: str, context: Dict[str, Any], policy_documents: str) -> Dict[str, Union[str, bool]]:
        """
        Asynchronously performs a critical review of the final output.

        Args:
            final_answer (str): The proposed final answer from the manager agent.
            context (Dict[str, Any]): General task context.
            policy_documents (str): Retrieved policy documents for compliance reference.

        Returns:
            Dict: {'status': 'PASS'/'FAIL', 'critique': str}
        """
        
        # 1. Chuẩn bị System Prompt cho Critic (Hardening Logic)
        review_prompt = f"""
        TASK: CRITIQUE & COMPLIANCE CHECK.
        
        Your role is the Compliance Auditor. You must strictly check the 'Final Answer' against the 'Internal Policies' and the general principle of PII and security compliance.
        
        INTERNAL POLICIES (Reference Material):
        ---
        {policy_documents}
        ---
        
        FINAL ANSWER TO BE CRITIQUED:
        ---
        {final_answer}
        ---

        EVALUATION CRITERIA:
        1. COMPLIANCE: Does the answer contradict or violate any policy mentioned above?
        2. PII/SECURITY: Does the answer reveal any actual PII (e.g., full names, specific IDs, account numbers) not already masked, or suggest unauthorized actions (e.g., DELETE/UPDATE database)?
        3. CLARITY: Is the answer clearly supported by the analysis context?

        If the answer is safe and compliant, respond with: <CRITIQUE_RESULT>PASS</CRITIQUE_RESULT>.
        If it fails, provide a detailed reason and suggest a fix, then respond with: <CRITIQUE_RESULT>FAIL: [Detailed Reason]</CRITIQUE_RESULT>
        """
        
        # 2. Gọi LLM (Async) để thực hiện Critique
        try:
            critique_response = await self.llm.async_generate(review_prompt, temperature=0.0)
            
            if "<CRITIQUE_RESULT>PASS</CRITIQUE_RESULT>" in critique_response:
                return {"status": True, "critique": "Compliant and safe."}
            else:
                critique_reason = critique_response.split("<CRITIQUE_RESULT>FAIL:")[1].split("</CRITIQUE_RESULT>")[0].strip() if "<CRITIQUE_RESULT>FAIL:" in critique_response else "Compliance check failed without detailed reason."
                return {"status": False, "critique": critique_reason}

        except Exception as e:
            raise GenAIFactoryError(f"Critic Agent failed to generate critique: {e}")

    # Các phương thức BaseAgent khác không cần thiết cho Critic (vì nó không tự khởi tạo loop)
    # ... (Giữ nguyên các phương thức base không cần thiết để không làm đầy code)

    def loop(self, user_input: str, max_steps: int = 10, timeout: Optional[int] = None) -> str:
        raise NotImplementedError("Critic Agent is managed externally by the Orchestrator.")
    
    #... Tương tự cho các methods còn lại của BaseAgent (plan, act, observe)