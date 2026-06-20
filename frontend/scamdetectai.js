// Scam Detect AI — shared frontend engine
// Talks ONLY to the live FastAPI backend + Supabase. No embedded/sample data,
// no silent local fallback scoring — if the API is unreachable, callers get a
// thrown error with a clear message so the UI can show it honestly.

const API_BASE = (location.hostname === "" || location.protocol === "file:")
  ? "http://127.0.0.1:8000"
  : (window.SCAMDETECT_API_BASE || "http://127.0.0.1:8000");

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiRequest(path, options = {}, timeoutMs = 12000) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
      ...options,
    });
  } catch (err) {
    if (err.name === "TimeoutError" || err.name === "AbortError") {
      throw new ApiError("The server took too long to respond. Please try again.", 0);
    }
    throw new ApiError(
      `Can't reach the Scam Detect AI server at ${API_BASE}. Make sure the backend is running.`,
      0
    );
  }

  let body = null;
  try { body = await res.json(); } catch (_) { /* no body */ }

  if (!res.ok) {
    const msg =
      body?.error?.message ||
      body?.detail ||
      `Request failed (${res.status})`;
    throw new ApiError(msg, res.status);
  }
  return body;
}

// ── Risk helpers ──────────────────────────────────────────────────────────────
function riskLabel(score) {
  if (score <= 30) return { label: "LOW RISK", cls: "low" };
  if (score <= 60) return { label: "MEDIUM RISK", cls: "medium" };
  if (score <= 80) return { label: "HIGH RISK", cls: "high" };
  return { label: "CONFIRMED SCAM", cls: "scam" };
}

function scoreColor(s) {
  if (s > 80) return "var(--scam)";
  if (s > 60) return "var(--high)";
  if (s > 30) return "var(--medium)";
  return "var(--low)";
}

function scoreClass(s) {
  if (s > 80) return "scam";
  if (s > 60) return "high";
  if (s > 30) return "medium";
  return "low";
}

// ── API wrappers — all real, all live ─────────────────────────────────────────
async function analyzeJob(fields) {
  return apiRequest("/analyze", {
    method: "POST",
    body: JSON.stringify({
      title: fields.title,
      company_name: fields.company,
      job_description: fields.description,
      salary: fields.salary,
      location: fields.location,
      source_url: fields.url,
      domain: fields.domain,
      recruiter_email: fields.recruiterEmail,
    }),
  });
}

async function analyzeJobByUrl(url, recruiterEmail = "") {
  return apiRequest("/analyze-url", {
    method: "POST",
    body: JSON.stringify({ url, recruiter_email: recruiterEmail || null }),
  }, 20000); // scraping can take longer than a normal request
}

async function checkDomain(domainName) {
  return apiRequest("/domain-check", {
    method: "POST",
    body: JSON.stringify({ domain_name: domainName }),
  });
}

async function checkRecruiter(email, company) {
  return apiRequest("/recruiter-check", {
    method: "POST",
    body: JSON.stringify({ email, company_name: company }),
  });
}

async function listRecruiters() {
  return apiRequest("/recruiters", { method: "GET" });
}

async function submitReport(payload) {
  return apiRequest("/report", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function listReports() {
  return apiRequest("/reports", { method: "GET" });
}

async function fetchDashboard() {
  return apiRequest("/dashboard", { method: "GET" });
}

// ── DOM helpers ──────────────────────────────────────────────────────────────
function qs(sel, ctx = document) { return ctx.querySelector(sel); }
function qsa(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }

function toast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = `sr-toast sr-toast--${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add("show"), 10);
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 400); }, 4500);
}

function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.dataset.original = btn.dataset.original || btn.textContent;
  btn.textContent = loading ? "Analyzing…" : btn.dataset.original;
}

// ── Connection status indicator ────────────────────────────────────────────
async function checkApiHealth() {
  try {
    await apiRequest("/health", { method: "GET" }, 4000);
    return true;
  } catch (_) {
    return false;
  }
}

function renderApiStatus(targetSelector) {
  const el = qs(targetSelector);
  if (!el) return;
  checkApiHealth().then(ok => {
    el.textContent = ok ? "● Live" : "● Offline";
    el.className = `api-status ${ok ? "api-status--ok" : "api-status--down"}`;
    el.title = ok
      ? `Connected to ${API_BASE}`
      : `Cannot reach ${API_BASE}. Start the backend (uvicorn backend.main:app).`;
  });
}
