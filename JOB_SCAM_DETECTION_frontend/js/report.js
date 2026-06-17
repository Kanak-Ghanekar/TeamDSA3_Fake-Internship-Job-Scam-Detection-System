const reportForm = document.getElementById("reportForm");
const reportResult = document.getElementById("reportResult");

function setReportResult(type, title, message) {
  reportResult.className = `report-result ${type}`;
  reportResult.innerHTML = `
    <span class="result-orb"></span>
    <strong>${title}</strong>
    <p>${message}</p>
  `;
}

reportForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const title = document.getElementById("reportTitle").value.trim();
  const company = document.getElementById("reportCompany").value.trim();
  const contact = document.getElementById("reportContact").value.trim();
  const type = document.getElementById("reportType").value.trim();
  const details = document.getElementById("reportDetails").value.trim();

  if (!title || !company || !contact || !type) {
    setReportResult(
      "warning",
      "More information needed",
      "Add the job title, company or recruiter, suspicious contact, and scam type before submitting."
    );
    return;
  }

  const detailMessage = details
    ? "Your report is ready for review with supporting details included."
    : "Your report is ready, but adding message details or payment context will make it stronger.";

  setReportResult("ready", "Report prepared", detailMessage);
  reportForm.reset();
});
