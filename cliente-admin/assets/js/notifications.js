import { API } from "./api.js";
import { $, el, fmt } from "./utils.js";
import { logger } from "./utils.js";

class NotificationManager {
	constructor() {
		this.alerts = [];
		this.callbacks = new Map();
	}

	async loadAlerts(onClickCallback) {
		try {
			this.alerts = await API.alertas();
			this.renderAlerts(onClickCallback);
			return this.alerts;
		} catch (error) {
			logger.error("Failed to load alerts:", error);
			return [];
		}
	}

	renderAlerts(onClickCallback) {
		const list = $("#alertList");
		if (!list) return;

		list.innerHTML = "";

		const sortedAlerts = [...this.alerts].sort((a, b) => b.fecha_creacion - a.fecha_creacion);

		sortedAlerts.forEach((alert) => {
			const li = el("li", { className: "alert-item" });
			li.innerHTML = `
        <span class="badge ${alert.nivel}"></span>
        <div>
          <div><strong>#${alert.alerta_id}</strong> • ${alert.mensaje}</div>
          <div class="muted">${fmt.time(alert.fecha_creacion)}</div>
        </div>
        <button class="btn btn-ghost" data-alert-id="${alert.alerta_id}">Ver</button>
      `;

			li.addEventListener("click", (e) => {
				if (e.target.tagName === "BUTTON") {
					e.stopPropagation();
				}
				if (onClickCallback) {
					onClickCallback(alert);
				}
			});

			list.appendChild(li);
		});
	}

	async resolveAlert(alertId) {
		try {
			await API.resolverAlerta(alertId);
			this.alerts = this.alerts.filter((a) => a.alerta_id !== alertId);
			logger.info(`Alert ${alertId} resolved`);
			return true;
		} catch (error) {
			logger.error("Failed to resolve alert:", error);
			return false;
		}
	}

	getAlertStats() {
		return {
			total: this.alerts.length,
			criticas: this.alerts.filter((a) => a.nivel === "critica").length,
			altas: this.alerts.filter((a) => a.nivel === "alta").length,
			medias: this.alerts.filter((a) => a.nivel === "media").length,
		};
	}
}

export const notificationManager = new NotificationManager();
