# QA-Matrix: Autonomous QA Tester & Automation RAG Engine
## End-to-End System Architecture, Engineering Specifications & Workflow Blueprint

**Author:** Pursharth Singh  
**Tech Stack:** FastAPI, Google Gemini 2.0 / 3.6 Flash, Gemini Embeddings (`gemini-embedding-001`), Pinecone Serverless RAG, Playwright, Cypress, PyTest, Postman, n8n Orchestrator  
**Version:** 1.0.0  

---

## 1. Executive Overview

**QA-Matrix** is an enterprise-grade Autonomous Quality Engineering and Test Automation Intelligence Platform. It bridges the gap between Product Requirement Documents (PRDs) and automated testing by leveraging 768-dimensional Vector RAG (Retrieval-Augmented Generation) and Google Gemini Flash models.

Traditional QA processes suffer from three critical bottlenecks:
1. **Manual Test Case Design:** Engineering teams manually interpret PRDs, frequently missing boundary conditions, edge cases, and security vulnerabilities.
2. **Slow Automation Script Authoring:** Translating test cases into robust Page Object Model (POM) Playwright/Cypress code takes days.
3. **Tedious Defect Triage:** When runtime exceptions or HTTP 500 errors occur, engineers spend hours tracing logs back to requirement clauses.

**QA-Matrix solves all three challenges** in a unified, sub-second autonomous pipeline.

---

## 2. End-to-End System Architecture

```
                                  ┌─────────────────────────────────────────┐
                                  │   Document Intake (PDF, OpenAPI, Specs) │
                                  └────────────────────┬────────────────────┘
                                                       │
                                            [pypdf / Text Parser]
                                                       │
                                        [Gemini Embedding 768-dim]
                                                       │
                                                       ▼
┌──────────────────────────────────────┐       ┌────────────────────────────┐
│   FastAPI Web Console & REST API     │ ◄───► │  Pinecone / Local RAG KB   │
│   (Obsidian Glass Dark UI)           │       └────────────────────────────┘
└──────────────────┬───────────────────┘                      ▲
                   │                                          │
            [Gemini 3.6 Flash] ───────────────────────────────┘
                   │
  ┌────────────────┼────────────────┬───────────────────┐
  ▼                ▼                ▼                   ▼
[1. Test Matrix] [2. Automation]  [3. Bug RCA]     [4. Live API Runner]
(P0-P3 Strategy) (Playwright/Py)  (Jira Defect)    (HTTP Assertions)
```

### Architectural Subsystems:

1. **Document Intake & Semantic Vectorization Layer**:
   - Ingests raw PDFs via `pypdf`, OpenAPI v3 JSON/YAML, or plain text user stories.
   - Chunks text dynamically (800 words with 100-word overlap) to preserve semantic coherence.
   - Vectorizes each chunk using Google `gemini-embedding-001` (768 dimensions).
   - Indexes into Pinecone Serverless namespace (`qa-specs-v1`) with instant fallback to a high-speed local cosine-similarity vector store.

