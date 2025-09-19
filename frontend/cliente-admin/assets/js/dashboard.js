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
let _selectedMember = null;

function openModal(id) {
	const m = document.getElementById(id);
	if (m) m.classList.add("active");
}
function closeModal(id) {
	const m = document.getElementById(id);
	if (m) m.classList.remove("active");
}

function wireModalsGlobal() {
	document.body.addEventListener("click", (e) => {
		const btn = e.target.closest("[data-close-modal]");
		if (btn) {
			closeModal(btn.getAttribute("data-close-modal"));
		}
	});
	document.addEventListener("keydown", (e) => {
		if (e.key === "Escape") {
			document.querySelectorAll(".modal.active").forEach((m) => m.classList.remove("active"));
		}
	});
}

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
			li.addEventListener("click", () => {
				document.querySelectorAll(".member-item.selected").forEach((x) => x.classList.remove("selected"));
				li.classList.add("selected");
				_selectedMember = m;
				openMember(m);
			});
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

// Invitaciones
async function generarInvitacion() {
	const role = document.getElementById("roleSelect").value;
	const btn = document.getElementById("btnGenerarInvitacion");
	btn.disabled = true;
	btn.textContent = "Generando...";
	try {
		const res = await API.invitarMiembro(role);
		document.getElementById("inviteLink").value = res.url;
		const mins = Math.round((res.expira_en - Date.now()) / 60000);
		document.getElementById("inviteExpire").textContent = `Expira en ${mins} min`;
		document.getElementById("inviteResult").classList.remove("hidden");
	} catch (e) {
		alert("No fue posible generar la invitación");
	} finally {
		btn.disabled = false;
		btn.textContent = "Generar enlace";
	}
}

function copiarInvitacion() {
	const input = document.getElementById("inviteLink");
	if (!input.value) return;
	navigator.clipboard.writeText(input.value).then(() => {
		const old = input.value;
		const btn = document.getElementById("btnCopiarInv");
		const prev = btn.textContent;
		btn.textContent = "Copiado";
		setTimeout(() => (btn.textContent = prev), 1400);
	});
}

async function compartirInvitacion() {
	const link = document.getElementById("inviteLink").value;
	if (!link) return;
	if (navigator.share) {
		try {
			await navigator.share({ title: "Invitación HeartGuard", text: "Únete a mi familia en HeartGuard", url: link });
		} catch {}
	} else {
		copiarInvitacion();
	}
}

// Eliminación
function solicitarEliminar() {
	// Poblar select con miembros actuales (excluye quizás al admin logueado si se desea, por ahora todos)
	const sel = document.getElementById("selectEliminar");
	if (!sel) return;
	sel.innerHTML = "";
	_miembros.forEach((m) => {
		const opt = document.createElement("option");
		opt.value = m.usuario_id;
		opt.textContent = `${m.nombre} ${m.apellido} (${m.rel})`;
		sel.appendChild(opt);
	});
	openModal("modalEliminar");
}

async function confirmarEliminar() {
	const sel = document.getElementById("selectEliminar");
	if (!sel || !sel.value) {
		return;
	}
	const usuarioId = parseInt(sel.value, 10);
	const btn = document.getElementById("btnConfirmEliminar");
	btn.disabled = true;
	btn.textContent = "Eliminando...";
	try {
		await API.eliminarMiembro(usuarioId);
		closeModal("modalEliminar");
		_seriesCache.clear();
		await bootstrapData();
		if (_selectedMember && _selectedMember.usuario_id === usuarioId) {
			_selectedMember = null;
		}
	} catch (e) {
		alert("No se pudo eliminar");
	} finally {
		btn.disabled = false;
		btn.textContent = "Eliminar";
	}
}

function wireActions() {
	const gen = document.getElementById("btnGenerarInvitacion");
	if (gen) gen.addEventListener("click", generarInvitacion);
	const copy = document.getElementById("btnCopiarInv");
	if (copy) copy.addEventListener("click", copiarInvitacion);
	const share = document.getElementById("btnCompartirInv");
	if (share) share.addEventListener("click", compartirInvitacion);
	const confirm = document.getElementById("btnConfirmEliminar");
	if (confirm) confirm.addEventListener("click", confirmarEliminar);

	// Botones que podrían estar en headers (si existen)
	const btnOpenInv = document.getElementById("btnOpenInvModal");
	if (btnOpenInv) btnOpenInv.addEventListener("click", () => openModal("modalInvitacion"));
	const btnSolicitarElim = document.getElementById("btnOpenDeleteModal");
	if (btnSolicitarElim) btnSolicitarElim.addEventListener("click", solicitarEliminar);

	// Icon buttons en card miembros
	const addMember = document.getElementById("btnAddMember");
	if (addMember) addMember.addEventListener("click", () => openModal("modalInvitacion"));
	const removeMember = document.getElementById("btnRemoveMember");
	if (removeMember) removeMember.addEventListener("click", solicitarEliminar);
}

wireModalsGlobal();
wireActions();

window.addEventListener("DOMContentLoaded", init);
