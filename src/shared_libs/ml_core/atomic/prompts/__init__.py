"""
This module contains concrete implementations of the BasePrompt interface
for various prompting techniques like few-shot, ReAct, and RAG.
"""

from .fewshot_prompt import FewShotPrompt
from .react_prompt import ReActPrompt
from .rag_prompt import RAGPrompt

__all__ = [
    "FewShotPrompt",
    "ReActPrompt",
    "RAGPrompt"
]
