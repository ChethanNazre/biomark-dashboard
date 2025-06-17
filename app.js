let chart; // store chart reference

document.getElementById("reportSelect").addEventListener("change", (e) => {
  loadDashboard(`/${e.target.value}`); // 👈 Now this gives /biomarkers1.json
});

function loadDashboard(filePath) {
  fetch(filePath)
    .then(response => response.json())
    .then(data => {
      const biomarkers = data.biomarkers;
      const patient = data.patient;

      // Update patient info
      document.getElementById("patientInfo").innerHTML =
        `<strong>Patient:</strong> ${patient.name} | 
         <strong>Age:</strong> ${patient.age} | 
         <strong>Date:</strong> ${patient.date}`;

      const labels = Object.keys(biomarkers);
      const values = labels.map(k => biomarkers[k].value);

      const backgroundColors = labels.map(k => {
        const val = biomarkers[k].value;
        const low = biomarkers[k].low;
        const high = biomarkers[k].high;
        if (low !== undefined && high !== undefined) {
          return (val < low || val > high)
            ? 'rgba(255, 99, 132, 0.6)' // Red for out-of-range
            : 'rgba(75, 192, 192, 0.6)'; // Green for normal
        }
        return 'gray';
      });

      const ctx = document.getElementById("biomarkerChart").getContext("2d");

      if (chart) chart.destroy();

      chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: "Biomarker Levels",
            data: values,
            backgroundColor: backgroundColors,
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const biomarker = biomarkers[ctx.label];
                  return `${ctx.label}: ${biomarker.value} ${biomarker.unit} (Normal: ${biomarker.reference_range})`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Value'
              }
            }
          }
        }
      });
    });
}

// ✅ Load initial report on page load
loadDashboard("/biomarkers1.json");
