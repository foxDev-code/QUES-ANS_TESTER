/* ─────────────────────────────────────────────────────────────
   QA-Matrix · Frontend Interactivity & API Client
   ───────────────────────────────────────────────────────────── */

let currentTestMatrix = null;
let currentAutomationCode = null;
let currentBugReport = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initPipelineTicker();
  initSampleButtons();
  initMatrixGenerator();
  initCodeSynthesizer();
  initBugAnalyzer();
  initApiRunner();
  initKnowledgeBase();
  initModals();
});

/* ─── QA PIPELINE LIVE LOG TICKER ─── */
function initPipelineTicker() {
  const tickerMessages = [
    'Received: "Synthesize full test matrix for OAuth2 Token Refresh PRD..."',
    'Chunking spec → 1,420 tokens → 768-dim Gemini embeddings generated',
    'Vector search complete: 4 relevant spec chunks, avg cosine sim 0.92',
    'RAG prompt context injected (2,840 tokens)',
    'Generating P0-P3 test cases: 8 scenarios, boundary & security checks',
    'Synthesizing Playwright TypeScript suite with Page Object Model...',
    'Live API Runner: POST /api/v1/auth/refresh executed in 3.42ms (Passed)',
    'RCA Engine: Diagnosed UnboundLocalError in token refresh exception handler',
    'Idle. Listening for next CI/CD webhook or PRD intake trigger...'
  ];

  let idx = 0;
  const logElem = document.getElementById('pipelineLiveLog');
  if (logElem) {
    setInterval(() => {
      idx = (idx + 1) % tickerMessages.length;
      logElem.style.opacity = '0';
      setTimeout(() => {
        logElem.textContent = tickerMessages[idx];
        logElem.style.opacity = '1';
      }, 250);
    }, 2800);
  }
}

/* ─── TOAST NOTIFICATIONS ─── */
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ─── TAB NAVIGATION ─── */
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetPane = document.getElementById(targetTab);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

function switchToTab(tabId) {
  const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  if (btn) btn.click();
}

/* ─── SAMPLE DATA LOADERS ─── */
function initSampleButtons() {
  const sampleReqBtn = document.getElementById('loadSampleReqBtn');
  if (sampleReqBtn) {
    sampleReqBtn.addEventListener('click', () => {
      document.getElementById('featureNameInput').value = 'OAuth2 JWT Authentication & Session Renewal API';
      document.getElementById('targetEnvInput').value = 'Next.js 14 Frontend + FastAPI Microservices';
      document.getElementById('requirementsInput').value = 
`USER STORY:
As a registered user, I want to securely log in with email/password and refresh my session automatically with a secure httpOnly refresh token so that my active session is never abruptly disconnected without logging out.

ACCEPTANCE CRITERIA:
1. Endpoint: POST /api/v1/auth/login
   - Requires valid email format and password (min 8 chars, 1 uppercase, 1 special char).
   - Rate limiting: max 5 failed login attempts in 15 minutes before locking account for 30 minutes (HTTP 429).
   - On success: Returns HTTP 200 with JSON { access_token: "...", token_type: "bearer", expires_in: 900 } and sets httpOnly Secure SameSite=Strict cookie for refresh_token (valid 7 days).
2. Endpoint: POST /api/v1/auth/refresh
   - Reads refresh_token cookie.
   - If refresh_token is expired or blacklisted: returns HTTP 401 { error: "token_expired_or_revoked" }.
   - If valid: issues new access_token and rotates the refresh_token in database (Token Rotation Defense).
3. Security & Boundary Requirements:
   - Reject SQL injection or NoSQL injection payloads with HTTP 400.
   - CORS headers must only allow whitelisted origins.
   - Never expose raw stack traces in error responses.`;
      showToast('Sample specification loaded!', 'success');
    });
  }

  const sampleBugBtn = document.getElementById('loadSampleBugBtn');
  if (sampleBugBtn) {
    sampleBugBtn.addEventListener('click', () => {
      document.getElementById('bugContextInput').value = 'POST /api/v1/auth/refresh';
      document.getElementById('bugExpectedInput').value = 'Return HTTP 401 Unauthorized with JSON { error: "token_expired" } when an expired refresh token cookie is submitted.';
      document.getElementById('bugLogInput').value = 
`ERROR:root:Unhandled exception in request POST /api/v1/auth/refresh
Traceback (most recent call last):
  File "/app/routers/auth.py", line 142, in refresh_token_handler
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
  File "/usr/local/lib/python3.11/site-packages/jwt/api_jwt.py", line 204, in decode
    self._validate_claims(payload, merged_options, **kwargs)
  File "/usr/local/lib/python3.11/site-packages/jwt/api_jwt.py", line 286, in _validate_claims
    raise ExpiredSignatureError("Signature has expired")
jwt.exceptions.ExpiredSignatureError: Signature has expired

During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 320, in app
    response = await run_endpoint_function(...)
  File "/app/routers/auth.py", line 148, in refresh_token_handler
    user_id = payload.get("sub")
UnboundLocalError: local variable 'payload' referenced before assignment
INFO: 192.168.1.45:54210 - "POST /api/v1/auth/refresh HTTP/1.1" 500 Internal Server Error`;
      showToast('Sample runtime stack trace loaded!', 'success');
    });
  }
}

