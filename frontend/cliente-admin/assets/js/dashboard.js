import { $, el, fmt } from "./utils.js";
import { API } from "./api.js";
import { authService, wireLogout } from "./auth.js";
import { chartManager } from "./charts.js";
import { mapManager } from "./map.js";
import { notificationManager } from "./notifications.js";

function bindUI() {
	const closeBtn = document.getElementById("btnCerrarDetalle");
	if (closeBtn) {
		closeBtn.addEventListener("click", () => document.getElementById("drawerDetalle").classList.remove("open"));
	}
}

async function init() {
	authService.requireAuth(); // Primero verifica si el usuario está autenticado
	wireLogout();

	chartManager.init();
	mapManager.init();
	bindUI();

	const user = authService.getUser() || {};
	document.getElementById("currentUser").textContent = user.username || "—";
	document.getElementById("familyName").textContent = user.familia_nombre || "Mi familia";

	await bootstrapData();
	startPolling();
}

let _miembros = [];
let _seriesCache = new Map();

/**
 * Carga los datos de un miembro en las gráficas principales del dashboard.
 * @param {object} member - El objeto del miembro de la familia.
 */
async function updateDashboardCharts(member) {
	if (!member) return;
	const pts = await getSeries(member.usuario_id);
	chartManager.updateSeries(pts);
	chartManager.updateActivity(pts);
	$("#metricTitle").textContent = `Métricas del día – ${member.nombre} ${member.apellido}`;
}

async function bootstrapData() {
	try {
		const [miembros, alertas] = await Promise.all([API.miembros(), API.alertas()]);
		_miembros = miembros;

		notificationManager.alerts = alertas;

		document.getElementById("statMiembros").textContent = fmt.int(miembros.length);
		const stats = notificationManager.getAlertStats();
		document.getElementById("statAlertas24").textContent = fmt.int(stats.total);
		document.getElementById("statCriticas").textContent = fmt.int(stats.criticas);

		const ul = document.getElementById("memberList");
		ul.innerHTML = "";
		miembros.forEach((m) => {
			const li = el("li", { className: "member-item" });
			const status = "ok";
			li.innerHTML = `
        <div><strong>${m.nombre} ${m.apellido}</strong> <span class="muted">(${m.rel})</span></div>
        <div class="right"><span class="dot ${status}"></span><button class="btn btn-ghost">Ver</button></div>
      `;
			li.addEventListener("click", () => openMember(m));
			ul.appendChild(li);
		});

		mapManager.updateMarkers(miembros, openMember);
		notificationManager.renderAlerts(openAlert);

		// Carga los datos del primer miembro en las gráficas al iniciar
		if (miembros.length > 0) {
			await updateDashboardCharts(miembros[0]);
		}
	} catch (error) {
		console.error("Error al cargar los datos del dashboard:", error);
		alert("No se pudieron cargar los datos de la familia.");
	}
}

async function getSeries(uid) {
	if (_seriesCache.has(uid)) return _seriesCache.get(uid);
	const pts = await API.series(uid);
	_seriesCache.set(uid, pts);
	return pts;
}

async function openMember(m) {
	// Actualiza las gráficas principales con los datos del miembro seleccionado
	await updateDashboardCharts(m);

	// Prepara y muestra la barra de detalles
	const pts = await getSeries(m.usuario_id);
	const lastPoint = pts.length > 0 ? pts[pts.length - 1] : null;
	openDetalleWith(m, lastPoint);

	mapManager.focusCoord([m.lat, m.lng]);
}

async function openAlert(alerta) {
	const m = _miembros.find((x) => x.usuario_id === alerta.usuario_id);
	if (!m) return;

	await updateDashboardCharts(m);

	const pts = await getSeries(m.usuario_id);
	const lastPoint = pts.length > 0 ? pts[pts.length - 1] : null;
	openDetalleWith(m, lastPoint, alerta);
	if (alerta.coord) mapManager.focusCoord(alerta.coord);
}

function openDetalleWith(member, lastPoint, alerta) {
	const drawer = document.getElementById("drawerDetalle");
	document.getElementById("detalleNombre").textContent = `${member.nombre} ${member.apellido}`;
	document.getElementById("detalleUsuario").textContent = `#${member.usuario_id}`;
	document.getElementById("detalleTimestamp").textContent = lastPoint ? fmt.time(lastPoint.ts) : "—";
	document.getElementById("detalleHR").textContent = lastPoint?.hr ?? "—";
	document.getElementById("detalleBP").textContent = lastPoint ? `${lastPoint.sys}/${lastPoint.dia}` : "—";
	document.getElementById("detalleSpO2").textContent = lastPoint?.spo2 ?? "—";
	document.getElementById("detalleAct").textContent = lastPoint?.act ?? "—";
	document.getElementById("detalleCoord").textContent = `${member.lat.toFixed(4)}, ${member.lng.toFixed(4)}`;
	drawer.classList.add("open");
}

function startPolling() {
	setInterval(async () => {
		try {
			_seriesCache.clear();
			await bootstrapData();
		} catch (e) {
			console.warn("Polling error", e);
		}
	}, 20000);
}

window.addEventListener("DOMContentLoaded", init);
