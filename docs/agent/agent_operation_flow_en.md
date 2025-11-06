📘 **GENAI FACTORY – AGENT OPERATION FLOW (REACT LOOP)**

---

### 🎯 OBJECTIVE
Understanding how an **Agent** operates allows you to gain full control over your GenAI system’s problem-solving capabilities.  
In **GenAI Factory**, the Agent follows the **ReAct (Reasoning and Acting)** model — enabling the LLM not only to think but also to **interact with the external world** through **Tools**.

---

## ⚙️ 1. FOUNDATION: REACT LOOP (THOUGHT → ACTION → OBSERVATION)
The **Agent (ReActAgent)** operates through a continuous **decision-making loop**, defined in `loop()` (base_agent.py) and implemented in detail in `react_agent.py`.

| **Stage** | **Role** | **Function (LLM/Agent)** | **LLM Output (Key Insight)** |
|------------|-----------|---------------------------|-------------------------------|
| **1. Thought** | LLM Reasoning | The LLM analyzes the user query, available tools, and history to decide the next step. | Thought: “I need to retrieve data from the database.” |
| **2. Action** | Agent Execution | The Agent parses the LLM output, extracts the tool name and parameters, and calls the tool’s `run()` method. | Action: `SQLTool(query='SELECT Q3_Revenue')` |
| **3. Observation** | Tool Result | The Tool executes and returns results (e.g., data, errors, or messages). The Agent logs this result. | Observation: “Database returned 10 million USD.” |
| **Loop** | State Update | The observation is appended to `self.history` and passed back to the LLM in the next prompt. | The process repeats from Thought. |
| **Final Answer** | Task Completion | When the LLM determines sufficient information is gathered, it stops the loop and returns the final answer. | Final Answer: “Q3 revenue is 10 million USD.” |

---

## 🧠 2. ARCHITECTURAL COMPONENTS
For the ReAct loop to function, the Agent coordinates **four core components**, all built upon standardized interfaces:

### 🔹 A. Agent (The Orchestrator)
- **Class:** `ReActAgent` inheriting from `BaseAgent` (`base_agent.py`).  
- **Function:** Contains loop logic (`loop`), manages history (`self.history`), and parses LLM outputs to trigger tools.  
- **Configuration:** Initialized with a `BaseLLM` (the brain) and a list of `BaseTool` (tools).

### 🔹 B. LLM (The Brain)
- **Class:** `OpenAILLM` or `HuggingFaceLLM` inheriting from `BaseLLM` (`base_llm.py`).  
- **Function:** Provides reasoning ability. It receives the prompt (question, history, and tool descriptions) and returns the next step (Thought or Action).

### 🔹 C. Prompt (The Communication Language)
- **Class:** `ReActPrompt` inheriting from `BasePrompt` (`react_prompt.py`).  
- **Function:** Enforces a strict format (*Thought: ...\nAction: ...*). If the LLM does not comply, the Agent cannot parse it (or must include an error-correction mechanism).

### 🔹 D. Tool (The Hands)
- **Class:** Specific tools such as `SQLTool`, `CalculatorTool` inheriting from `BaseTool` (`base_tool.py`).  
- **Function:** Provides real-world interaction (Database, API, File System). The Agent simply calls `tool.run(input_data)`.

---

## 🔄 3. DETAILED ANALYSIS: THE `loop()` METHOD
The `loop(self, query: str)` method is the **heart of the Agent**, governing how components interact during execution:

```python
self.history = []
# 1️⃣ Initialize context: user query + tool descriptions
context = self.react_prompt.render({...})

# 2️⃣ Main Loop (up to max_loops)
for _ in range(self.max_loops):
    # 3.1 Trigger Reasoning (Thought/Action)
    current_thought = self.llm.generate(context)
    self.history.append(current_thought)

    # 3.2 Check Stopping Condition
    if "Final Answer:" in current_thought:
        return current_thought.split("Final Answer:")[1].strip()

    # 3.3 Execute Action
    action_name, action_input = self._parse_action(current_thought)
    observation = self.tools[action_name].run(action_input)

    # 3.4 Record Observation
    self.history.append(f"Observation: {observation}")

    # 3.5 Update Context for Next Iteration
    context = self.react_prompt.render({
        "agent_history": "\n".join(self.history),
        ...
    })
```

---

## 🧩 CONCLUSION
**An Agent is not an LLM.** It is a **state management system** that uses the LLM as a **control logic engine**.  

By alternating control between **LLM (thinking)** and **Tool (acting)**, the Agent enables the system to:

✅ Solve multi-step reasoning problems.  
✅ Automate complex workflows.  
✅ Overcome the limitations of LLMs that only generate text.

> 💡 **Agent = Brain + Memory + Tools + Logic Loop → Autonomous Intelligence.**

