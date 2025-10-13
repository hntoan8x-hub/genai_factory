🏭 **GenAI Factory: Khung Phát Triển AI Tạo Sinh Cấp Độ Sản Xuất**

---

## 1️⃣ TỔNG QUAN & ĐỊNH VỊ (OVERVIEW & POSITIONING)

| Tiêu chí | Mô tả |
|-----------|--------|
| **Vai trò cốt lõi** | GenAI Factory là một **Khung phần mềm (Framework)** và **Nền tảng MLOps toàn diện**, được thiết kế để xây dựng, triển khai và vận hành các ứng dụng AI Tạo sinh (GenAI) ổn định, an toàn và có khả năng mở rộng. |
| **Mục tiêu** | Chuyển đổi khả năng của **Mô hình Ngôn ngữ Lớn (LLM)** thành **Dịch vụ API cấp độ sản xuất (Production-Grade API Service)**, tách biệt logic GenAI khỏi logic nghiệp vụ và hạ tầng. |
| **Sự khác biệt** | Factory **không phải là một mô hình AI** (như GPT, Gemini) mà là hệ thống điều phối giúp các mô hình đó: ① Truy cập kiến thức (RAG), ② Thực hiện hành động (Tools/Agents), ③ Tuân thủ quy tắc (Safety), và ④ Được giám sát (Monitoring/Logging). |
| **Ứng dụng điển hình** | GenAI Assistant, Code Copilot, Customer Support Agent, Autonomous Data Agent, Content Generator. |

---

## 2️⃣ KIẾN TRÚC BA LỚP (THREE-LAYER ARCHITECTURE)

Hệ thống được tổ chức theo **3 lớp độc lập**, đảm bảo tính mô-đun, khả năng mở rộng và dễ bảo trì.

### 🔹 **Layer 1: `shared_libs/` – Thư viện tái sử dụng cốt lõi GenAI**
Đây là nơi chứa các khối xây dựng nền tảng, độc lập với ứng dụng cụ thể.