/* ─── 1. TEST MATRIX GENERATION ─── */
function initMatrixGenerator() {
  const form = document.getElementById('matrixForm');
  const spinner = document.getElementById('matrixSpinner');
  const generateBtn = document.getElementById('generateMatrixBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const featureName = document.getElementById('featureNameInput').value;
    const testScope = document.getElementById('testScopeSelect').value;
    const targetEnv = document.getElementById('targetEnvInput').value;
    const requirements = document.getElementById('requirementsInput').value;

    spinner.classList.remove('hidden');
    generateBtn.disabled = true;

    try {
      const resp = await fetch('/api/generate-test-matrix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature_name: featureName,
          test_scope: testScope,
          target_env: targetEnv,
          requirements: requirements
        })
      });

      const data = await resp.json();
      if (data.status === 'success') {
        currentTestMatrix = data.data;
        renderTestMatrix(data.data);
        showToast(`Generated ${data.data.test_cases.length} test cases via RAG!`, 'success');
      } else {
        showToast(data.message || 'Error generating test matrix', 'error');
      }
    } catch (err) {
      showToast('Network error while querying RAG engine', 'error');
      console.error(err);
    } finally {
      spinner.classList.add('hidden');
      generateBtn.disabled = false;
    }
  });

  // Export Matrix JSON & Markdown
  document.getElementById('exportMatrixJsonBtn')?.addEventListener('click', () => {
    if (!currentTestMatrix) return;
    downloadTextFile(`test_matrix_${Date.now()}.json`, JSON.stringify(currentTestMatrix, null, 2), 'application/json');
  });

  document.getElementById('exportMatrixMdBtn')?.addEventListener('click', () => {
    if (!currentTestMatrix) return;
    let md = `# Test Plan & Matrix: ${currentTestMatrix.feature_name}\n\n`;
    md += `**Risk Level:** ${currentTestMatrix.risk_level}\n\n`;
    md += `### Executive Summary\n${currentTestMatrix.summary}\n\n`;
    md += `### Test Cases\n\n`;
    currentTestMatrix.test_cases.forEach(tc => {
      md += `#### [${tc.id}] ${tc.title} (${tc.priority} - ${tc.category})\n`;
      md += `- **Preconditions:** ${tc.preconditions}\n`;
      md += `- **Steps:**\n`;
      tc.steps.forEach(s => md += `  - ${s}\n`);
      md += `- **Test Data:** \`${tc.test_data}\`\n`;
      md += `- **Expected Result:** ${tc.expected_result}\n\n`;
    });
    downloadTextFile(`test_plan_${Date.now()}.md`, md, 'text/markdown');
  });

  // Send directly to code synthesizer
  document.getElementById('sendToSynthesizerBtn')?.addEventListener('click', () => {
    if (!currentTestMatrix) return;
    document.getElementById('synthFeatureName').value = currentTestMatrix.feature_name;
    document.getElementById('synthCustomContext').value = `Automate the generated test cases: ${currentTestMatrix.test_cases.map(t => t.id + ' (' + t.title + ')').join(', ')}`;
    switchToTab('tab-scripts');
    showToast('Transferred test matrix into code synthesizer!', 'success');
  });
}

