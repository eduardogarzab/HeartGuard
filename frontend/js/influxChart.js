import { sendXMLRequest } from "./xmlClient.js";
import { API_CONFIG } from "./config.js";

let charts = {};

// ====================================================
// Inicializa los gráficos en influx.html
// ====================================================
export async function initInfluxCharts() {
  const container = document.getElementById("influxMetrics");
  container.innerHTML = `
    <div class="charts-grid">
      <canvas id="chartHR"></canvas>
      <canvas id="chartSpO2"></canvas>
      <canvas id="chartHRV"></canvas>
      <canvas id="chartECG"></canvas>
    </div>
  `;

  charts = {
    hr: createChart("chartHR", "Frecuencia Cardíaca (BPM)", "rgba(255,99,132,0.8)"),
    spo2: createChart("chartSpO2", "SpO₂ (%)", "rgba(75,192,192,0.8)"),
    hrv: createChart("chartHRV", "HRV (ms)", "rgba(255,206,86,0.8)"),
    ecg: createChart("chartECG", "ECG (mV)", "rgba(54,162,235,0.8)"),
  };

  // Actualiza cada 5 segundos
  updateInfluxCharts();
  setInterval(updateInfluxCharts, 5000);
}

// ====================================================
// Crea un gráfico individual
// ====================================================
function createChart(canvasId, label, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label,
          data: [],
          borderColor: color,
          borderWidth: 2,
          fill: false,
          tension: 0.2,
        },
      ],
    },
    options: {
      scales: {
        x: { display: false },
        y: { beginAtZero: false },
      },
      plugins: { legend: { display: true } },
    },
  });
}

// ====================================================
// Solicita datos al microservicio Influx vía Gateway
// ====================================================
async function updateInfluxCharts() {
  const token = localStorage.getItem("jwt");
  try {
    const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}/influx/metrics`, "GET", "", token);
    const xml = new DOMParser().parseFromString(res, "application/xml");

    const timestamp = new Date().toLocaleTimeString();
    const hr = parseFloat(xml.querySelector("metric[name='heart_rate'] value")?.textContent || 0);
    const spo2 = parseFloat(xml.querySelector("metric[name='spo2'] value")?.textContent || 0);
    const hrv = parseFloat(xml.querySelector("metric[name='hrv'] value")?.textContent || 0);
    const ecg = parseFloat(xml.querySelector("metric[name='ecg'] value")?.textContent || 0);

    updateChart(charts.hr, hr, timestamp);
    updateChart(charts.spo2, spo2, timestamp);
    updateChart(charts.hrv, hrv, timestamp);
    updateChart(charts.ecg, ecg, timestamp);
  } catch (err) {
    console.error("Error actualizando métricas Influx:", err);
  }
}

// ====================================================
// Actualiza cada gráfico
// ====================================================
function updateChart(chart, value, label) {
  const data = chart.data.datasets[0].data;
  const labels = chart.data.labels;

  data.push(value);
  labels.push(label);

  if (data.length > 20) {
    data.shift();
    labels.shift();
  }

  chart.update();
}