| Thư mục | Vai trò | Ví dụ cấu phần |
|----------|----------|----------------|
| **base/** | Interfaces (Giao diện): Định nghĩa hợp đồng API cho tất cả các thành phần LLM, Agent, Tool. | `base_llm.py`, `base_tool.py` |
| **atomic/** | Thành phần cơ bản: Các triển khai cụ thể của giao diện. | `openai_llm.py`, `react_prompt.py`, `sql_tool.py` |
| **factory/** | Decoupling (Khử khớp nối): Khởi tạo các thành phần Atomic từ cấu hình YAML để thay đổi dễ dàng mà không ảnh hưởng đến logic ứng dụng. | `llm_factory.py`, `agent_factory.py` |
| **orchestrator/** | Điều phối cấp cao: Quản lý các luồng phức tạp (Multi-Agent, Memory Lifecycle, Evaluation Flow). | `genai_orchestrator.py`, `memory_orchestrator.py` |

---

### 🔹 **Layer 2: `domain_models/` – Lớp Ứng dụng & Nghiệp vụ**
Đây là nơi định nghĩa **logic nghiệp vụ cụ thể** cho từng ứng dụng (ví dụ: `genai_assistant/`).

| Thư mục | Vai trò | Ví dụ cấu phần |
|----------|----------|----------------|
| **pipelines/** | Logic nghiệp vụ: Định nghĩa luồng công việc End-to-End (E2E). | `rag_pipeline.py`, `conversation_pipeline.py` |
| **services/** | Entry Points & Backend Logic: Xây dựng API (FastAPI/gRPC), kết nối Request ↔ Pipeline, và logic training. | `assistant_service.py`, `assistant_trainer.py` |
| **schemas/** | Data Contracts: Đảm bảo toàn vẹn dữ liệu giữa các thành phần và hệ thống bên ngoài. | `assistant_input_schema.py`, `tool_schema.py` |
| **monitoring/** & **logging/** | Độ đo & Ghi nhật ký: Ghi lại hiệu suất, chi phí, và tương tác người dùng. | `cost_monitor.py`, `telemetry_logger.py` |

---

### 🔹 **Layer 3: `infra/` – Hạ tầng & Vận hành**
Quản lý việc triển khai, mở rộng và giám sát hệ thống.

| Thư mục | Vai trò | Ví dụ cấu phần |
|----------|----------|----------------|
| **docker/** | Containerization: Đóng gói ứng dụng và job training. | `Dockerfile.assistant`, `docker-compose.yml` |
| **k8s/** | Orchestration: Triển khai và tự động mở rộng (Autoscaling). | `assistant-deployment.yaml`, `api-keys-secret.yaml` |
| **cicd/** | Automation: Quy trình CI/CD tự động kiểm thử, xây dựng và triển khai. | `github-actions.yaml` |
| **monitoring/** & **logging/** | Stack Ops: Thiết lập Prometheus, Grafana, Loki cho giám sát & log tập trung. | `prometheus.yaml`, `loki-config.yaml` |

---

## 3️⃣ LUỒNG VẬN HÀNH CHI TIẾT (DETAILED OPERATING WORKFLOW)

### 🔸 3.1. **Luồng Thực thi Cốt lõi (Inference Flow)**

1. **Request Ingestion** → Yêu cầu được tiếp nhận tại `assistant_service.py` qua API POST.
2. **Validation** → Kiểm tra dữ liệu bằng `assistant_input_schema.py`.
3. **Safety Input Check** → `safety_pipeline.py` ngăn Prompt Injection hoặc nội dung độc hại.
4. **Orchestration & Routing** → `assistant_inference.py` xác định loại yêu cầu, chọn pipeline phù hợp (`conversation_pipeline.py` hoặc `rag_pipeline.py`).
5. **Pipeline Execution** →
   - **RAG Pipeline:** Truy vấn → Retrieval (Vector DB) → Reranking → Tạo Prompt (`rag_prompt.py`).
   - **Agent Pipeline:** Agent (`react_agent.py`) chọn Tool (`tool_service.py`) → Thực thi → Tổng hợp kết quả.
6. **LLM Call** → `llm_factory.py` lấy instance mô hình và gửi Prompt.
7. **Logging & Monitoring** → `cost_monitor.py`, `latency_monitor.py`, `telemetry_logger.py` ghi lại token, thời gian, trace.
8. **Safety Output Check** → `safety_pipeline.py` kiểm duyệt đầu ra (hallucination, toxicity).
9. **Response Generation** → Chuẩn hóa phản hồi bằng `assistant_output_schema.py` và gửi kết quả.

---

### 🔸 3.2. **Luồng Phát triển & Triển khai (CI/CD Workflow)**

1. **Code Commit** → Developer push code lên Git.
2. **CI Build & Test (`github-actions.yaml`)** →
   - Unit & Integration Tests: `test_assistant_service.py`, `test_tools_integration.py`.
   - Code Quality: Linter, Formatters.
   - Infra Validation: `test_k8s_manifests.py`.
3. **Image Building** → Nếu test pass, build `Dockerfile.assistant`, `Dockerfile.trainer` và đẩy image lên registry.
4. **CD Deployment** → Triển khai tự động qua Kubernetes (`assistant-deployment.yaml`) bằng chiến lược rollout (Blue/Green, Canary).

---

### 🔸 3.3. **Luồng MLOps Lifecycle (Vòng đời Mô hình)**

1. **Scheduled Retraining** → `airflow_dag_retrain.py` hoặc `cron_retrain.yaml` kích hoạt training job.
2. **Training Job** → Chạy `assistant_trainer.py` từ `Dockerfile.trainer`.
3. **Evaluation** → `evaluation_orchestrator.py` đánh giá mô hình mới (`hallucination_eval.py`, `safety_eval.py`).
4. **Tracking & Metrics** → `mlflow_adapter.py` ghi lại BLEU, ROUGE, chi phí, thời gian vào MLflow.
5. **Model Promotion** → Nếu đạt ngưỡng, mô hình/cấu hình mới được lưu và sẵn sàng deploy.
6. **Drift Monitoring** → `drift_monitor.py` phân tích log tương tác từ `interaction_logger.py` để phát hiện Data Drift và cảnh báo retraining.

---

📘 **Tóm lại:** GenAI Factory là một **nền tảng AI Tạo sinh cấp độ doanh nghiệp**, giúp bạn xây dựng, triển khai và quản trị các ứng dụng GenAI có khả năng mở rộng, giám sát và tự động hóa toàn diện.

