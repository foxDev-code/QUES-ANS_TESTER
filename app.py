"""
QA Automated Tester & Automation RAG Engine
Author: Pursharth Singh
Tech Stack: FastAPI, PyPDF, Google Gemini 2.0 Flash, Gemini Embeddings, Pinecone Serverless / Local Hybrid Vector Store
"""

import os
import io
import json
import time
import math
import re
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pypdf

# ─────────────────────────────────────────────────────────────
# CONFIGURATION & API CREDENTIALS (Loaded from Environment)
# ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_HOST = os.environ.get("PINECONE_HOST", "")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "qa-specs-v1")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
LOCAL_VECTORS_FILE = os.path.join(DATA_DIR, "vector_knowledge_base.json")
SUITES_STORE_FILE = os.path.join(DATA_DIR, "saved_test_suites.json")
BUG_REPORTS_FILE = os.path.join(DATA_DIR, "saved_bug_reports.json")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="QA Automated Tester & Automation RAG Engine",
    description="Autonomous QA Intelligence and Test Automation Platform by Pursharth Singh",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ─────────────────────────────────────────────────────────────
# PERSISTENCE HELPERS
# ─────────────────────────────────────────────────────────────
def load_json_file(filepath: str, default_val: Any) -> Any:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val


def save_json_file(filepath: str, data: Any):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")


# ─────────────────────────────────────────────────────────────
# VECTOR SEARCH & GEMINI EMBEDDING UTILITIES
# ─────────────────────────────────────────────────────────────
def get_gemini_embedding(text: str) -> List[float]:
    """Generates 768-dimensional embedding vector via Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "content": {"parts": [{"text": text[:8000]}]},
        "outputDimensionality": 768
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["embedding"]["values"]
    except Exception as e:
        print(f"⚠️ Gemini Embedding API error: {e}")
        # Deterministic fallback pseudo-vector in case of rate limit/network outage
        return [0.0] * 768


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def upsert_knowledge_vector(doc_id: str, vector: List[float], metadata: dict) -> bool:
    """Upserts into both Pinecone (if configured) and persistent local vector store."""
    # 1. Local Vector Store (Guaranteed durability)
    local_store = load_json_file(LOCAL_VECTORS_FILE, [])
    # Remove existing if any
    local_store = [item for item in local_store if item.get("id") != doc_id]
    local_store.append({
        "id": doc_id,
        "values": vector,
        "metadata": metadata,
        "created_at": time.time()
    })
    save_json_file(LOCAL_VECTORS_FILE, local_store)

    # 2. Pinecone Serverless
    if PINECONE_API_KEY and PINECONE_HOST:
        url = f"{PINECONE_HOST}/vectors/upsert"
        payload = {
            "vectors": [{
                "id": doc_id,
                "values": vector,
                "metadata": metadata
            }],
            "namespace": PINECONE_NAMESPACE
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Api-Key": PINECONE_API_KEY,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                pass
        except Exception as e:
            print(f"⚠️ Pinecone upsert note (using local store): {e}")

    return True


def query_knowledge_vectors(vector: List[float], top_k: int = 4, filter_category: Optional[str] = None) -> List[dict]:
    """Queries vector knowledge base for relevant PRD/API specification chunks."""
    matches = []

    # Try Pinecone first
    if PINECONE_API_KEY and PINECONE_HOST:
        url = f"{PINECONE_HOST}/query"
        payload = {
            "vector": vector,
            "topK": top_k,
            "includeMetadata": True,
            "namespace": PINECONE_NAMESPACE
        }
        if filter_category:
            payload["filter"] = {"category": filter_category}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Api-Key": PINECONE_API_KEY,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pinecone_matches = data.get("matches", [])
                if pinecone_matches:
                    for m in pinecone_matches:
                        matches.append({
                            "id": m.get("id"),
                            "score": m.get("score", 0.0),
                            "metadata": m.get("metadata", {})
                        })
                    return matches
        except Exception as e:
            print(f"⚠️ Pinecone query fallback to local: {e}")

    # Fallback to local vector store
    local_store = load_json_file(LOCAL_VECTORS_FILE, [])
    scored_items = []
    for item in local_store:
        if filter_category and item.get("metadata", {}).get("category") != filter_category:
            continue
        item_vector = item.get("values", [])
        if len(item_vector) == len(vector) and any(item_vector):
            score = cosine_similarity(vector, item_vector)
        else:
            score = 0.5  # fallback matching score
        scored_items.append({
            "id": item.get("id"),
            "score": round(score, 4),
            "metadata": item.get("metadata", {})
        })

    scored_items.sort(key=lambda x: x["score"], reverse=True)
    return scored_items[:top_k]


# ─────────────────────────────────────────────────────────────
# GEMINI 2.0 FLASH GENERATION ENGINE
# ─────────────────────────────────────────────────────────────
def call_gemini_llm(prompt: str, temperature: float = 0.2, response_format: str = "text") -> str:
    """Invokes Google Gemini 3.6 Flash model."""
    models_to_try = ["gemini-3.6-flash", "gemini-flash-latest"]
    
    generation_config: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": 8192,
    }
    if response_format == "json":
        generation_config["responseMimeType"] = "application/json"

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            last_error = e
            continue

    print(f"⚠️ Gemini LLM call error: {last_error}")
    raise HTTPException(status_code=500, detail=f"Gemini LLM error: {str(last_error)}")


# ─────────────────────────────────────────────────────────────
# DOCUMENT PARSER
# ─────────────────────────────────────────────────────────────
def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


def chunk_document(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    """Splits document text into overlapping chunks for semantic indexing."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks if chunks else [text]


