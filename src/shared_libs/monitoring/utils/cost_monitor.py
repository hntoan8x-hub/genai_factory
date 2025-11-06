# src/shared_libs/monitoring/utils/cost_monitor.py (FINAL PRODUCTION CODE)

import logging
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import Gauge, Counter # Import Prometheus

# Hardening: Import Schema và Contract
from shared_libs.monitoring.configs.monitoring_schema import CostMonitorConfigSchema 
from shared_libs.monitoring.contracts.base_alert_adapter import BaseAlertAdapter 

logger = logging.getLogger(__name__)

# --- METRICS DEFINITION (PROMETHEUS HARDENING) ---
COST_GAUGE = Gauge(
    'genai_daily_cost_usd', 
    'Daily cumulative cost of LLM API usage in USD', 
    labelnames=['model_name']
)
TOKEN_COUNTER = Counter(
    'genai_total_tokens_used', 
    'Total number of prompt and completion tokens used', 
    labelnames=['model_name', 'type'] # type: input/output
)

class CostMonitor:
    """
    Tracks token usage and API billing, integrated with Prometheus and Alerting.
    """
    
    def __init__(self, config: Dict[str, Any], alert_adapter: BaseAlertAdapter):
        # Hardening 1: Khởi tạo Config từ Schema
        self.cost_conf = CostMonitorConfigSchema.model_validate(config)
        self.cost_threshold = self.cost_conf.cost_threshold_usd
        self.pricing_map = self.cost_conf.token_pricing_map
        
        # Hardening 2: Dependency Injection cho Alert Adapter
        self.alert_adapter = alert_adapter 
        self.current_daily_cost: Dict[str, float] = {} # Theo dõi chi phí theo model
        
        # Hardening 3: Cờ để tránh cảnh báo liên tục
        self._threshold_exceeded_flag = False

    def calculate_cost(self, tokens: int, model: str) -> float:
        """Helper function to calculate cost based on token pricing."""
        # Hardening: Sử dụng pricing map đã được validate
        rate = self.pricing_map.get(model, 0.000001) 
        return tokens * rate

    async def async_log_cost(self, 
                             request_id: str, 
                             input_tokens: int, 
                             output_tokens: int, 
                             model_name: str):
        """
        Records cost and token metrics to Prometheus and checks the alert threshold.
        """
        
        # 1. Tính toán chi phí
        total_tokens = input_tokens + output_tokens
        cost_usd = self.calculate_cost(total_tokens, model_name)
        
        # 2. Ghi metrics vào Prometheus Counter/Gauge
        TOKEN_COUNTER.labels(model_name=model_name, type='input').inc(input_tokens)
        TOKEN_COUNTER.labels(model_name=model_name, type='output').inc(output_tokens)
        
        # Cập nhật chi phí tích lũy theo model
        self.current_daily_cost[model_name] = self.current_daily_cost.get(model_name, 0.0) + cost_usd
        current_model_cost = self.current_daily_cost[model_name]
        
        COST_GAUGE.labels(model_name=model_name).set(current_model_cost)
        
        logger.info("Cost metrics updated to Prometheus.", extra={'request_id': request_id, 'cost': cost_usd})
        
        # 3. Kiểm tra Ngưỡng Cảnh báo (CRITICAL HARDENING)
        if current_model_cost > self.cost_threshold and not self._threshold_exceeded_flag:
            
            self._threshold_exceeded_flag = True # Set cờ
            
            message = (f"Model {model_name} exceeded the daily cost threshold of "
                       f"${self.cost_threshold:.2f}. Current Cost: ${current_model_cost:.2f}.")
            
            context = {
                "threshold_exceeded": True,
                "current_cost_usd": f"{current_model_cost:.4f}",
                "model": model_name
            }
            
            # Kích hoạt cảnh báo thông qua Adapter
            await self.alert_adapter.async_send_alert(
                message=message, 
                severity="CRITICAL", 
                context=context
            )
            logger.critical("DAILY COST ALERT: Threshold exceeded. Alert sent via Adapter.")