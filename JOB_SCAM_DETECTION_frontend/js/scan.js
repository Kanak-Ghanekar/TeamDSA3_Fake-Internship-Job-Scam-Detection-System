function checkJob() {
  const url = document.getElementById("jobUrl").value;

  if (!url) {
    alert("Please enter a job URL");
    return;
  }

  alert("ML Analysis API will be connected here later.");
}
