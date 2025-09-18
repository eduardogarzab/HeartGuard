import { $ } from "./utils.js";
import { CONFIG } from "./config.js";

class ChartManager {
	constructor() {
		this.charts = {};
	}

	init() {
		this.initVitalsChart();
		this.initActivityChart();
		this.initMiniChart();
	}

	initVitalsChart() {
		this.charts.vitals = new Chart($("#chartVitals"), {
			type: "line",
			data: {
				labels: [],
				datasets: [
					{
						label: "HR (bpm)",
						data: [],
						borderColor: "#5b8cff",
						backgroundColor: "rgba(91, 140, 255, 0.1)",
						tension: 0.3,
						yAxisID: "y",
					},
					{
						label: "SpO₂ (%)",
						data: [],
						borderColor: "#2bb673",
						backgroundColor: "rgba(43, 182, 115, 0.1)",
						tension: 0.3,
						yAxisID: "y1",
					},
					{
						label: "Sys (mmHg)",
						data: [],
						borderColor: "#ff5d73",
						backgroundColor: "rgba(255, 93, 115, 0.1)",
						tension: 0.3,
						yAxisID: "y2",
					},
					{
						label: "Dia (mmHg)",
						data: [],
						borderColor: "#f6c445",
						backgroundColor: "rgba(246, 196, 69, 0.1)",
						tension: 0.3,
						yAxisID: "y2",
					},
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				animation: {
					duration: CONFIG.CHART_UPDATE_ANIMATION_DURATION,
				},
				plugins: {
					legend: { position: "bottom" },
					tooltip: {
						mode: "index",
						intersect: false,
					},
				},
				scales: {
					y: {
						type: "linear",
						position: "left",
						title: { display: true, text: "HR (bpm)" },
					},
					y1: {
						type: "linear",
						position: "right",
						title: { display: true, text: "SpO₂ (%)" },
						grid: { drawOnChartArea: false },
						min: 85,
						max: 100,
					},
					y2: {
						type: "linear",
						position: "right",
						display: false,
						min: 50,
						max: 200,
					},
				},
			},
		});
	}

	initActivityChart() {
		this.charts.activity = new Chart($("#chartActivity"), {
			type: "doughnut",
			data: {
				labels: ["Reposo", "Caminar", "Activo"],
				datasets: [
					{
						data: [0, 0, 0],
						backgroundColor: ["#5b8cff", "#2bb673", "#f6c445"],
						borderColor: "#121a33",
						borderWidth: 2,
					},
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				animation: {
					duration: CONFIG.CHART_UPDATE_ANIMATION_DURATION,
				},
				plugins: {
					legend: { position: "bottom" },
				},
			},
		});
	}

	initMiniChart() {
		this.charts.mini = new Chart($("#chartUserMini"), {
			type: "line",
			data: {
				labels: [],
				datasets: [
					{
						label: "HR (bpm)",
						data: [],
						borderColor: "#5b8cff",
						backgroundColor: "rgba(91, 140, 255, 0.1)",
						tension: 0.3,
					},
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				animation: {
					duration: CONFIG.CHART_UPDATE_ANIMATION_DURATION,
				},
				plugins: {
					legend: { display: false },
				},
			},
		});
	}

	updateSeries(points) {
		const labels = points.map((p) =>
			new Date(p.ts).toLocaleTimeString("es-MX", {
				hour: "2-digit",
				minute: "2-digit",
			})
		);

		const hr = points.map((p) => p.hr);
		const spo2 = points.map((p) => p.spo2);
		const sys = points.map((p) => p.sys);
		const dia = points.map((p) => p.dia);

		this.charts.vitals.data.labels = labels;
		this.charts.vitals.data.datasets[0].data = hr;
		this.charts.vitals.data.datasets[1].data = spo2;
		this.charts.vitals.data.datasets[2].data = sys;
		this.charts.vitals.data.datasets[3].data = dia;
		this.charts.vitals.update();

		this.charts.mini.data.labels = labels;
		this.charts.mini.data.datasets[0].data = hr;
		this.charts.mini.update();
	}

	updateActivity(points) {
		const counts = { Reposo: 0, Caminar: 0, Activo: 0 };
		points.forEach((p) => (counts[p.act] = (counts[p.act] || 0) + 1));

		this.charts.activity.data.datasets[0].data = [counts.Reposo, counts.Caminar, counts.Activo];
		this.charts.activity.update();
	}

	destroy() {
		Object.values(this.charts).forEach((chart) => chart.destroy());
		this.charts = {};
	}
}

export const chartManager = new ChartManager();
