const form = document.getElementById("verifyForm");
const result = document.getElementById("verifyResult");

function setResult(type, title, message) {
  result.className = `verify-result ${type}`;
  result.innerHTML = `
    <span class="result-orb"></span>
    <strong>${title}</strong>
    <p>${message}</p>
  `;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const name = document.getElementById("recruiterName").value.trim();
  const company = document.getElementById("companyName").value.trim();
  const contact = document.getElementById("recruiterContact").value.trim();
  const jobLink = document.getElementById("jobLink").value.trim();
  const combined = `${name} ${company} ${contact} ${jobLink}`.toLowerCase();

  if (!name || !company || !contact) {
    setResult(
      "warning",
      "More details needed",
      "Add recruiter name, company name, and contact details before trusting this opportunity."
    );
    return;
  }

  const riskySignals = [
    "whatsapp",
    "telegram",
    "registration fee",
    "joining fee",
    "security deposit",
    "paytm",
    "urgent",
  ];

  const hasRisk = riskySignals.some((signal) => combined.includes(signal));
  const hasCompanyEmail = contact.includes("@") && company.length > 2;

  if (hasRisk) {
    setResult(
      "danger",
      "High-risk recruiter signal",
      "This submission contains common scam indicators. Verify the official company domain before continuing."
    );
    return;
  }

  if (!hasCompanyEmail) {
    setResult(
      "warning",
      "Manual review recommended",
      "The contact does not look like a company email. Confirm the recruiter through official company channels."
    );
    return;
  }

  setResult(
    "safe",
    "No obvious red flags",
    "The submitted details passed the basic front-end checks. Continue with domain and identity verification."
  );
});