function renderTestMatrix(matrix) {
  document.getElementById('matrixEmptyState').classList.add('hidden');
  document.getElementById('matrixResultView').classList.remove('hidden');
  document.getElementById('matrixExportGroup').classList.remove('hidden');

  document.getElementById('matrixSubtitle').textContent = `${matrix.feature_name} (${matrix.test_cases.length} Scenarios)`;
  document.getElementById('resRiskBadge').textContent = matrix.risk_level || 'MEDIUM';
  document.getElementById('resTotalCases').textContent = matrix.test_metrics?.total_cases || matrix.test_cases.length;
  
  const criticalCount = matrix.test_cases.filter(tc => tc.priority === 'P0' || tc.priority === 'P1').length;
  document.getElementById('resCriticalCases').textContent = criticalCount;
  document.getElementById('resEstTime').textContent = (matrix.test_metrics?.estimated_exec_time_mins || Math.round(matrix.test_cases.length * 2.5)) + 'm';

  document.getElementById('resStrategySummary').innerHTML = `<b>Strategy & Quality Gates:</b> ${matrix.summary}`;

  const container = document.getElementById('testCasesContainer');
  container.innerHTML = '';

  matrix.test_cases.forEach(tc => {
    const pClass = tc.priority === 'P0' ? 'badge-p0' : tc.priority === 'P1' ? 'badge-p1' : tc.priority === 'P2' ? 'badge-p2' : 'badge-p3';
    const card = document.createElement('div');
    card.className = 'test-case-item';
    card.innerHTML = `
      <div class="tc-header">
        <div class="tc-badges">
          <span class="tc-id">${tc.id}</span>
          <span class="badge-pill ${pClass}">${tc.priority}</span>
          <span class="badge-pill badge-cat">${tc.category}</span>
        </div>
      </div>
      <div class="tc-title">${tc.title}</div>
      <div class="tc-details">
        <div><b>Preconditions:</b> ${tc.preconditions || 'None'}</div>
        <ol class="tc-steps">
          ${tc.steps.map(s => `<li>${s}</li>`).join('')}
        </ol>
        <div><b>Test Data:</b> <code>${tc.test_data || 'Standard'}</code></div>
        <div class="tc-expected"><b>Expected Result:</b> ${tc.expected_result}</div>
      </div>
    `;
    container.appendChild(card);
  });
}

/* ─── 2. AUTOMATION CODE SYNTHESIZER ─── */
function initCodeSynthesizer() {
  const form = document.getElementById('synthForm');
  const spinner = document.getElementById('scriptSpinner');
  const generateBtn = document.getElementById('generateScriptBtn');
  const codeOutput = document.getElementById('codeOutput');
  const copyBtn = document.getElementById('copyCodeBtn');
  const downloadBtn = document.getElementById('downloadScriptBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const featureName = document.getElementById('synthFeatureName').value;
    const framework = document.getElementById('synthFramework').value;
    const apiBaseUrl = document.getElementById('synthApiBase').value;
    const webUrl = document.getElementById('synthWebBase').value;
    const customContext = document.getElementById('synthCustomContext').value;

    spinner.classList.remove('hidden');
    generateBtn.disabled = true;
    codeOutput.textContent = '// Synthesizing robust automated test suite with AI... Please wait...';

    try {
      const payload = {
        feature_name: featureName,
        framework: framework,
        api_base_url: apiBaseUrl,
        web_url: webUrl,
        test_cases: currentTestMatrix ? currentTestMatrix.test_cases : [],
        custom_instructions: customContext
      };

      const resp = await fetch('/api/generate-automation-scripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await resp.json();
      if (data.status === 'success') {
        currentAutomationCode = data.data;
        document.getElementById('codeEditorFilename').textContent = data.data.filename || 'test_suite.spec.ts';
        document.getElementById('codeEditorSub').textContent = `Framework: ${data.data.framework}`;
        codeOutput.textContent = data.data.code;

        // Setup instructions
        const instructionsBox = document.getElementById('setupInstructionsBox');
        const instructionsList = document.getElementById('setupInstructionsList');
        if (data.data.setup_instructions && data.data.setup_instructions.length) {
          instructionsBox.classList.remove('hidden');
          instructionsList.innerHTML = data.data.setup_instructions.map(i => `<li>${i}</li>`).join('');
        }
        showToast('Automation script synthesized successfully!', 'success');
      } else {
        codeOutput.textContent = `// Error: ${data.message || 'Failed to synthesize code'}`;
        showToast('Failed to synthesize code', 'error');
      }
    } catch (err) {
      showToast('Network error during script generation', 'error');
      console.error(err);
    } finally {
      spinner.classList.add('hidden');
      generateBtn.disabled = false;
    }
  });

  copyBtn?.addEventListener('click', () => {
    const text = codeOutput.textContent;
    navigator.clipboard.writeText(text).then(() => {
      showToast('Code copied to clipboard!', 'success');
    });
  });

  downloadBtn?.addEventListener('click', () => {
    if (!currentAutomationCode) return;
    downloadTextFile(currentAutomationCode.filename || 'test_script.txt', currentAutomationCode.code, 'text/plain');
  });
}

