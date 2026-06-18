const BACKEND_URL  = "https://teamdsa3-fake-internship-job-scam-9aem.onrender.com";
const chartColors  = ["#2563eb", "#0f9f6e", "#d97706", "#dc2626", "#7c3aed"];

// ── helpers ──────────────────────────────────────────────────────────────────
function escapeHtml(value) {
  return String(value ?? "Unknown").replace(/[&<>"']/g, c =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[c])
  );
}
function getCol(row, names) {
  for (const n of names) if (row[n]) return row[n];
  return "Unknown";
}
function countBy(rows, names) {
  return rows.reduce((acc, row) => {
    const v = getCol(row, names);
    acc[v] = (acc[v] || 0) + 1;
    return acc;
  }, {});
}
function topEntries(counts, limit = 5) {
  return Object.entries(counts).sort((a,b) => b[1]-a[1]).slice(0, limit);
}
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── recent jobs table ─────────────────────────────────────────────────────────
function renderJobsTable(rows) {
  const tbody = document.getElementById("jobsTable");
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3">No job posts found.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.slice(0, 10).map(job => `
    <tr>
      <td>${escapeHtml(getCol(job, ["Title","Job Title","job_title","title"]))}</td>
      <td>${escapeHtml(getCol(job, ["Company_name","Company","company"]))}</td>
      <td>${escapeHtml(getCol(job, ["Location","location"]))}</td>
    </tr>`).join("");
}

// ── scam alerts table ─────────────────────────────────────────────────────────
function riskBadge(score) {
  const s = Number(score) || 0;
  if (s >= 70) return '<span class="risk-badge high">★ HIGH RISK</span>';
  if (s >= 35) return '<span class="risk-badge suspicious">★ SUSPICIOUS</span>';
  return '<span class="risk-badge safe">★ SAFE</span>';
}
function scoreBar(score) {
  const s = Math.min(Number(score) || 0, 100);
  const color = s >= 70 ? "#dc2626" : s >= 35 ? "#d97706" : "#0f9f6e";
  return `<div style="display:flex;align-items:center;gap:6px">
    <span style="font-weight:600;min-width:28px">${s}</span>
    <div style="flex:1;height:4px;background:#edf1f6;border-radius:2px">
      <div style="width:${s}%;height:4px;background:${color};border-radius:2px"></div>
    </div>
  </div>`;
}
function renderScamTable(rows) {
  const tbody = document.getElementById("scamAlertsTable");
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6">No scam alerts found.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.slice(0, 6).map(row => {
    const score = Number(row.Scam_score ?? row.scam_score ?? 0);
    const date  = row.created_at ? new Date(row.created_at).toLocaleString() : "—";
    return `<tr>
      <td>${escapeHtml(getCol(row, ["Company_name","Company","company"]))}</td>
      <td>${escapeHtml(getCol(row, ["Title","job_title","title"]))}</td>
      <td>${scoreBar(score)}</td>
      <td>${riskBadge(score)}</td>
      <td style="font-size:11px;color:#687489">${escapeHtml(row.Domain_name || row.domain || "—")}</td>
      <td style="font-size:11px;color:#687489">${date}</td>
    </tr>`;
  }).join("");

  // pagination label
  const label = document.getElementById("scamAlertsPagination");
  if (label) label.textContent = `Showing 1–${Math.min(rows.length,6)} of ${rows.length} scam incidents`;
}

// ── charts ────────────────────────────────────────────────────────────────────
function renderChart(canvasId, entries, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;
  const labels = entries.length ? entries.map(([n]) => n) : ["No data"];
  const values = entries.length ? entries.map(([,c]) => c) : [0];
  new Chart(canvas, {
    type: "bar",
    data: { labels, datasets: [{ label, data: values,
      backgroundColor: chartColors, borderRadius: 6, borderSkipped: false }] },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#687489" } },
        y: { beginAtZero: true, ticks: { color: "#687489", precision: 0 },
             grid: { color: "#edf1f6" } },
      },
    },
  });
}

// ── ML metrics ────────────────────────────────────────────────────────────────
async function loadMLMetrics() {
  try {
    const res  = await fetch(`${BACKEND_URL}/model-metrics`);
    const data = await res.json();
    setText("mlAccuracy",  data.accuracy  + "%");
    setText("mlPrecision", data.precision + "%");
    setText("mlRecall",    data.recall    + "%");
    setText("mlF1",        data.f1_score  + "%");
    setText("mlConfidence", data.confidence + "%");
  } catch (_) {
    // keep static fallback values already in HTML
  }
}

// ── main ──────────────────────────────────────────────────────────────────────
async function loadDashboard() {
  // load scam alerts + job posts in parallel
  const [jobRes, scamRes] = await Promise.allSettled([
    supabaseClient.from("job_posts").select("*", { count: "exact" }).limit(200),
    supabaseClient.from("job_posts").select("*").eq("is_flagged", true).order("created_at", { ascending: false }).limit(50),
  ]);

  const jobs     = jobRes.status  === "fulfilled" ? (jobRes.value.data  || []) : [];
  const jobCount = jobRes.status  === "fulfilled" ? (jobRes.value.count || jobs.length) : jobs.length;
  const scams    = scamRes.status === "fulfilled" ? (scamRes.value.data || []) : [];

  const companies = countBy(jobs, ["Company_name","Company","company"]);
  const locations = countBy(jobs, ["Location","location"]);

  setText("totalJobs",      jobCount);
  setText("totalCompanies", Object.keys(companies).length);
  setText("totalLocations", Object.keys(locations).length);
  setText("totalReports",   0);

  renderJobsTable(jobs);
  renderScamTable(scams);
  renderChart("companyChart",  topEntries(companies), "Jobs by company");
  renderChart("locationChart", topEntries(locations), "Jobs by location");
  loadMLMetrics();
}

loadDashboard();