# ─────────────────────────────────────────────────────────────
# ROUTES - WEB DASHBOARD VIEWS
# ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    local_kb = load_json_file(LOCAL_VECTORS_FILE, [])
    saved_suites = load_json_file(SUITES_STORE_FILE, [])
    saved_bugs = load_json_file(BUG_REPORTS_FILE, [])
    
    unique_specs = {}
    for item in local_kb:
        meta = item.get("metadata", {})
        title = meta.get("spec_title", "General Spec")
        if title not in unique_specs:
            unique_specs[title] = {
                "title": title,
                "category": meta.get("category", "PRD"),
                "chunks": 0,
                "created_at": item.get("created_at", time.time())
            }
        unique_specs[title]["chunks"] += 1

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "specs": list(unique_specs.values()),
            "suites_count": len(saved_suites),
            "bugs_count": len(saved_bugs),
            "kb_chunks": len(local_kb)
        }
    )


# ─────────────────────────────────────────────────────────────
# ROUTES - API ENDPOINTS
# ─────────────────────────────────────────────────────────────

# 1. SPEC / PRD / OPENAPI INGESTION
@app.post("/api/ingest-spec")
async def ingest_spec(
    spec_title: str = Form(...),
    category: str = Form("PRD"),  # PRD, OpenAPI, UserStories, Architecture
    content_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    extracted_text = ""
    if file and file.filename:
        file_bytes = await file.read()
        if file.filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_bytes)
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
    elif content_text:
        extracted_text = content_text.strip()

    if not extracted_text:
        raise HTTPException(status_code=400, detail="Please upload a PDF/text spec or paste the requirements.")

    chunks = chunk_document(extracted_text, chunk_size=800, overlap=100)
    indexed_count = 0

    clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', spec_title.lower())
    for idx, chunk in enumerate(chunks):
        doc_id = f"spec_{clean_title}_{idx}_{int(time.time())}"
        vector = get_gemini_embedding(chunk)
        metadata = {
            "spec_title": spec_title,
            "category": category,
            "chunk_index": idx,
            "total_chunks": len(chunks),
            "text": chunk[:1500]
        }
        upsert_knowledge_vector(doc_id, vector, metadata)
        indexed_count += 1

    return JSONResponse({
        "status": "success",
        "message": f"Successfully indexed '{spec_title}' into RAG vector knowledge base.",
        "spec_title": spec_title,
        "category": category,
        "chunks_indexed": indexed_count,
        "sample_preview": extracted_text[:300] + "..."
    })