/* ─── 3. BUG & RCA ANALYZER ─── */
function initBugAnalyzer() {
  const form = document.getElementById('bugForm');
  const spinner = document.getElementById('bugSpinner');
  const analyzeBtn = document.getElementById('analyzeBugBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorLog = document.getElementById('bugLogInput').value;
    const testContext = document.getElementById('bugContextInput').value;
    const expectedBehavior = document.getElementById('bugExpectedInput').value;

    if (!errorLog.trim()) {
      showToast('Please paste an error log or stack trace', 'error');
      return;
    }

    spinner.classList.remove('hidden');
    analyzeBtn.disabled = true;

    try {
      const resp = await fetch('/api/analyze-bug-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_log: errorLog,
          test_context: testContext,
          expected_behavior: expectedBehavior
        })
      });

      const data = await resp.json();
      if (data.status === 'success') {
        currentBugReport = data.data;
        renderBugReport(data.data);
        showToast('Root cause diagnosed & Jira ticket generated!', 'success');
      } else {
        showToast(data.message || 'Error diagnosing bug', 'error');
      }
    } catch (err) {
      showToast('Network error during bug diagnosis', 'error');
      console.error(err);
    } finally {
      spinner.classList.add('hidden');
      analyzeBtn.disabled = false;
    }
  });

  document.getElementById('copyJiraTicketBtn')?.addEventListener('click', () => {
    if (!currentBugReport) return;
    const ticketText = currentBugReport.markdown_jira_ticket || 
`h2. Defect: ${currentBugReport.bug_title}
*Severity:* ${currentBugReport.severity} | *Priority:* ${currentBugReport.priority}

h3. Root Cause Analysis
${currentBugReport.root_cause_analysis}

h3. Violated Requirement
${currentBugReport.violated_spec_or_requirement}

h3. Steps to Reproduce
${currentBugReport.steps_to_reproduce.join('\n')}

h3. Recommended Fix
{code}
${currentBugReport.recommended_code_fix}
{code}`;

    navigator.clipboard.writeText(ticketText).then(() => {
      showToast('Jira ticket markdown copied to clipboard!', 'success');
    });
  });
}

function renderBugReport(bug) {
  document.getElementById('bugEmptyState').classList.add('hidden');
  document.getElementById('bugResultView').classList.remove('hidden');
  document.getElementById('copyJiraTicketBtn').classList.remove('hidden');

  document.getElementById('bugSeverityBadge').textContent = bug.severity;
  document.getElementById('bugPriorityBadge').textContent = bug.priority;
  document.getElementById('bugComponentBadge').textContent = bug.affected_component || 'Backend Service';

  document.getElementById('bugTitleView').textContent = bug.bug_title;
  document.getElementById('bugRcaText').textContent = bug.root_cause_analysis;
  document.getElementById('bugViolatedSpecText').textContent = bug.violated_spec_or_requirement || 'General API Contract Violation';
  document.getElementById('bugFixCode').textContent = bug.recommended_code_fix;

  const stepsList = document.getElementById('bugStepsList');
  stepsList.innerHTML = bug.steps_to_reproduce.map(s => `<li>${s}</li>`).join('');
}

