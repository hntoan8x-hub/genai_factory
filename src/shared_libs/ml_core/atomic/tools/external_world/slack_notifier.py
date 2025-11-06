# shared_libs/atomic/tools/external_world/slack_notifier.py
import asyncio
import requests
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError
from concurrent.futures import ThreadPoolExecutor

class SlackInput(BaseModel):
    """Schema for the input of the Slack Notifier Tool."""
    channel: str = Field(..., description="The Slack channel ID or name (e.g., #mlops-alerts).")
    message: str = Field(..., description="The text content of the notification to send.")
    severity: Optional[str] = Field("info", description="The severity level of the alert (info, warning, critical).")

class SlackOutput(BaseModel):
    """Schema for the output of the Slack Notifier Tool."""
    response_message: str = Field(..., description="The response message from the Slack API.")
    success: bool = Field(..., description="Indicates if the notification was sent successfully.")

class SlackNotifier(BaseTool):
    """
    A hardened tool for sending asynchronous notifications or alerts to Slack channels.
    """

    @property
    def name(self) -> str:
        return "slack_notifier"

    @property
    def description(self) -> str:
        return "Send an important text message or alert to a designated Slack channel."

    @property
    def input_schema(self) -> BaseModel:
        return SlackInput
    
    @property
    def output_schema(self) -> BaseModel:
        return SlackOutput

    def __init__(self, slack_webhook_url: str):
        # Slack Webhook URL hoặc Token sẽ được cấu hình trong tool_config.yaml
        self.webhook_url = slack_webhook_url 
        self.executor = ThreadPoolExecutor(max_workers=3)

    def _execute_sync(self, validated_input: SlackInput) -> Dict[str, Any]:
        """Synchronous API call to Slack."""
        try:
            # Payload tùy chỉnh để dễ nhìn hơn
            payload = {
                "channel": validated_input.channel,
                "text": f"[{validated_input.severity.upper()}] New Notification: {validated_input.message}"
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            
            return SlackOutput(
                response_message=f"Message sent to {validated_input.channel}.",
                success=True
            ).model_dump()

        except requests.exceptions.RequestException as e:
            raise ToolExecutionError(f"Slack notification failed: {e.response.text if e.response is not None else str(e)}")
        except Exception as e:
            raise ToolExecutionError(f"Critical error during Slack execution: {e}")

    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously runs the tool by offloading blocking I/O."""
        validated_input = self.input_schema.model_validate(input_data)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._execute_sync, validated_input)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper."""
        return asyncio.run(self.async_run(input_data))