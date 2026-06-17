function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
}

function getColumnValue(row, names) {
  for (const name of names) {
    if (row[name]) {
      return row[name];
    }
  }

  return null;
}

async function loadHomePage() {
  const { data = [], count = 0, error } = await supabaseClient
    .from("job_posts")
    .select("*", {
      count: "exact",
    })
    .limit(200);

  if (error) {
    console.error("Homepage stats failed:", error);
    return;
  }

  const companies = new Set();
  const locations = new Set();

  data.forEach((job) => {
    const company = getColumnValue(job, ["Company", "company"]);
    const location = getColumnValue(job, ["Location", "location"]);

    if (company) {
      companies.add(company);
    }

    if (location) {
      locations.add(location);
    }
  });

  setText("totalJobs", count || data.length);
  setText("totalCompanies", companies.size);
  setText("totalLocations", locations.size);
}

function checkJob() {
  const url = document.getElementById("jobUrl").value.trim();

  if (!url) {
    alert("Please enter a Job URL");
    return;
  }

  const keywords = [
    "Contact HR on WhatsApp",
    "Registration Fee",
    "Immediate Joining",
    "Work From Home",
  ];

  document.getElementById("resultCard").style.display = "block";
  document.getElementById("keywordSection").style.display = "block";

  const container = document.getElementById("keywordContainer");

  container.innerHTML = "";

  keywords.forEach((word) => {
    container.innerHTML += `
      <span class="keyword">
        Alert: ${word}
      </span>
    `;
  });
}

loadHomePage();