/* ─── 4. LIVE API TEST RUNNER ─── */
function initApiRunner() {
  const form = document.getElementById('apiRunnerForm');
  const spinner = document.getElementById('apiSpinner');
  const runBtn = document.getElementById('runApiBtn');

  // Preset Buttons
  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('apiUrlInput').value = btn.dataset.url;
      document.getElementById('apiMethodSelect').value = btn.dataset.method;
      document.getElementById('apiExpectedStatus').value = btn.dataset.status;
    });
  });

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('apiUrlInput').value;
    const method = document.getElementById('apiMethodSelect').value;
    const expectedStatus = document.getElementById('apiExpectedStatus').value;
    const headersInput = document.getElementById('apiHeadersInput').value;
    const bodyInput = document.getElementById('apiBodyInput').value;

    spinner.classList.remove('hidden');
    runBtn.disabled = true;

    try {
      const resp = await fetch('/api/execute-api-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url,
          method: method,
          expected_status: parseInt(expectedStatus),
          headers: headersInput,
          body: bodyInput
        })
      });

      const data = await resp.json();
      renderApiResult(data);
      if (data.passed) {
        showToast(`API Test Passed! (${data.latency_ms}ms)`, 'success');
      } else {
        showToast(`API Test Failed assertions! (${data.response_status})`, 'error');
      }
    } catch (err) {
      showToast('Failed to connect to API target', 'error');
      console.error(err);
    } finally {
      spinner.classList.add('hidden');
      runBtn.disabled = false;
    }
  });
}

function renderApiResult(res) {
  document.getElementById('apiEmptyState').classList.add('hidden');
  document.getElementById('apiResultView').classList.remove('hidden');
  
  const statusBadge = document.getElementById('apiLiveStatusBadge');
  statusBadge.classList.remove('hidden');
  document.getElementById('apiStatusCode').textContent = `${res.response_status || 'ERR'} ${res.method}`;

  document.getElementById('resLatency').textContent = `${res.latency_ms} ms`;
  const passElem = document.getElementById('resOverallPass');
  passElem.textContent = res.passed ? 'PASSED ✓' : 'FAILED ✕';
  passElem.className = res.passed ? 'metric-value text-emerald' : 'metric-value text-red';

  const assertionsContainer = document.getElementById('assertionsContainer');
  assertionsContainer.innerHTML = '';

  (res.assertions || []).forEach(a => {
    const row = document.createElement('div');
    row.className = 'assertion-row';
    row.innerHTML = `
      <span>${a.assertion}</span>
      <span class="${a.passed ? 'assert-pass' : 'assert-fail'}">
        ${a.passed ? '✓ PASS' : '✕ FAIL'} (${a.actual})
      </span>
    `;
    assertionsContainer.appendChild(row);
  });

  const bodyCode = document.getElementById('apiResponseBody');
  if (typeof res.body === 'object') {
    bodyCode.textContent = JSON.stringify(res.body, null, 2);
  } else {
    bodyCode.textContent = res.body || (res.error ? `Error: ${res.error}` : 'Empty body');
  }
}

