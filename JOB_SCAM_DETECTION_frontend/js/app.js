async function loadHomePage() {
  const { data, count } = await supabaseClient
    .from("job_posts")
    .select("*", {
      count: "exact",
    })
    .limit(10);

  document.getElementById("totalJobs").textContent = count;

  const table = document.getElementById("jobsTable");

  data.forEach((job) => {
    table.innerHTML += `
        <tr>
            <td>${job["Job Title"]}</td>
            <td>${job["Company"]}</td>
            <td>${job["Location"]}</td>
        </tr>
        `;
  });
}

loadHomePage();
