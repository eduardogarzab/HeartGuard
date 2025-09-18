import { CONFIG } from "./config.js";
import { logger } from "./utils.js";

// Datos de demo
const DEMO_DATA = {
	familia: { familia_id: 1, nombre: "Familia Garza" },
	members: [
		{ usuario_id: 11, nombre: "Eduardo", apellido: "Garza", rel: "Hijo", lat: 25.6869, lng: -100.3134 },
		{ usuario_id: 12, nombre: "Mariana", apellido: "Garza", rel: "Madre", lat: 25.6942, lng: -100.3249 },
		{ usuario_id: 13, nombre: "Carlos", apellido: "Garza", rel: "Padre", lat: 25.6811, lng: -100.3112 },
		{ usuario_id: 14, nombre: "Ana", apellido: "Garza", rel: "Hermana", lat: 25.6905, lng: -100.3291 },
	],
	series: {
		11: generateTimeSeries(11),
		12: generateTimeSeries(12),
		13: generateTimeSeries(13),
		14: generateTimeSeries(14),
	},
	alerts: [
		{ alerta_id: 101, usuario_id: 11, nivel: "media", mensaje: "FC elevada tras actividad (145 bpm)", fecha_creacion: Date.now() - 1200000, coord: [25.6869, -100.3134] },
		{ alerta_id: 102, usuario_id: 12, nivel: "alta", mensaje: "Presión arterial 162/104 mmHg", fecha_creacion: Date.now() - 600000, coord: [25.6942, -100.3249] },
		{ alerta_id: 103, usuario_id: 14, nivel: "critica", mensaje: "SpO₂ baja 88%", fecha_creacion: Date.now() - 300000, coord: [25.6905, -100.3291] },
	],
};

// Generar series de tiempo realistas
function generateTimeSeries(userId) {
	const series = [];
	const activities = ["Reposo", "Caminar", "Activo"];
	const baseHR = 60 + (userId % 20);

	for (let i = 12; i >= 0; i--) {
		const activity = activities[Math.floor(Math.random() * activities.length)];
		const hrVariation = activity === "Activo" ? 15 : activity === "Caminar" ? 8 : 0;

		series.push({
			ts: Date.now() - (i * 3600000) / 4, // Cada 15 minutos
			hr: baseHR + hrVariation + Math.floor(Math.random() * 10 - 5),
			sys: 110 + Math.floor(Math.random() * 30),
			dia: 70 + Math.floor(Math.random() * 20),
			spo2: 94 + Math.floor(Math.random() * 6),
			act: activity,
		});
	}

	return series;
}

// Cliente HTTP con interceptores
class ApiClient {
	constructor(baseURL) {
		this.baseURL = baseURL;
	}

	async request(path, options = {}) {
		const token = localStorage.getItem("jwt");
		const headers = {
			"Content-Type": "application/json",
			...(token ? { Authorization: `Bearer ${token}` } : {}),
			...options.headers,
		};

		try {
			const response = await fetch(`${this.baseURL}${path}`, {
				...options,
				headers,
			});

			if (!response.ok) {
				throw new Error(`${response.status} ${response.statusText}`);
			}

			return response.status === 204 ? null : response.json();
		} catch (error) {
			logger.error("API Error:", error);
			throw error;
		}
	}

	get(path) {
		return this.request(path, { method: "GET" });
	}

	post(path, data) {
		return this.request(path, {
			method: "POST",
			body: JSON.stringify(data),
		});
	}

	put(path, data) {
		return this.request(path, {
			method: "PUT",
			body: JSON.stringify(data),
		});
	}

	delete(path) {
		return this.request(path, { method: "DELETE" });
	}
}

const apiClient = new ApiClient(CONFIG.API_BASE_URL);

// API pública con modo demo
export const API = {
	async login(username, password) {
		if (CONFIG.DEMO_MODE) {
			if (username === "maria_admin" && password === "admin123") {
				const user = {
					username,
					rol: "admin_familia",
					familia_id: DEMO_DATA.familia.familia_id,
					familia_nombre: DEMO_DATA.familia.nombre,
				};
				return { token: "demo.token." + Date.now(), user };
			}
			throw new Error("Credenciales inválidas");
		}
		return apiClient.post("/api/v1/login", { username, password });
	},

	async familia() {
		if (CONFIG.DEMO_MODE) return DEMO_DATA.familia;
		return apiClient.get("/api/v1/mi-familia");
	},

	async miembros() {
		if (CONFIG.DEMO_MODE) return DEMO_DATA.members;
		return apiClient.get("/api/v1/mi-familia/miembros");
	},

	async series(usuario_id) {
		if (CONFIG.DEMO_MODE) {
			// Simular actualización de datos en tiempo real
			if (Math.random() > 0.7) {
				const series = DEMO_DATA.series[usuario_id];
				if (series && series.length > 0) {
					const lastPoint = series[series.length - 1];
					const newPoint = {
						...lastPoint,
						ts: Date.now(),
						hr: lastPoint.hr + Math.floor(Math.random() * 6 - 3),
						sys: lastPoint.sys + Math.floor(Math.random() * 10 - 5),
						dia: lastPoint.dia + Math.floor(Math.random() * 8 - 4),
						spo2: Math.max(90, Math.min(100, lastPoint.spo2 + Math.floor(Math.random() * 4 - 2))),
					};
					series.push(newPoint);
					if (series.length > 20) series.shift(); // Mantener máximo 20 puntos
				}
			}
			return DEMO_DATA.series[usuario_id] || [];
		}
		return apiClient.get(`/api/v1/usuarios/${usuario_id}/metricas?last_hours=12`);
	},

	async alertas() {
		if (CONFIG.DEMO_MODE) return DEMO_DATA.alerts;
		return apiClient.get("/api/v1/mi-familia/alertas?range=24h");
	},

	async resolverAlerta(id) {
		if (CONFIG.DEMO_MODE) {
			const index = DEMO_DATA.alerts.findIndex((a) => a.alerta_id === id);
			if (index !== -1) {
				DEMO_DATA.alerts.splice(index, 1);
				return { ok: true };
			}
			throw new Error("Alerta no encontrada");
		}
		return apiClient.put(`/api/v1/alertas/${id}/resolver`);
	},
};
