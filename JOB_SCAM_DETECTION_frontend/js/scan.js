const BACKEND_URL = "https://teamdsa3-fake-internship-job-scam-9aem.onrender.com";

async function checkJob() {
  const url         = document.getElementById("jobUrl")?.value.trim() || "";
  const title       = document.getElementById("jobTitle")?.value.trim() || "";
  const description = document.getElementById("jobDescription")?.value.trim() || "";

  if (!url && !title && !description) {
    alert("Please enter at least a job URL, title, or description.");
    return;
  }

  let domain = "";
  try {
    if (url) domain = new URL(url).hostname.replace("www.", "");
  } catch (_) {}

  // Show loading
  setResult("scamScoreValue", "...");
  setResult("riskLevelValue", "...");
  setResult("domainTrustValue", "...");
  const badge = document.querySelector("#resultCard .table-badge");
  if (badge) badge.textContent = "Analyzing...";

  const keywordContainer = document.getElementById("keywordContainer");
  if (keywordContainer) keywordContainer.innerHTML = "<p>Checking...</p>";

  try {
    const [analyzeRes, domainRes] = await Promise.all([
      fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: title,
          job_description: description,
          job_url: url,
          domain: domain,
        }),
      }),
      domain
        ? fetch(`${BACKEND_URL}/domain-check`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ domain }),
          })
        : Promise.resolve(null),
    ]);

    const analyze   = await analyzeRes.json();
    const domainData = domainRes ? await domainRes.json() : null;

    const score = Math.round(analyze.scam_score ?? 0);
    setResult("scamScoreValue", `${score} / 100`);

    let risk = "Low";
    if (score >= 70)      risk = "High";
    else if (score >= 35) risk = "Medium";
    setResult("riskLevelValue", risk);

    if (domainData) {
      setResult("domainTrustValue", domainData.is_suspicious ? "Suspicious" : "Trusted");
    } else {
      setResult("domainTrustValue", "N/A");
    }

    if (badge) badge.textContent = "Analysis complete";

    // Show warning keywords
    if (keywordContainer) {
      const reasons = analyze.reasons || [];
      if (reasons.length === 0) {
        keywordContainer.innerHTML = '<span class="keyword-tag safe">No suspicious keywords detected</span>';
      } else {
        keywordContainer.innerHTML = reasons
          .map(r => `<span class="keyword-tag danger">${r}</span>`)
          .join("");
      }
    }

    // Scroll to result
    document.getElementById("resultCard")?.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    console.error("checkJob error:", err);
    setResult("scamScoreValue", "Error");
    setResult("riskLevelValue", "Error");
    setResult("domainTrustValue", "Error");
    if (badge) badge.textContent = "Error";
    alert("Could not reach the analysis server. Please try again.");
  }
}

function setResult(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