# 2. GENERATE TEST MATRIX & COMPREHENSIVE TEST PLAN
@app.post("/api/generate-test-matrix")
async def generate_test_matrix(request: Request):
    data = await request.json()
    feature_name = data.get("feature_name", "Authentication & User Management")
    requirements = data.get("requirements", "")
    test_scope = data.get("test_scope", "full")  # full, smoke, regression, security, edge_cases
    target_env = data.get("target_env", "Web App & REST API")

    # Step 1: RAG Search for relevant context
    search_query = f"{feature_name} {requirements}"
    query_vec = get_gemini_embedding(search_query)
    rag_matches = query_knowledge_vectors(query_vec, top_k=4)
    
    rag_context = ""
    citations = []
    for idx, match in enumerate(rag_matches):
        meta = match.get("metadata", {})
        txt = meta.get("text", "")
        title = meta.get("spec_title", f"Spec Chunk {idx+1}")
        if txt:
            rag_context += f"\n--- [RAG Source: {title} (Score: {match.get('score', 0):.2f})] ---\n{txt}\n"
            citations.append({"title": title, "score": match.get("score", 0)})

    # Step 2: Gemini 2.0 Flash Prompt
    prompt = f"""
You are an Elite Principal QA Automation Architect and Lead Quality Engineer.
Analyze the user's feature requirement and the retrieved RAG specifications to generate an exhaustive, industrial-grade Test Plan and Test Matrix.

FEATURE / MODULE: {feature_name}
TARGET ENVIRONMENT: {target_env}
TEST SCOPE: {test_scope.upper()}
USER REQUIREMENTS / USER STORY:
{requirements}

RELEVANT RAG KNOWLEDGE BASE CONTEXT:
{rag_context if rag_context else "No prior documents indexed. Use the provided requirements directly."}

Return a STRICT JSON object matching this schema:
{{
  "feature_name": "{feature_name}",
  "summary": "Executive summary of testing strategy, risk assessment, and quality gates.",
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "test_metrics": {{
    "total_cases": 0,
    "positive_cases": 0,
    "negative_cases": 0,
    "boundary_edge_cases": 0,
    "security_cases": 0,
    "estimated_exec_time_mins": 0
  }},
  "test_cases": [
    {{
      "id": "TC-001",
      "category": "Functional / Positive" | "Negative / Error Handling" | "Boundary & Edge Case" | "Security & Auth" | "API Contract" | "Accessibility",
      "priority": "P0" | "P1" | "P2" | "P3",
      "title": "Clear descriptive title",
      "preconditions": "Preconditions required",
      "steps": [
        "Step 1: ...",
        "Step 2: ...",
        "Step 3: ..."
      ],
      "test_data": "Input parameters or payload",
      "expected_result": "Exact expected behavior and assertion criteria",
      "rag_requirement_ref": "Specific requirement or acceptance criteria mapped"
    }}
  ],
  "suggested_automation_framework": "Playwright / Cypress / PyTest",
  "rag_citations": [
    {{ "title": "...", "relevance": "..." }}
  ]
}}
Ensure you provide at least 6 to 10 highly detailed test cases covering all edge conditions, status codes, payload validations, and authorization boundaries. Return ONLY valid JSON.
"""

    raw_response = call_gemini_llm(prompt, temperature=0.15, response_format="json")
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        result = json.loads(clean_json.strip())
        
        # Save to stored suites
        suites = load_json_file(SUITES_STORE_FILE, [])
        suite_record = {
            "id": f"suite_{int(time.time())}",
            "created_at": time.time(),
            "feature_name": feature_name,
            "scope": test_scope,
            "data": result
        }
        suites.insert(0, suite_record)
        save_json_file(SUITES_STORE_FILE, suites[:50])

        return JSONResponse({"status": "success", "data": result})
    except Exception as e:
        print(f"Error parsing Gemini response: {e}\nRaw: {raw_response}")
        return JSONResponse({"status": "error", "message": "Failed to parse test matrix JSON", "raw": raw_response}, status_code=500)


