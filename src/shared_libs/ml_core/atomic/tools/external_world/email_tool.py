from typing import Any, Dict
from pydantic import BaseModel, EmailStr, Field
from shared_libs.genai.base.base_tool import BaseTool

class EmailInput(BaseModel):
    """Schema for the input of the Email Tool."""
    to: EmailStr = Field(..., description="The recipient's email address.")
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")

class EmailOutput(BaseModel):
    """Schema for the output of the Email Tool."""
    message: str = Field(..., description="A success or failure message.")
    success: bool = Field(..., description="Indicates if the email was successfully processed.")

class EmailTool(BaseTool):
    """
    A tool for sending and parsing emails.

    This tool allows an agent to interact with email systems, enabling it to
    send notifications or process incoming messages.
    """

    @property
    def input_schema(self) -> BaseModel:
        return EmailInput

    @property
    def output_schema(self) -> BaseModel:
        return EmailOutput

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates sending an email.

        Note: This is a placeholder. In a production environment, this would
        use an SMTP library or an email API client.

        Args:
            input_data (Dict[str, Any]): The input data containing 'to', 'subject', and 'body'.

        Returns:
            Dict[str, Any]: A dictionary with a success message.
        """
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            to = parsed_input.to
            subject = parsed_input.subject
            body = parsed_input.body
            
            print(f"Simulating email sent to: {to}")
            print(f"Subject: {subject}")
            print(f"Body: {body[:50]}...")
            
            return {"message": "Email sent successfully.", "success": True}

        except Exception as e:
            return {"message": f"Failed to send email: {e}", "success": False}
