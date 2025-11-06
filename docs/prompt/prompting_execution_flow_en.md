📘 **GENAI FACTORY – PROMPTING EXECUTION FLOW**

---

### 🎯 OBJECTIVE
Understanding the Prompting process is the key to controlling and optimizing LLM outputs. In **GenAI Factory**, this process is designed using a **Factory Pattern** and **Abstraction Layer**, ensuring modularity, scalability, and reusability across all pipelines.

---

## ⚙️ 1. FOUNDATION: BASEPROMPT INTERFACE (PROMPT CONTRACT)
Just like `BaseLLM` defines an interface for language models, `BasePrompt` defines a standard contract for all prompt templates. This allows the system to flexibly switch between different prompting strategies (RAG, Few-Shot, Chain-of-Thought, etc.) without changing the pipeline logic.

| **Component** | **Technical Role** | **Core Methods** |
|----------------|--------------------|------------------|
| **BasePrompt** | Abstraction Layer – defines programming interface for prompt templates. | `render(context: Dict[str, Any])` |
| **render()** | Rendering – fills template variables with context to produce a final prompt string. | Input: `{ 'context': '...', 'query': '...' }` → Output: Complete prompt string. |
| **validate()** | Validation – ensures that all required variables exist in the context dictionary. | Prevents runtime errors before sending API requests to LLM. |

🔹 **Value:** The `RAGPipeline` only calls `rag_prompt.render(context)` and gets a safe, validated prompt without worrying about its internal structure.

---

## 🧠 2. CLASSIFICATION: MAIN PROMPTING STRATEGIES
In **GenAI Factory**, there are three main prompting strategies, each implemented via a subclass derived from `BasePrompt`.

### 🧩 A. RAGPrompt (Context Augmentation)
**File:** `rag_prompt.py`

- **Purpose:** Ground LLM answers with factual information retrieved from Vector DB.  
- **Input Variables:**
  - `instruction`: System instruction (e.g., *“You are a compliance officer. Answer based ONLY on the documents below.”*)
  - `retrieved_docs`: List of retrieved text chunks.
  - `query`: Original user question.

**render() mechanism:**
```python
prompt_parts = [
    self.instruction,
    "---",
    "Retrieved Documents:",
    retrieved_docs_str,
    "---",
    f"Question: {context['query']}",
    "Answer:"
]
return "\n".join(prompt_parts)
```
---

### 🧩 B. FewShotPrompt (Learning by Example)
**File:** `fewshot_prompt.py`

- **Purpose:** Guide the LLM to perform a task by providing in-context examples (In-Context Learning).  
- **Input Variables:**
  - `instruction`: Task description (e.g., *“Classify the following sentiment as Positive, Negative, or Neutral.”*)
  - `examples`: List of example Input/Output pairs.
  - `input`: New data to be processed.

**render() mechanism:** Combines `instruction + examples + new_input` into one complete prompt.

---

### 🧩 C. ReActPrompt (Reasoning and Acting)
**File:** `react_prompt.py`

- **Purpose:** Instructs the LLM to follow a *Thought → Action → Observation* reasoning cycle to solve complex tasks using tools.  
- **Input Variables:**
  - `tools_string`: Description of available tools and their I/O schema.
  - `tool_names`: List of tools (e.g., [Calculator, SQLTool, RetrieverTool]).
  - `agent_history`: Log of previous Thought/Action/Observation steps.
  - `question`: Original query.

**render() mechanism:** Uses a predefined template containing the required output structure (e.g., *Thought: ... → Action: ... → Action Input: ...*), ensuring consistent formatting for tool parsing and activation.

---

## 🔄 3. PROMPT EXECUTION FLOW
The runtime execution of a Prompt (e.g., `RAGPrompt`) follows a six-step pipeline:

| **Step** | **Component** | **Action** | **Purpose** |
|-----------|----------------|-------------|--------------|
| **1. Configuration** | `prompt_config.py` | Define template strings and variable names. | Separate template from logic. |
| **2. Initialization** | `RAGPipeline` | Initialize specific prompt object: `RAGPrompt(instruction="...")`. | Create a dedicated prompt instance. |
| **3. Context Collection** | `RAGPipeline` | Retrieve user query and `retrieved_docs` from Vector DB. | Build the context dictionary. |
| **4. Validation** | `RAGPrompt.validate()` | Check all required context keys exist. | Prevent missing-variable errors before token use. |
| **5. Rendering** | `RAGPrompt.render(context)` | Fill the template with context data. | Produce final complete prompt string. |
| **6. LLM Generation** | `LLMWrapper.async_generate(final_prompt)` | Send prompt to LLM and generate output. | Produce grounded, accurate response. |

---

## 🧩 SUMMARY
The **Prompting Flow** in GenAI Factory acts as a **Context Injection Pipeline** — where structured information (instructions, examples, and documents) is injected into the LLM input.

This approach ensures that every LLM call:

✅ Has complete and relevant context.  
✅ Produces outputs that follow strict formatting and logic.  
✅ Can scale easily across multiple prompting strategies (RAG, Few-Shot, ReAct) without breaking core system behavior.