# 3. GENERATE AUTOMATION TEST SCRIPTS (PLAYWRIGHT, CYPRESS, PYTEST, POSTMAN)
@app.post("/api/generate-automation-scripts")
async def generate_automation_scripts(request: Request):
    data = await request.json()
    feature_name = data.get("feature_name", "User Authentication API")
    framework = data.get("framework", "playwright_ts") # playwright_ts, playwright_py, cypress_js, pytest_api, postman_json
    test_cases_json = data.get("test_cases", [])
    api_base_url = data.get("api_base_url", "https://api.example.com")
    web_url = data.get("web_url", "https://app.example.com")

    prompt = f"""
You are a Staff QA Automation Engineer. Write production-ready, fully executable, robust automated test suite code.

FEATURE: {feature_name}
FRAMEWORK REQUESTED: {framework}
BASE API URL: {api_base_url}
BASE WEB URL: {web_url}

TEST CASES TO AUTOMATE:
{json.dumps(test_cases_json, indent=2) if test_cases_json else "Automate standard CRUD, edge-cases, invalid auth, boundary lengths, and contract validations for: " + feature_name}

FRAMEWORK GUIDELINES:
- If 'playwright_ts': Use TypeScript `@playwright/test`, Page Object Model structure or clean async test functions, robust locators (`getByRole`, `getByTestId`, `getByPlaceholder`), explicit assertions (`expect(...)`), and API request fixture testing where applicable.
- If 'playwright_py': Use Python `playwright.sync_api` or `async_api` with `pytest` fixtures, clean assertions, and exception handling.
- If 'cypress_js': Use modern Cypress v13 syntax, custom commands if helpful, data-cy locators, assertions with `should()`.
- If 'pytest_api': Use Python `pytest`, `requests` / `httpx`, parametrized fixtures, status code assertions, JSON schema validation, and header checks.
- If 'postman_json': Generate a valid Postman Collection v2.1.0 JSON format with pre-request scripts, environment variables, tests asserting `pm.response.to.have.status(...)` and `pm.expect(jsonData...)`.

Return a STRICT JSON object:
{{
  "framework": "{framework}",
  "filename": "e.g. auth_spec.spec.ts or test_auth_api.py or Postman_Collection.json",
  "code": "The complete, raw code string (properly escaped for JSON)",
  "setup_instructions": [
    "Step 1: npm install ... or pip install ...",
    "Step 2: Command to execute the suite"
  ],
  "dependencies": ["@playwright/test", "typescript"] or ["pytest", "requests"]
}}
Return ONLY valid JSON.
"""

    raw_response = call_gemini_llm(prompt, temperature=0.1, response_format="json")
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        result = json.loads(clean_json.strip())
        return JSONResponse({"status": "success", "data": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error generating code: {str(e)}", "raw": raw_response}, status_code=500)


# 4. BUG REPORT & ROOT CAUSE ANALYZER (WITH RAG SPEC CITATIONS)
@app.post("/api/analyze-bug-log")
async def analyze_bug_log(request: Request):
    data = await request.json()
    error_log = data.get("error_log", "")
    test_context = data.get("test_context", "API Endpoint or UI Flow")
    expected_behavior = data.get("expected_behavior", "")

    if not error_log:
        raise HTTPException(status_code=400, detail="Please paste an error log, stack trace, or test assertion failure.")

    # Query vector store for related spec requirements
    query_vec = get_gemini_embedding(f"{test_context} {error_log[:1000]}")
    rag_matches = query_knowledge_vectors(query_vec, top_k=3)

    rag_specs = ""
    for m in rag_matches:
        meta = m.get("metadata", {})
        rag_specs += f"\n- Spec '{meta.get('spec_title', 'Requirement')}': {meta.get('text', '')[:400]}...\n"

    prompt = f"""
You are a Principal Software Reliability & QA Lead.
Analyze the following runtime failure / stack trace against the system specifications to perform an exhaustive Root Cause Analysis (RCA) and generate a ready-to-publish Jira/GitHub Bug Report.

TEST CONTEXT: {test_context}
USER'S EXPECTED BEHAVIOR: {expected_behavior}
ACTUAL RUNTIME ERROR LOG / STACK TRACE:
{error_log}

RELEVANT SYSTEM SPECIFICATIONS (RAG RETRIEVED):
{rag_specs if rag_specs else "No matching spec chunks found in knowledge base."}

Return a STRICT JSON object matching this schema:
{{
  "bug_title": "Concise, actionable Jira-style bug title (e.g., '[Auth Service] HTTP 500 Unhandled NullPointerException when refreshing expired JWT token')",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "priority": "P0 - Blocker" | "P1 - Critical" | "P2 - Major" | "P3 - Minor",
  "affected_component": "e.g. Auth Service / Payment Gateway / React UI",
  "root_cause_analysis": "Detailed technical diagnosis explaining why the error occurred, memory leak, concurrency race condition, missing null check, or API contract mismatch.",
  "violated_spec_or_requirement": "Exact requirement or acceptance criteria that was breached based on the RAG context.",
  "steps_to_reproduce": [
    "1. Send POST request to /api/v1/auth/refresh with body...",
    "2. Pass expired header...",
    "3. Observe response..."
  ],
  "expected_result": "Detailed expected outcome",
  "actual_result": "Detailed actual error outcome",
  "recommended_code_fix": "Concrete code diff or patch recommendation to fix the defect",
  "markdown_jira_ticket": "Complete formatted Markdown string ready to copy-paste into Jira or GitHub Issues."
}}
Return ONLY valid JSON.
"""

    raw_response = call_gemini_llm(prompt, temperature=0.1, response_format="json")
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        result = json.loads(clean_json.strip())

        # Save to stored bugs
        bugs = load_json_file(BUG_REPORTS_FILE, [])
        bug_record = {
            "id": f"bug_{int(time.time())}",
            "created_at": time.time(),
            "data": result
        }
        bugs.insert(0, bug_record)
        save_json_file(BUG_REPORTS_FILE, bugs[:50])

        return JSONResponse({"status": "success", "data": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error analyzing bug: {str(e)}", "raw": raw_response}, status_code=500)


# 5. LIVE API TEST EXECUTOR & ASSERTION RUNNER
@app.post("/api/execute-api-test")
async def execute_api_test(request: Request):
    import httpx
    data = await request.json()
    url = data.get("url", "").strip()
    method = data.get("method", "GET").upper()
    headers_input = data.get("headers", {})
    body_input = data.get("body", None)
    expected_status = data.get("expected_status", 200)

    if not url:
        raise HTTPException(status_code=400, detail="Target URL is required.")

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    start_time = time.time()
    headers = {"User-Agent": "QA-Matrix-Bot/1.0", "Accept": "application/json"}
    if isinstance(headers_input, dict):
        headers.update(headers_input)
    elif isinstance(headers_input, str) and headers_input.strip():
        try:
            parsed_h = json.loads(headers_input)
            headers.update(parsed_h)
        except Exception:
            pass

    req_json = None
    req_content = None
    if method in ["POST", "PUT", "PATCH"] and body_input:
        if isinstance(body_input, dict):
            req_json = body_input
        elif isinstance(body_input, str) and body_input.strip():
            try:
                req_json = json.loads(body_input)
            except Exception:
                req_content = body_input.encode("utf-8")

    status_code = None
    response_headers = {}
    response_body = ""
    error_msg = None

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=req_json,
                content=req_content
            )
            status_code = resp.status_code
            response_headers = dict(resp.headers)
            try:
                response_body = resp.json()
            except Exception:
                response_body = resp.text[:4000]
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        response_headers = dict(e.response.headers)
        try:
            response_body = e.response.json()
        except Exception:
            response_body = e.response.text[:4000]
    except Exception as e:
        error_msg = str(e)

    latency_ms = round((time.time() - start_time) * 1000, 2)
    status_passed = (status_code == int(expected_status)) if status_code else False

    assertions = [
        {
            "assertion": f"Status Code equals {expected_status}",
            "actual": status_code if status_code else "Connection Failed",
            "passed": status_passed
        },
        {
            "assertion": "Latency under 2000ms",
            "actual": f"{latency_ms} ms",
            "passed": latency_ms < 2000
        },
        {
            "assertion": "Response payload received",
            "actual": "Valid response body" if response_body else (error_msg or "Empty"),
            "passed": bool(response_body) and not error_msg
        }
    ]

    all_passed = all(a["passed"] for a in assertions)

    return JSONResponse({
        "status": "success",
        "url": url,
        "method": method,
        "response_status": status_code,
        "latency_ms": latency_ms,
        "passed": all_passed,
        "assertions": assertions,
        "headers": response_headers,
        "body": response_body,
        "error": error_msg
    })


# 6. EXPORT / HISTORY ENDPOINTS
@app.get("/api/history")
async def get_history():
    suites = load_json_file(SUITES_STORE_FILE, [])
    bugs = load_json_file(BUG_REPORTS_FILE, [])
    local_kb = load_json_file(LOCAL_VECTORS_FILE, [])
    return JSONResponse({
        "suites": suites[:20],
        "bugs": bugs[:20],
        "kb_count": len(local_kb)
    })


@app.delete("/api/clear-knowledge-base")
async def clear_kb():
    save_json_file(LOCAL_VECTORS_FILE, [])
    return JSONResponse({"status": "success", "message": "Knowledge base cleared."})


@app.get("/architecture-pdf")
async def download_architecture_pdf():
    pdf_path = os.path.join(BASE_DIR, "QA_MATRIX_SYSTEM_ARCHITECTURE_AND_WORKFLOW.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename="QA_MATRIX_SYSTEM_ARCHITECTURE_AND_WORKFLOW.pdf")
    raise HTTPException(status_code=404, detail="PDF document not found.")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting QA Automated Tester & Automation RAG Engine on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