/* ─── 5. KNOWLEDGE BASE & SPEC INGESTION ─── */
function initKnowledgeBase() {
  const form = document.getElementById('kbIngestForm');
  const spinner = document.getElementById('kbSpinner');
  const ingestBtn = document.getElementById('kbIngestBtn');
  const fileDropZone = document.getElementById('fileDropZone');
  const fileInput = document.getElementById('kbFileInput');
  const fileDropText = document.getElementById('fileDropText');
  const clearKbBtn = document.getElementById('clearKbBtn');

  if (fileDropZone && fileInput) {
    fileDropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        fileDropText.textContent = `Selected: ${fileInput.files[0].name}`;
      }
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const specTitle = document.getElementById('kbSpecTitle').value;
      const category = document.getElementById('kbCategory').value;
      const contentText = document.getElementById('kbContentText').value;

      const formData = new FormData();
      formData.append('spec_title', specTitle);
      formData.append('category', category);
      if (contentText) formData.append('content_text', contentText);
      if (fileInput && fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
      }

      spinner.classList.remove('hidden');
      ingestBtn.disabled = true;

      try {
        const resp = await fetch('/api/ingest-spec', {
          method: 'POST',
          body: formData
        });

        const data = await resp.json();
        if (data.status === 'success') {
          showToast(`Indexed ${data.chunks_indexed} vector chunks for '${specTitle}'!`, 'success');
          form.reset();
          if (fileDropText) fileDropText.innerHTML = 'Drag & drop PRD PDF here or <span class="browse-link">browse</span>';
          setTimeout(() => window.location.reload(), 1200);
        } else {
          showToast(data.detail || 'Error indexing document', 'error');
        }
      } catch (err) {
        showToast('Network error indexing specification', 'error');
        console.error(err);
      } finally {
        spinner.classList.add('hidden');
        ingestBtn.disabled = false;
      }
    });
  }

  clearKbBtn?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear the vectorized knowledge base memory?')) return;
    try {
      await fetch('/api/clear-knowledge-base', { method: 'DELETE' });
      showToast('Knowledge base cleared!', 'success');
      setTimeout(() => window.location.reload(), 1000);
    } catch (err) {
      showToast('Failed to clear knowledge base', 'error');
    }
  });
}

/* ─── 6. HISTORY & EXPORT MODALS ─── */
function initModals() {
  const historyModal = document.getElementById('historyModal');
  const openHistoryBtn = document.getElementById('openHistoryModalBtn');
  const closeHistoryBtn = document.getElementById('closeHistoryModalBtn');
  const openIngestBtn = document.getElementById('openIngestModalBtn');

  openIngestBtn?.addEventListener('click', () => {
    switchToTab('tab-knowledge-base');
  });

  openHistoryBtn?.addEventListener('click', async () => {
    historyModal.classList.remove('hidden');
    const body = document.getElementById('historyModalBody');
    body.innerHTML = '<p class="text-muted">Fetching saved test runs and bug reports...</p>';

    try {
      const resp = await fetch('/api/history');
      const data = await resp.json();
      
      let html = '<h4>📋 Saved Test Suites</h4><div style="margin-bottom: 20px;">';
      if (data.suites && data.suites.length) {
        html += '<ul style="list-style: none; padding: 0;">';
        data.suites.forEach(s => {
          html += `<li style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between;">
            <span><b>${s.feature_name}</b> (${s.scope})</span>
            <span style="color: #06b6d4;">${s.data.test_cases.length} cases</span>
          </li>`;
        });
        html += '</ul>';
      } else {
        html += '<p style="color: #64748b;">No test suites saved yet.</p>';
      }
      html += '</div>';

      html += '<h4>🐛 Stored Bug & RCA Reports</h4><div>';
      if (data.bugs && data.bugs.length) {
        html += '<ul style="list-style: none; padding: 0;">';
        data.bugs.forEach(b => {
          html += `<li style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between;">
            <span><b>${b.data.bug_title}</b></span>
            <span style="color: #f43f5e;">${b.data.severity}</span>
          </li>`;
        });
        html += '</ul>';
      } else {
        html += '<p style="color: #64748b;">No bug reports recorded yet.</p>';
      }
      html += '</div>';

      body.innerHTML = html;
    } catch (err) {
      body.innerHTML = '<p style="color: #f43f5e;">Failed to load history data.</p>';
    }
  });

  closeHistoryBtn?.addEventListener('click', () => {
    historyModal.classList.add('hidden');
  });

  historyModal?.addEventListener('click', (e) => {
    if (e.target === historyModal) historyModal.classList.add('hidden');
  });
}

/* ─── HELPER: DOWNLOAD TEXT FILE ─── */
function downloadTextFile(filename, text, mimeType = 'text/plain') {
  const blob = new Blob([text], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Downloaded ${filename}`, 'success');
}
