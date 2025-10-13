from typing import Dict, Any

class PromptConfig:
    """
    Configuration for prompt templates.

    This class stores the actual template strings and other variables
    needed to render prompts for different use cases.
    """
    FEW_SHOT_PROMPT_CONFIG: Dict[str, Any] = {
        "type": "fewshot",
        "template": "Analyze the following sentiment: {text}\n\nExamples:\n{examples}",
        "variables": ["text", "examples"],
    }

    REACT_PROMPT_CONFIG: Dict[str, Any] = {
        "type": "react",
        "template": "Answer the following question. You have access to the following tools: {tool_names_string}. "
                    "Use the format: 'Thought: <thought>\nAction: <tool_name>[<input>]\nObservation: <observation>'\n\n"
                    "Question: {question}",
        "variables": ["tool_names_string", "question"],
    }

    RAG_PROMPT_CONFIG: Dict[str, Any] = {
        "type": "rag",
        "template": "Based on the following context, answer the question.\n\nContext: {context}\n\nQuestion: {question}",
        "variables": ["context", "question"],
    }
