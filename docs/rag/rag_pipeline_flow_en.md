📘 **GENAI FACTORY – RAG (RETRIEVAL-AUGMENTED GENERATION) EXECUTION FLOW**

---

### 🎯 OBJECTIVE
Understand how RAG operates within the **GenAI Factory** system — from the offline processing phase (Indexing) to the real-time processing phase (Inference) — including the role and technical mechanism of each component.

---

## ⚙️ 1. STAGE 1 – INDEXING PIPELINE (OFFLINE PROCESSING)
This stage converts raw documents into queryable knowledge (Vector Embeddings) to support semantic search during real-time inference.

| **Step** | **Technical Action** | **Factory Component** | **Output** |
|-----------|----------------------|------------------------|-------------|
| **1. Data Loading** | MLOps job loads raw files (PDF, DOCX, JSON) from S3 or internal storage. | `infra/storage/s3_bucket_config.yaml` | Raw documents. |
| **2. Chunking** | Long documents are split into smaller overlapping chunks (e.g., 512 tokens) to improve retrieval accuracy. | Preprocessing job (via Dockerfile.trainer). | Optimized text chunks. |
| **3. Embedding Creation** | Each text chunk is converted into a numerical vector using the embedding model (`.embed`). | `shared_libs/atomic/llms/openai_llm.py` – method `async_embed`. | Embedding vectors with metadata. |
| **4. Indexing** | Stores vectors and metadata in a Vector Database (e.g., ChromaDB, Pinecone, FAISS). | `infra/storage/vector_db_config.yaml` | Indexed Knowledge Base (Vector Index). |

🔹 **Result:** The system generates a structured, searchable knowledge repository, enabling fast and accurate semantic retrieval.

---

## ⚡ 2. STAGE 2 – INFERENCE PIPELINE (REAL-TIME PROCESSING)
This stage executes the real-time workflow when a user sends a query through the API (`assistant_service.py`), orchestrated by `AssistantInferenceService`.

| **Step** | **Technical Action** | **Factory Component** | **Role & Output** |
|-----------|----------------------|------------------------|------------------|
| **A. Query Reception** | `AssistantInferenceService` receives `user_query` and performs input safety checks (PII, Injection). | `assistant_service.py`, `safety_pipeline.py` | Validated and safe user query. |
| **B. Query Embedding** | The system embeds `user_query` into a Query Vector using the same model as in Indexing. | `openai_llm.py` – `async_embed`. | Query Vector. |
| **C. Retrieval** | Sends Query Vector to the Vector DB to find the top-k semantically closest vectors. | `retriever_tool.py` (hardened `BaseTool`). | Retrieved relevant text chunks. |
| **D. Re-ranking (Optional)** | A re-ranking model filters and reorders retrieved documents to prioritize the most relevant ones. | `rag_pipeline.py`, `retriever_config.yaml`. | High-quality Grounded Documents. |
| **E. Prompt Augmentation** | Combines Instruction + Grounded Documents + User Query into a single enhanced Prompt. | `rag_prompt.py`. | Final Prompt for LLM input. |
| **F. Response Generation** | Sends Prompt to LLM (protected by Retry & Fallback) for context-grounded answer generation. | `openai_llm.py` – `async_generate`. | Grounded and accurate LLM response. |
| **G. Output Validation** | Performs post-generation safety check (Toxicity, PII) before delivering to user. | `safety_pipeline.py`. | Safe, context-aware final answer. |

---

## 🧩 SUMMARY
RAG in GenAI Factory is a **multi-layered technical workflow**, hardened with **Async I/O, Retry/Fallback, and Vector DB**, transforming static internal data into **dynamic, queryable knowledge** in real time.

✅ **Indexing Pipeline:** Prepares knowledge (Offline).  
✅ **Inference Pipeline:** Queries and generates responses (Online).  

The result is a **Production-Grade GenAI Factory System** — fast, reliable, accurate, and enterprise-ready.

