const BACKEND_URL = "https://teamdsa3-fake-internship-job-scam-9aem.onrender.com";

const reportForm   = document.getElementById("reportForm");
const reportResult = document.getElementById("reportResult");

function setReportResult(type, title, message) {
  reportResult.className = `report-result ${type}`;
  reportResult.innerHTML = `
    <span class="result-orb"></span>
    <strong>${title}</strong>
    <p>${message}</p>
  `;
}

reportForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const title   = document.getElementById("reportTitle").value.trim();
  const company = document.getElementById("reportCompany").value.trim();
  const contact = document.getElementById("reportContact").value.trim();
  const type    = document.getElementById("reportType").value.trim();
  const details = document.getElementById("reportDetails").value.trim();

  if (!title || !company || !contact || !type) {
    setReportResult("warning", "More information needed",
      "Add the job title, company or recruiter, suspicious contact, and scam type before submitting.");
    return;
  }

  setReportResult("ready", "Submitting...", "Sending your report to the server.");

  try {
    const res = await fetch(`${BACKEND_URL}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_title:    title,
        company_name: company,
        description:  `Type: ${type}\nContact: ${contact}\n\n${details}`,
        reason:       type,
        evidence_url: contact.startsWith("http") ? contact : "",
      }),
    });

    const data = await res.json();

    if (res.ok) {
      setReportResult("success", "Report submitted",
        data.message || "Thank you. Your report is now in the review queue.");
      reportForm.reset();
    } else {
      setReportResult("warning", "Submission issue",
        data.detail || data.message || "Something went wrong. Please try again.");
    }
  } catch (err) {
    console.error("report submit error:", err);
    setReportResult("warning", "Could not connect",
      "The server could not be reached. Please try again in a moment.");
  }
});
