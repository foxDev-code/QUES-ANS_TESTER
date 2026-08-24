# QA-Matrix · Autonomous QA Tester & Automation RAG Engine

A production-ready, autonomous Quality Engineering platform built with **FastAPI**, **Google Gemini 2.0 Flash**, **Pinecone Serverless RAG**, and **n8n Automation Pipelines**.

Developed by **Pursharth Singh**.

---

## ⚡ Core Capabilities

1. **📋 Autonomous Test Matrix & Plan Generator**:
   - Ingests PRDs, user stories, acceptance criteria, or OpenAPI schemas.
   - Vectorizes specifications with 768-dimensional Google Gemini embeddings.
   - Generates exhaustive test suites including **Functional / Positive**, **Negative & Error Handling**, **Boundary & Edge Cases**, **Security & Injection**, and **API Contract** tests with P0–P3 priority rankings.

2. **⚡ Multi-Framework Automation Code Synthesizer**:
   - Converts requirements and test matrices into production-grade automated scripts in:
     - **Playwright (TypeScript / Async)** with robust locators and POM structure
     - **Playwright (Python / Pytest)**
     - **Cypress v13 (JavaScript)**
     - **PyTest + Requests / Httpx (Python API Suite)**
     - **Postman Collection v2.1.0 JSON** with pre-request scripts and assertions

3. **🔍 Bug Report & Root Cause Analyzer (RCA)**:
   - Ingests runtime failure logs, stack traces, or console errors.
   - Queries the vector store to identify violated PRD requirements and acceptance criteria.
   - Outputs comprehensive Jira/GitHub formatted defect reports with root cause analysis, reproduction steps, and code patches.

4. **🚀 Live API Test & Assertion Runner**:
   - Built-in HTTP test runner that executes live requests against REST endpoints.
   - Evaluates status code matches, latency benchmarks (<2000ms), and response payload assertions with real-time metrics.

5. **🔄 CI/CD & n8n Workflow Automation**:
   - Import-ready `qa-automated-tester-rag.json` for automated GitHub/GitLab PR triggers and Slack notification reports.

---

## 🏗 System Architecture

```
                                  ┌────────────────────────┐
                                  │   PRD / OpenAPI / Docs │
                                  └───────────┬────────────┘
                                              │
                                     [pypdf / Parser]
                                              │
                                   [Gemini Embeddings]
                                              │
                                              ▼
┌─────────────────────────┐       ┌────────────────────────┐
│  FastAPI Web Dashboard  │ ◄───► │  Pinecone / Local RAG  │
│  (Obsidian Glass Theme) │       └────────────────────────┘
└───────────┬─────────────┘                   ▲
            │                                 │
     [Gemini 2.0 Flash] ──────────────────────┘
            │
            ├─► 1. Test Matrix & Risk Assessment
            ├─► 2. Playwright / Cypress / PyTest Code
            ├─► 3. Root Cause Analysis & Jira Bug Ticket
            ├─► 4. Live API Assertion Runner
            └─► 5. n8n CI/CD Webhook Trigger
```

---

## 🚀 Quick Start & Running Locally

### 1. Requirements
Ensure Python 3.9+ is installed. Dependencies:
```bash
pip install fastapi uvicorn pypdf jinja2 python-multipart requests httpx
```

### 2. Launch the Application
```bash
cd /Users/pursharthsingh/Desktop/Satyarth/Q&A_tool
python3 app.py
```
Or with Uvicorn directly:
```bash
uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8001`**

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ingest-spec` | Ingest and vectorize PRD PDF, OpenAPI schema, or user stories |
| `POST` | `/api/generate-test-matrix` | Generate test matrix & strategy via RAG semantic search |
| `POST` | `/api/generate-automation-scripts` | Synthesize Playwright, Cypress, PyTest, or Postman test code |
| `POST` | `/api/analyze-bug-log` | Perform Root Cause Analysis and generate Jira bug tickets |
| `POST` | `/api/execute-api-test` | Execute real HTTP test against endpoint and check assertions |
| `GET` | `/api/history` | Retrieve saved test suites, bug tickets, and knowledge base stats |
| `DELETE` | `/api/clear-knowledge-base` | Reset/clear vectorized memory |

---

## 📦 File Structure

```
Q&A_tool/
├── app.py                         # FastAPI application & RAG Intelligence Engine
├── qa-automated-tester-rag.json   # Exportable n8n QA workflow
├── README.md                      # Documentation & Guide
├── static/
│   ├── style.css                  # Obsidian Cyberpunk Glassmorphic styling
│   └── script.js                  # Frontend client & interactive logic
├── templates/
│   └── index.html                 # Main dashboard UI
└── data/                          # Persistent JSON storage & local vectors
```
