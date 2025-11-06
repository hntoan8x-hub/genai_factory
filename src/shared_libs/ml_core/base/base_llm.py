from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class BaseLLM(ABC):
    """
    Interface (hợp đồng API) cho các mô hình ngôn ngữ lớn (LLM).
    Các lớp cụ thể sẽ triển khai các phương thức này.
    """

    @abstractmethod
    def generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """
        Tạo văn bản dựa trên một prompt đầu vào.

        Args:
            prompt: Prompt đầu vào, có thể là một chuỗi hoặc một danh sách các tin nhắn.
            **kwargs: Các tham số bổ sung như temperature, max_tokens, v.v.

        Returns:
            Văn bản được tạo ra.
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Nhúng (embed) một đoạn văn bản vào một vector.

        Args:
            text: Đoạn văn bản cần nhúng.

        Returns:
            Một danh sách các float biểu thị vector nhúng.
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Thực hiện một phiên trò chuyện.

        Args:
            messages: Lịch sử trò chuyện dưới dạng danh sách các tin nhắn.
            **kwargs: Các tham số bổ sung.

        Returns:
            Tin nhắn phản hồi từ mô hình.
        """
        pass

# --- Asynchronous Methods (HARDENING ADDITIONS) ---
    @abstractmethod
    async def async_generate(self, prompt: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """
        Asynchronously generates text based on an input prompt.
        This is the preferred method for high-concurrency API services.
        """
        raise NotImplementedError

    @abstractmethod
    async def async_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Asynchronously conducts a chat session.
        """
        raise NotImplementedError

    @abstractmethod
    async def async_embed(self, text: str) -> List[float]:
        """
        Asynchronously embeds a piece of text into a vector.
        Useful for async RAG pipeline flows.
        """
        raise NotImplementedError