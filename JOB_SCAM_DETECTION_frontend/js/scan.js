function extractDomain(url) {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return url.split("//").pop().split("/")[0].replace("www.", "");
  }
}

async function checkJob() {
  const url = document.getElementById("jobUrl").value.trim();
  const title = document.getElementById("jobTitle").value.trim();
  const description = document.getElementById("jobDescription").value.trim();

  if (!url && !title && !description) {
    alert("Please enter at least a job URL, title, or description");
    return;
  }

  const badge = document.querySelector("#resultCard .table-badge");
  badge.textContent = "Checking...";

  try {
    const domain = url ? extractDomain(url) : "";

    const analysis = await analyzeJob({
      job_title: title || null,
      job_description: description || null,
      job_url: url || null,
      domain: domain || null,
    });

    const domainResult = domain ? await checkDomain(domain) : null;

    document.getElementById("scamScoreValue").textContent = `${analysis.scam_score}/100`;
    document.getElementById("riskLevelValue").textContent = analysis.is_flagged ? "High Risk" : "Low Risk";
    document.getElementById("domainTrustValue").textContent = domainResult
      ? (domainResult.is_suspicious ? "Suspicious" : "Trusted")
      : "Not checked";

    const keywordContainer = document.getElementById("keywordContainer");
    keywordContainer.innerHTML = "";
    const reasons = [...(analysis.reasons || []), ...((domainResult && domainResult.reasons) || [])];

    if (reasons.length === 0) {
      keywordContainer.innerHTML = "<p>No suspicious signals detected.</p>";
    } else {
      reasons.forEach((reason) => {
        const tag = document.createElement("span");
        tag.className = "keyword-tag";
        tag.textContent = reason;
        keywordContainer.appendChild(tag);
      });
    }

    badge.textContent = "Result ready";
  } catch (err) {
    console.error(err);
    badge.textContent = "Error";
    alert("Something went wrong checking this job. Please try again in a moment.");
  }
}