2. **RAG Semantic Retrieval Layer**:
   - Queries the vector store using cosine similarity $\text{Sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$.
   - Retrieves top-$k$ requirement chunks with relevance scores $\ge 0.75$.
   - Injects requirement citations into the prompt context for strict ground-truth generation.

3. **Gemini Flash Intelligence Core**:
   - Employs `gemini-3.6-flash` / `gemini-flash-latest` with temperature tuning ($0.1$–$0.2$) and strict JSON schema enforcement.
   - Synthesizes risk matrices, automation suites, and Jira tickets.

4. **Multi-Framework Code Synthesizer**:
   - Playwright TypeScript / Async with Page Object Models.
   - Playwright Python / Pytest.
   - Cypress v13 JavaScript with clean assertions.
   - PyTest + Requests API Contract Suites.
   - Postman Collection v2.1.0 JSON format.

5. **Runtime Failure Root Cause Analyzer (RCA)**:
   - Ingests stack traces and error logs.
   - Identifies exact code defect lines, cites breached PRD clauses, and provides code patches.

6. **Live Execution & Assertion Engine**:
   - Non-blocking asynchronous client (`httpx.AsyncClient`) for validating status codes, latency benchmarks, and payload schemas.

---

## 3. Why RAG is Used & Its Architectural Benefits

### 💡 The Core Concept (The "Open-Book Exam" Principle)
- **Without RAG (Closed Book):** The LLM relies solely on pre-training or tries to fit monolithic documents into its context window, leading to high token costs, hallucinations, and fabricated routes/assertions.
- **With RAG (Open Book):** When generating a test or diagnosing a failure, the AI queries the vector database, extracts only the exact relevant requirement clauses, and writes code/assertions strictly adhering to those rules.

### Key Architectural Benefits in QA-Matrix:
1. **100% Grounded Test Assertions:** Test cases and validations match real schema types, required parameters, and explicit acceptance criteria.
2. **Pinpoint Defect Root Cause Analysis (RCA):** On runtime exceptions or HTTP 500 errors, RAG identifies the exact PRD requirement violated and auto-generates Jira tickets with reproduction patches.
3. **90%+ Token & Latency Savings:** Instead of re-sending 50,000+ words on every request, RAG passes only the Top-4 context chunks (~1,200 tokens) with relevance scores $\ge 0.75$.
4. **Instant Zero-Retraining Adaptation:** Uploading an updated PRD or OpenAPI spec via `/api/ingest-spec` updates vectorized memory in milliseconds without model fine-tuning.
5. **High-Fidelity Code Locators:** Injects real UI field labels and DOM roles into Page Object Models (`getByRole`, `getByTestId`), eliminating test flakiness.

| Evaluation Dimension | Standard LLM Prompting | QA-Matrix Vector RAG |
|---|---|---|
| **Test Accuracy & Grounding** | Hallucinates missing fields; invents routes. | **100% strict ground-truth** tied to PRD chunks. |
| **Document Size Limit** | Restricted by context window / token budget. | **Unlimited**; handles hundreds of PDFs & specs. |
| **Token Efficiency & Cost** | Re-transmits 50,000+ tokens on every click. | Transmits only ~1,200 tokens (Top-4 chunks). |
| **Defect RCA Traceability** | Generic troubleshooting advice. | **Direct PRD clause citation** + reproduction patch. |
| **Spec Updates & Maintenance** | Manual copy-pasting of updated documents. | **Instant vector re-indexing** via `/api/ingest-spec`. |

---

## 4. Visual Workflow Blueprints

### Workflow A: Spec Ingestion & Vectorization
1. **User Action:** Uploads PRD PDF or pastes OpenAPI schema.
2. **Parser:** Extracts text and chunks into overlapping windows.
3. **Embedder:** Calls `gemini-embedding-001` to generate 768-dim vectors.
4. **Storage:** Upserts vectors + metadata into Pinecone and `data/vector_knowledge_base.json`.

### Workflow B: Autonomous Test Matrix Synthesis
1. **User Action:** Enters feature name, scope (Full, Smoke, Security), and requirements.
2. **RAG Query:** Vector search finds matching spec chunks.
3. **Gemini Engine:** Evaluates requirements against risk model.
4. **Output:** Formatted P0–P3 test cards with preconditions, steps, test data, and expected outcomes.

### Workflow C: Multi-Framework Automation Code Generation
1. **User Action:** Selects framework (e.g. Playwright TypeScript) and clicks Synthesize.
2. **Code Synthesizer:** Structures Page Object Model classes, API request fixtures, locators (`getByRole`, `getByPlaceholder`), and explicit assertions (`expect(...)`).
3. **Output:** Formatted syntax-highlighted code with 1-click copy and file download.

### Workflow D: Failure Log Root Cause Analysis & Jira Bug Generation
1. **User Action:** Pastes exception traceback or HTTP 500 error.
2. **RAG Context Search:** Finds relevant PRD requirements breached.
3. **RCA Engine:** Diagnoses unhandled exceptions, race conditions, or schema drift.
4. **Output:** Actionable Jira markdown ticket with reproduction steps and code patch.

### Workflow E: Live API Test & Assertion Execution
1. **User Action:** Inputs target URL, method, headers, and expected status.
2. **Asynchronous Runner:** Executes live HTTP request via `httpx`.
3. **Evaluation:** Measures latency, checks status match, and validates response structure.

### Workflow F: CI/CD n8n Pipeline Automation
1. **Git Trigger:** GitHub/GitLab Webhook triggers on PR commit.
2. **n8n Workflow:** Calls `/api/generate-test-matrix` and `/api/generate-automation-scripts`.
3. **Slack Alert:** Posts executive QA summary and risk assessment to `#qa-automation`.

---

## 5. REST API Reference

| Endpoint | Method | Input Parameters | Output Response |
|---|---|---|---|
| `/api/ingest-spec` | `POST` | `spec_title`, `category`, `file` or `content_text` | `chunks_indexed`, status confirmation |
| `/api/generate-test-matrix` | `POST` | `feature_name`, `test_scope`, `target_env`, `requirements` | Full JSON test matrix with P0-P3 cases |
| `/api/generate-automation-scripts` | `POST` | `feature_name`, `framework`, `test_cases`, `api_base_url` | Synthesized code, setup commands, filename |
| `/api/analyze-bug-log` | `POST` | `error_log`, `test_context`, `expected_behavior` | RCA diagnosis, code fix, Jira ticket markdown |
| `/api/execute-api-test` | `POST` | `url`, `method`, `headers`, `body`, `expected_status` | Status code, latency ms, assertion checklist |
| `/api/history` | `GET` | None | Stored test suites and bug reports |
| `/api/clear-knowledge-base` | `DELETE` | None | Clears vectorized memory |

---

## 6. Summary
The QA-Matrix engine establishes an end-to-end autonomous QA feedback loop from product requirements to production-ready test automation and bug resolution.
