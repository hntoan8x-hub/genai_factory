# GenAI_Factory/src/domain_models/genai_assistant/pipelines/2_agent_orchestration/risk_analysis_pipeline.py

import logging
from typing import Any, Dict, List, Optional
from shared_libs.base.base_llm import BaseLLM
from shared_libs.base.base_tool import BaseTool
from shared_libs.utils.exceptions import GenAIFactoryError, SecurityError
from domain_models.genai_assistant.services.tool_service import ToolService 
from domain_models.genai_assistant.schemas.conversation_schema import ConversationHistory # Cần cho Memory (nếu muốn)
from shared_libs.factory.agent_factory import AgentFactory # Cần để khởi tạo Agents theo tên
from shared_libs.configs.schemas import ReActAgentConfig # Cần để truyền config cho Manager

logger = logging.getLogger(__name__)

class RiskAnalysisPipeline:
    """
    Orchestrates a Hierarchical Multi-Agent workflow for complex financial risk analysis.
    This pipeline enforces a final Compliance Gate using the Critic Agent.
    Nó là một Composition Root cho các Domain Agent (RiskManager, Critic).
    """

    def __init__(self, llm_instance: BaseLLM, tool_service: ToolService, agent_config: Dict[str, Any]):
        self.llm = llm_instance
        self.tool_service = tool_service
        self.agent_config = agent_config
        self.max_loops = agent_config.get('max_agent_steps', 12) # Từ assistant_config.yaml

        # 1. Định nghĩa các Tools BẮT BUỘC cho Lead Agent (RiskManager)
        # Các Tools này phải được ToolService cung cấp và kiểm tra ACL
        required_tool_names = [
            "sql_query_executor", 
            "document_retriever", 
            "data_analyzer", 
            "statistical_visualizer", # Tool mới
            "web_search_tool"
        ]
        
        # 2. Lấy Tool Instances từ ToolService
        self.tools: List[BaseTool] = []
        for name in required_tool_names:
            try:
                # ToolService.get_tool() trả về instance BaseTool
                self.tools.append(self.tool_service.get_tool(name))
            except Exception as e:
                logger.warning(f"Required Tool '{name}' not available for Risk Pipeline: {e}")
                # Trong Production: Có thể raise lỗi nghiêm trọng nếu Tool cốt lõi thiếu

        # 3. Khởi tạo Agents (Sử dụng AgentFactory)
        # RiskManager Agent config (Giả định lấy từ assistant_config nếu có)
        manager_conf_model = ReActAgentConfig.model_validate(
            {"type": "risk_manager", "llm_config_key": "primary", "tools": required_tool_names, "max_loops": self.max_loops}
        )
        
        # 3a. Khởi tạo Lead Agent (RiskManager - sử dụng ReAct logic)
        self.manager_agent = AgentFactory().build(
            agent_name="risk_manager", 
            llm=self.llm, 
            tools=self.tools, 
            config_model=manager_conf_model
        )
        
        # 3b. Khởi tạo Critic Agent (Compliance Gate - chỉ cần LLM)
        self.critic_agent = AgentFactory().build(
            agent_name="compliance_critic", 
            llm=self.llm
        )


    async def async_run_with_role(self, query: str, user_role: str) -> Dict[str, Any]:
        """
        Runs the Risk Analysis Multi-Agent Orchestration Flow.
        Enforces Tool Access Control via ToolService inside the agent loop (thông qua user_role).
        """
        
        # MOCK POLICY: Thông tin chính sách được hardcode, trong thực tế sẽ lấy từ DocumentRetriever Tool
        MOCK_RISK_POLICY = (
            "Policy 2024: All credit risk scores above 0.85 must be manually reviewed. "
            "PII such as account numbers must NEVER be disclosed in the final report."
        )
        
        MAX_CRITIQUE_REATTEMPTS = 2
        final_response = None
        
        # Vòng lặp chính cho Phân tích và Phản biện
        for attempt in range(MAX_CRITIQUE_REATTEMPTS + 1):
            
            # --- 1. Thực thi Phân tích chính (Manager Agent Loop) ---
            logger.info(f"Running Manager Agent (Attempt {attempt+1})...")
            
            # Agent chạy loop của nó (ReAct), các lệnh gọi Tool sẽ tự động
            # được kiểm tra quyền bởi ToolService (sử dụng user_role).
            raw_analysis_output = await self.manager_agent.async_loop(
                user_input=query,
                max_steps=self.max_loops
            )
            
            # Kiểm tra lỗi thoát sớm
            if "Agent failed:" in raw_analysis_output or "Max steps" in raw_analysis_output:
                raise GenAIFactoryError(f"Risk Manager Agent loop failed: {raw_analysis_output}")

            # --- 2. Compliance Gate (Critic Agent Review) ---
            logger.info("Running Compliance Critic Gate...")
            
            # Critic Agent (Domain Agent) thực hiện chức năng Critique
            critique_result = await self.critic_agent.async_review(
                final_answer=raw_analysis_output,
                context={"query": query, "user_role": user_role},
                policy_documents=MOCK_RISK_POLICY
            )
            
            # --- 3. Quyết định (PASS/FAIL) ---
            if critique_result["status"] is True:
                final_response = raw_analysis_output
                logger.info("Compliance Gate PASSED.")
                break # Thoát khỏi vòng lặp Critique

            # Nếu FAIL
            if attempt < MAX_CRITIQUE_REATTEMPTS:
                logger.warning(f"Compliance Gate FAILED. Reason: {critique_result['critique']}. Re-attempting...")
                # Cung cấp phản hồi của Critic cho Manager Agent để sửa lỗi
                critique_feedback = (
                    f"CRITIQUE FAILED: You must revise your final answer because of the following compliance issue: "
                    f"{critique_result['critique']}. Generate a new Final Answer."
                )
                
                # Cập nhật context của Manager Agent với phản hồi của Critic
                self.manager_agent.observe({"role": "critic", "content": critique_feedback})
            else:
                # Nếu hết lần thử, trả về lỗi Compliance
                logger.critical(f"Compliance Gate FAILED after all re-attempts. Blocking final output.")
                final_response = (
                    f"COMPLIANCE VIOLATION DETECTED: The risk analysis failed to meet internal compliance standards. "
                    f"Reason: {critique_result['critique']}. The answer has been blocked."
                )
                break
                
        # --- 4. Trả về kết quả cuối cùng ---
        return {
            "response": final_response,
            "pipeline": "risk_analysis_agent",
            "metadata": {"critic_status": "PASS" if critique_result["status"] else "BLOCKED", "attempts": attempt + 1}
        }

    async def async_run(self, session_id: str, query: str) -> Dict[str, Any]:
        # Giữ lại phương thức base, nhưng raise lỗi vì nó không thể chạy mà không có user_role
        raise GenAIFactoryError("Risk Analysis Pipeline requires user_role for Tool Authorization. Use async_run_with_role.")