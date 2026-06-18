const BACKEND_URL = "https://teamdsa3-fake-internship-job-scam-9aem.onrender.com";

const form   = document.getElementById("verifyForm");
const result = document.getElementById("verifyResult");

function setResult(type, title, message) {
  result.className = `verify-result ${type}`;
  result.innerHTML = `
    <span class="result-orb"></span>
    <strong>${title}</strong>
    <p>${message}</p>
  `;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name     = document.getElementById("recruiterName").value.trim();
  const company  = document.getElementById("companyName").value.trim();
  const contact  = document.getElementById("recruiterContact").value.trim();
  const jobLink  = document.getElementById("jobLink")?.value.trim() || "";

  if (!name || !company || !contact) {
    setResult("warning", "More details needed",
      "Add recruiter name, company name, and contact details before verifying.");
    return;
  }

  setResult("ready", "Checking...", "Verifying recruiter details against the database.");

  try {
    const res = await fetch(`${BACKEND_URL}/recruiter-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name:         name,
        company:      company,
        email:        contact.includes("@") ? contact : undefined,
        linkedin_url: jobLink.includes("linkedin") ? jobLink : undefined,
      }),
    });

    const data = await res.json();
    const risk = data.risk_score ?? 0;

    if (risk >= 70) {
      setResult("danger", "High-risk recruiter signal",
        `Risk score: ${risk}/100. ${data.reasons?.join(". ") || "This recruiter shows common scam indicators."}`);
    } else if (risk >= 35) {
      setResult("warning", "Manual review recommended",
        `Risk score: ${risk}/100. ${data.reasons?.join(". ") || "Confirm the recruiter through official company channels."}`);
    } else {
      setResult("safe", "No obvious red flags",
        `Risk score: ${risk}/100. Details passed basic checks. Continue with domain and identity verification.`);
    }

  } catch (err) {
    console.error("verify error:", err);
    setResult("warning", "Could not connect",
      "The server could not be reached. Please try again in a moment.");
  }
});
