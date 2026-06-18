const BACKEND_URL = "https://teamdsa3-fake-internship-job-scam-x9bm.onrender.com";
 
async function checkJob() {
  const url        = document.getElementById("jobUrl")?.value.trim() || "";
  const title      = document.getElementById("jobTitle")?.value.trim() || "";
  const description = document.getElementById("jobDescription")?.value.trim() || "";
 
  if (!url && !title && !description) {
    alert("Please enter at least a job URL, title, or description.");
    return;
  }
 
  // Extract domain from URL for the domain-check call
  let domain = "";
  try {
    if (url) domain = new URL(url).hostname.replace("www.", "");
  } catch (_) {}
 
  // Show loading state
  setResult("scamScoreValue", "...");
  setResult("riskLevelValue", "...");
  setResult("domainTrustValue", "...");
 
  try {
    // Run analyze + domain-check in parallel
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
 
    const analyze = await analyzeRes.json();
    const domainData = domainRes ? await domainRes.json() : null;
 
    // Scam score
    const score = Math.round(analyze.scam_score ?? 0);
    setResult("scamScoreValue", `${score} / 100`);
 
    // Risk level
    let risk = "Low";
    if (score >= 70) risk = "High";
    else if (score >= 35) risk = "Medium";
    setResult("riskLevelValue", risk);
 
    // Domain trust
    if (domainData) {
      const trust = domainData.is_suspicious ? "Suspicious" : "Looks OK";
      setResult("domainTrustValue", trust);
    } else {
      setResult("domainTrustValue", "N/A");
    }
 
    // Show reasons if any
    if (analyze.reasons?.length) {
      console.info("Scam flags:", analyze.reasons);
    }
 
  } catch (err) {
    console.error("checkJob error:", err);
    setResult("scamScoreValue", "Error");
    setResult("riskLevelValue", "Error");
    setResult("domainTrustValue", "Error");
    alert("Could not reach the analysis server. Please try again.");
  }
}
 
function setResult(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
