const API_BASE_URL = "https://teamdsa3-fake-internship-job-scam-9aem.onrender.com";

async function analyzeJob(payload) {
  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
  return res.json();
}

async function checkDomain(domain) {
  const res = await fetch(`${API_BASE_URL}/domain-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain }),
  });
  if (!res.ok) throw new Error(`Domain check failed: ${res.status}`);
  return res.json();
}

async function getDashboardStats() {
  const res = await fetch(`${API_BASE_URL}/dashboard`);
  if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.status}`);
  return res.json();
}

async function submitReport(payload) {
  const res = await fetch(`${API_BASE_URL}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Report submission failed: ${res.status}`);
  return res.json();
}

async function checkRecruiter(payload) {
  const res = await fetch(`${API_BASE_URL}/recruiter-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Recruiter check failed: ${res.status}`);
  return res.json();
}
