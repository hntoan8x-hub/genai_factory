🏭 **GenAI Factory: A Production-Grade Generative AI Development Framework**

---

## 1️⃣ OVERVIEW & POSITIONING

| Criteria | Description |
|-----------|-------------|
| **Core Role** | GenAI Factory is a **comprehensive MLOps framework and platform** designed to build, deploy, and operate Generative AI (GenAI) applications that are stable, secure, and scalable. |
| **Objective** | Transform the capabilities of **Large Language Models (LLMs)** into **production-grade API services**, fully decoupled from business logic and infrastructure layers. |
| **Key Differentiator** | The Factory **is not an AI model** (like GPT or Gemini), but a coordination system that enables models to: ① access knowledge (RAG), ② take actions (Tools/Agents), ③ comply with safety policies (Safety), and ④ be monitored (Monitoring/Logging). |
| **Typical Applications** | GenAI Assistant, Code Copilot, Customer Support Agent, Autonomous Data Agent, Content Generator. |

---

## 2️⃣ THREE-LAYER ARCHITECTURE

The project is structured into **three independent layers** to ensure modularity, maintainability, and extensibility.

### 🔹 **Layer 1: `shared_libs/` – Core Reusable GenAI Libraries**
These are foundational building blocks, independent of any specific application.

| Directory | Role | Example Components |
|------------|------|--------------------|
| **base/** | Interfaces: Define API contracts for all core components (LLM, Agent, Tool). | `base_llm.py`, `base_tool.py` |
| **atomic/** | Atomic Components: Concrete implementations of base interfaces. | `openai_llm.py`, `react_prompt.py`, `sql_tool.py` |
| **factory/** | Decoupling Layer: Instantiates atomic components from YAML configurations, allowing model/tool swapping without breaking application logic. | `llm_factory.py`, `agent_factory.py` |
| **orchestrator/** | High-Level Coordination: Manages complex multi-agent, memory lifecycle, and evaluation flows. | `genai_orchestrator.py`, `memory_orchestrator.py` |

---

### 🔹 **Layer 2: `domain_models/` – Business & Application Layer**
This layer defines **business-specific logic** for each application (e.g., `genai_assistant/`).

| Directory | Role | Example Components |
|------------|------|--------------------|
| **pipelines/** | Business Logic: Defines the end-to-end (E2E) workflow of the application. | `rag_pipeline.py`, `conversation_pipeline.py` |
| **services/** | Entry Points & Backend Logic: Define API endpoints (FastAPI/gRPC), connect user requests to pipelines, and handle training workflows. | `assistant_service.py`, `assistant_trainer.py` |
| **schemas/** | Data Contracts: Ensure data integrity between internal components and external systems. | `assistant_input_schema.py`, `tool_schema.py` |
| **monitoring/** & **logging/** | Metrics & Logging: Record performance, cost, and user interaction data. | `cost_monitor.py`, `telemetry_logger.py` |

---

### 🔹 **Layer 3: `infra/` – Infrastructure & Operations Layer**
Handles deployment, scaling, and operational monitoring of the system.

| Directory | Role | Example Components |
|------------|------|--------------------|
| **docker/** | Containerization: Package application and training jobs. | `Dockerfile.assistant`, `docker-compose.yml` |
| **k8s/** | Orchestration: Deploy and auto-scale workloads via Kubernetes. | `assistant-deployment.yaml`, `api-keys-secret.yaml` |
| **cicd/** | Automation: CI/CD pipelines for testing, building, and deployment. | `github-actions.yaml` |
| **monitoring/** & **logging/** | Ops Stack Configuration: Integrate Prometheus, Grafana, and Loki for metrics and centralized logging. | `prometheus.yaml`, `loki-config.yaml` |

---

## 3️⃣ DETAILED OPERATIONAL WORKFLOW

### 🔸 3.1. **Core Inference Flow**

1. **Request Ingestion** → User request received by `assistant_service.py` (POST API).
2. **Validation** → Input validated via `assistant_input_schema.py`.
3. **Safety Input Check** → `safety_pipeline.py` filters out malicious or prompt injection content.
4. **Orchestration & Routing** → `assistant_inference.py` identifies the request type and routes to the appropriate pipeline (`conversation_pipeline.py` or `rag_pipeline.py`).
5. **Pipeline Execution** →
   - **RAG Pipeline:** Query → Retrieve (Vector DB) → Rerank → Prompt Generation (`rag_prompt.py`).
   - **Agent Pipeline:** Agent (`react_agent.py`) selects Tool (`tool_service.py`) → Executes → Aggregates results.
6. **LLM Invocation** → Pipeline calls `llm_factory.py` to fetch the LLM instance and send the final prompt.
7. **Logging & Monitoring** → `cost_monitor.py`, `latency_monitor.py`, and `telemetry_logger.py` record tokens, response time, and trace logs.
8. **Safety Output Check** → `safety_pipeline.py` validates output for hallucinations or toxicity.
9. **Response Generation** → Standardized via `assistant_output_schema.py` and returned to the user.

---

### 🔸 3.2. **Development & Deployment (CI/CD Workflow)**

1. **Code Commit** → Developer pushes changes to Git.
2. **CI Build & Test (`github-actions.yaml`)** →
   - Run Unit & Integration Tests (`test_assistant_service.py`, `test_tools_integration.py`).
   - Perform Code Quality checks (Linter, Formatter).
   - Validate Infrastructure (`test_k8s_manifests.py`).
3. **Image Building** → If tests pass, build `Dockerfile.assistant` and `Dockerfile.trainer` → Push images to container registry.
4. **CD Deployment** → Deploy automatically to Kubernetes (`assistant-deployment.yaml`) using rollout strategies (Blue/Green, Canary).

---

### 🔸 3.3. **MLOps Lifecycle Management**

1. **Scheduled Retraining** → Triggered by `airflow_dag_retrain.py` or `cron_retrain.yaml`.
2. **Training Job** → Executes `assistant_trainer.py` using `Dockerfile.trainer`.
3. **Evaluation** → `evaluation_orchestrator.py` assesses model performance (`hallucination_eval.py`, `safety_eval.py`).
4. **Tracking & Metrics** → `mlflow_adapter.py` logs BLEU, ROUGE, training cost, and duration to MLflow.
5. **Model Promotion** → If performance meets thresholds, model/config is promoted for deployment.
6. **Drift Monitoring** → `drift_monitor.py` analyzes `interaction_logger.py` data to detect data drift and trigger retraining alerts.

---

📘 **Summary:** GenAI Factory is a **production-ready enterprise framework** that enables the creation, deployment, and governance of scalable, auditable, and autonomous Generative AI systems.

