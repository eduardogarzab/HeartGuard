import { CONFIG } from "./config.js";
import { logger } from "./utils.js";

class MapManager {
	constructor() {
		this.map = null;
		this.markers = new Map();
	}

	init() {
		try {
			this.map = L.map("map").setView(CONFIG.MAP_DEFAULT_CENTER, CONFIG.MAP_DEFAULT_ZOOM);

			L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
				attribution: "© OpenStreetMap contributors",
			}).addTo(this.map);

			logger.info("Map initialized");
		} catch (error) {
			logger.error("Failed to initialize map:", error);
		}
	}

	setUserMarker(usuario, onClick) {
		const key = usuario.usuario_id;
		let marker = this.markers.get(key);

		if (!marker) {
			marker = L.marker([usuario.lat, usuario.lng]).addTo(this.map);
			this.markers.set(key, marker);
		} else {
			marker.setLatLng([usuario.lat, usuario.lng]);
		}

		marker.bindTooltip(`${usuario.nombre} ${usuario.apellido}`);
		marker.off("click");
		if (onClick) {
			marker.on("click", () => onClick(usuario));
		}

		return marker;
	}

	focusCoord([lat, lng], zoom = 14) {
		this.map.setView([lat, lng], zoom, { animate: true });
	}

	updateMarkers(members, onClickCallback) {
		members.forEach((member) => {
			this.setUserMarker(member, onClickCallback);
		});
	}

	destroy() {
		if (this.map) {
			this.map.remove();
			this.map = null;
		}
		this.markers.clear();
	}
}

export const mapManager = new MapManager();
