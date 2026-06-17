const chartColors = ["#2563eb", "#0f9f6e", "#d97706", "#dc2626", "#7c3aed"];

function escapeHtml(value) {
  return String(value ?? "Unknown").replace(/[&<>"']/g, (character) => {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[character];
  });
}

function getColumnValue(row, names) {
  for (const name of names) {
    if (row[name]) {
      return row[name];
    }
  }

  return "Unknown";
}

function countBy(rows, names) {
  return rows.reduce((counts, row) => {
    const value = getColumnValue(row, names);
    counts[value] = (counts[value] || 0) + 1;
    return counts;
  }, {});
}

function topEntries(counts, limit = 5) {
  return Object.entries(counts)
    .sort((first, second) => second[1] - first[1])
    .slice(0, limit);
}

function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
}

function renderTable(rows) {
  const table = document.getElementById("jobsTable");

  if (!table) {
    return;
  }

  if (!rows.length) {
    table.innerHTML = '<tr><td colspan="3">No job posts found.</td></tr>';
    return;
  }

  table.innerHTML = rows
    .slice(0, 10)
    .map((job) => {
      const title = getColumnValue(job, ["Job Title", "job_title", "title"]);
      const company = getColumnValue(job, ["Company", "company"]);
      const location = getColumnValue(job, ["Location", "location"]);

      return `
        <tr>
          <td>${escapeHtml(title)}</td>
          <td>${escapeHtml(company)}</td>
          <td>${escapeHtml(location)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderChart(canvasId, entries, label) {
  const canvas = document.getElementById(canvasId);

  if (!canvas || typeof Chart === "undefined") {
    return;
  }

  const labels = entries.length ? entries.map(([name]) => name) : ["No data"];
  const values = entries.length ? entries.map(([, count]) => count) : [0];

  new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: chartColors,
          borderRadius: 6,
          borderSkipped: false,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: "#687489",
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: "#687489",
            precision: 0,
          },
          grid: {
            color: "#edf1f6",
          },
        },
      },
    },
  });
}

async function loadDashboard() {
  const { data = [], count = 0, error } = await supabaseClient
    .from("job_posts")
    .select("*", {
      count: "exact",
    })
    .limit(200);

  if (error) {
    console.error("Dashboard load failed:", error);
    renderTable([]);
    return;
  }

  const companies = countBy(data, ["Company", "company"]);
  const locations = countBy(data, ["Location", "location"]);

  setText("totalJobs", count || data.length);
  setText("totalCompanies", Object.keys(companies).length);
  setText("totalLocations", Object.keys(locations).length);
  setText("totalReports", 0);

  renderTable(data);
  renderChart("companyChart", topEntries(companies), "Jobs by company");
  renderChart("locationChart", topEntries(locations), "Jobs by location");
}

loadDashboard();
