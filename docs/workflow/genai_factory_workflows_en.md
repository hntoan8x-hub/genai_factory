📘 **GENAI FACTORY – OPERATIONAL & MLOPS HARDENING ECOSYSTEM**

---

### 🎯 OBJECTIVE
**GenAI Factory** functions as a dynamic ecosystem consisting of two primary cycles:

1️⃣ **Operational & Inference Workflow** – the real-time system that processes user requests efficiently and safely.  
2️⃣ **Model Governance & Retraining (MLOps Workflow)** – ensuring models and knowledge bases stay accurate, up-to-date, and optimized.

---

## 🧠 I. CYCLE 1: INFERENCE WORKFLOW
This is the real-time operational loop that leverages **Async I/O** and **Resilience Hardening** techniques.

| **Stage** | **Technical Action** | **Core Components** | **Hardening Value** |
|------------|----------------------|----------------------|----------------------|
| **1. Ingestion & Security** | Request Flow Start: Incoming API request → Rate Limiting & Input Safety checks. | `assistant_service.py`, `safety_pipeline.py` | 🛡️ Anti-DoW/Abuse: Prevents denial-of-wallet attacks or malicious requests. |
| **2. Core Orchestration** | Routing: `AssistantInferenceService` selects the correct pipeline (RAG or Agent). Entire flow runs asynchronously. | `assistant_inference.py` | ⚡ Performance: Async I/O ensures no blocking from slow I/O calls. |
| **3. Knowledge Retrieval (RAG/Agent Logic)** | RAG: Call RAG Tool → Vector DB → render RAGPrompt.  
Agent: Call `async_loop` → LLM → Thought/Action → Tool (`tool.async_run`). | `rag_pipeline.py`, `react_agent.py`, `BaseTool` | 🔁 Reliability: `async_run` + Retry/Fallback logic prevents system failures from API or I/O downtime. |
| **4. Generation (Response Creation)** | Final prompt sent to the LLM Wrapper for inference. | `OpenAILLM` (extends `BaseLLMWrapper`) | 🔄 Resilience: Automatic handling of 429/5xx errors via Retry/Backoff without crashing. |
| **5. Monitoring & Logging** | Track token usage, latency, and operational metrics. | `CostMonitor`, `LatencyMonitor`, `TracingUtils` | 💰 Cost Control: Enables proactive token budgeting and latency optimization. |
| **6. Output Safety** | Validate LLM output for toxicity, bias, and PII leaks. | `safety_pipeline.py` | ✅ Compliance: Ensures sensitive or restricted data is sanitized before response delivery. |

---

## 🧪 II. CYCLE 2: MODEL GOVERNANCE & RETRAINING (MLOPS WORKFLOW)
This cycle maintains long-term accuracy, performance, and governance for both models and RAG knowledge indices.

| **Stage** | **Technical Action** | **Core Components** | **MLOps Objective** |
|------------|----------------------|----------------------|----------------------|
| **1. Job Trigger** | Scheduled retraining jobs triggered via Airflow DAG or Kubernetes CronJob. | `infra/scheduler/` | 🔁 Automation: Eliminates manual triggering and ensures consistent retraining. |
| **2. Training Execution** | `assistant_trainer.py` performs Fine-Tuning. `mlflow_adapter.py` logs parameters and artifacts. | `assistant_trainer.py`, `mlflow_adapter.py` | 🧩 Reproducibility: Every model version can be tracked and reproduced. |
| **3. Quality Evaluation** | Run evaluation orchestrator with `HallucinationEval`, `SafetyEval`, etc. | `evaluation_orchestrator.py`, `base_evaluator.py` | 🧠 Governance: Ensures models meet accuracy, compliance, and safety standards. |
| **4. Knowledge Update (RAG Indexing)** | Rebuild Vector Index using LLM Wrapper `.embed()` method. | `LLM Wrapper`, `Vector DB` | 🔄 Refresh: Keeps RAG knowledge (Policies, Reports, etc.) synchronized with latest versions. |
| **5. Drift Monitoring** | Analyze logs for user behavior or model performance changes. | `drift_monitor.py`, `logging_utils.py` | ⚠️ Prevention: Detects model decay early and triggers retraining automatically. |

---

### 🧭 CONCLUSION
**GenAI Factory** operates as a **closed-loop AI ecosystem**, where:

- **Inference Cycle** → generates **observations & metrics** for monitoring.  
- **MLOps Cycle** → leverages those insights to **retrain, fine-tune, and improve models**.  

> 💡 **Inference → Monitoring → Retraining → Improved Model → Back to Inference** – a complete and self-sustaining intelligence loop.

