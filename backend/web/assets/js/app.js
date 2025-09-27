/* HeartGuard Superadmin Panel (vanilla JS SPA)
   - Grid de módulos (tiles) en Home
   - Router por hash (#/module)
   - Vistas modulares con tabs internas
   - Fetch helpers con auth demo (X-Demo-Superadmin) o Bearer
   - Toasts, modales y feedback
*/

const CONFIG = {
	BASE_URL: localStorage.getItem("hg_base") || "", // vacío = mismo host/puerto
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

/* ---------- THEME ---------- */
(function initTheme() {
	const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
	const saved = localStorage.getItem("theme");
	document.documentElement.setAttribute("data-theme", saved || (prefersDark ? "dark" : "light"));
})();

$("#themeToggle")?.addEventListener("click", () => {
	const cur = document.documentElement.getAttribute("data-theme");
	const next = cur === "dark" ? "light" : "dark";
	document.documentElement.setAttribute("data-theme", next);
	localStorage.setItem("theme", next);
});

/* ---------- ENV UI ---------- */
function updateEnvLabel() {
	const label = CONFIG.BASE_URL || window.location.origin + " (same-origin)";
	$("#envBase").textContent = label;
}
updateEnvLabel();

/* ---------- AUTH MODE ---------- */
const authMode = $("#authMode"); // checkbox -> demo header / bearer
const bearerToken = $("#bearerToken");

authMode.addEventListener("change", () => {
	toast("Modo auth", authMode.checked ? "Demo header" : "Bearer", "info");
});
bearerToken.value = localStorage.getItem("hg_bearer") || "let-me-in";
bearerToken.addEventListener("input", () => {
	localStorage.setItem("hg_bearer", bearerToken.value);
});

/* ---------- REFRESH ---------- */
$("#refreshBtn")?.addEventListener("click", () => Router.render());

/* ---------- TOASTS ---------- */
function toast(title, msg, type = "ok") {
	const root = $("#toastRoot");
	const el = document.createElement("div");
	el.className = `toast ${type === "error" ? "err" : "ok"}`;
	el.innerHTML = `
    <span class="material-symbols-rounded">${type === "error" ? "error" : "check_circle"}</span>
    <div>
      <div style="font-weight:600">${title}</div>
      <div style="opacity:.85">${msg}</div>
    </div>
  `;
	root.appendChild(el);
	setTimeout(() => el.remove(), 3800);
}

/* ---------- MODAL ---------- */
function modal({ title = "Confirmar", content = "", onOk = null, okText = "Confirmar", cancelText = "Cancelar" }) {
	const root = $("#modalRoot");
	root.style.display = "flex";
	root.innerHTML = `
    <div class="modal">
      <header>
        <div style="font-weight:700">${title}</div>
        <button class="btn ghost" id="mClose"><span class="material-symbols-rounded">close</span></button>
      </header>
      <div class="content">${content}</div>
      <footer>
        <button class="btn ghost" id="mCancel">${cancelText}</button>
        <button class="btn danger" id="mOk">${okText}</button>
      </footer>
    </div>
  `;
	const close = () => {
		root.style.display = "none";
		root.innerHTML = "";
	};
	$("#mClose").onclick = close;
	$("#mCancel").onclick = close;
	$("#mOk").onclick = async () => {
		try {
			await onOk?.();
		} finally {
			close();
		}
	};
}

/* ---------- FETCH WRAPPER ---------- */
function buildURL(path, query) {
	const isAbs = /^https?:\/\//i.test(path);
	const base = CONFIG.BASE_URL || window.location.origin; // same-origin si no hay base
	// Normaliza el path relativo: asegura que empiece con "/"
	const rel = path.replace(/^\/*/, "/");
	const url = isAbs ? new URL(path) : new URL(rel, base);
	if (query) {
		Object.entries(query).forEach(([k, v]) => {
			if (v !== undefined && v !== null) url.searchParams.set(k, v);
		});
	}
	return url;
}

async function api(path, { method = "GET", data, query } = {}) {
	const url = buildURL(path, query);
	const headers = { "Content-Type": "application/json" };

	// Auth de demo o bearer
	if ($("#authMode")?.checked) {
		headers["X-Demo-Superadmin"] = "1";
	} else {
		headers["Authorization"] = `Bearer ${$("#bearerToken")?.value || "let-me-in"}`;
	}

	const res = await fetch(url.toString(), {
		method,
		headers,
		body: data ? JSON.stringify(data) : undefined,
	});

	if (!res.ok) {
		let errText = await res.text().catch(() => "");
		try {
			const j = JSON.parse(errText);
			errText = j.message || errText;
		} catch {}
		throw new Error(`${res.status} ${res.statusText} • ${errText}`);
	}
	if (res.status === 204) return null;
	return res.json().catch(() => ({}));
}

/* ---------- MINI ROUTER ---------- */
const Router = {
	routes: {},
	register(path, fn) {
		this.routes[path] = fn;
	},
	async render() {
		const hash = location.hash.replace(/^#/, "") || "/";
		const route = this.routes[hash] || this.routes["/"];
		const el = $("#app");
		el.innerHTML = "";
		try {
			await route(el);
		} catch (e) {
			console.error(e);
			toast("Error", e.message, "error");
			el.innerHTML = `<div class="panel"><div class="panel-header"><div class="panel-title"><span class="material-symbols-rounded">error</span> Error</div></div><p>${e.message}</p></div>`;
		}
	},
};
window.addEventListener("hashchange", () => Router.render());

/* ---------- HOME (TILES) ---------- */
Router.register("/", async (el) => {
	el.innerHTML = `
    <div class="tile-grid">
      ${tile("Organizaciones", "groups", "Alta/baja/cambio y membresías", "#/organizations")}
      ${tile("Usuarios", "supervised_user_circle", "Busqueda y estados", "#/users")}
      ${tile("Invitaciones", "mail", "Emitir tokens de invitación", "#/invitations")}
      ${tile("API Keys", "vpn_key", "Gestión de llaves y permisos", "#/apikeys")}
      ${tile("Logs Auditoría", "fact_check", "Eventos y acciones del sistema", "#/audit")}
      ${tile("Servicios", "hub", "Servicios y health checks", "#/services")}
      ${tile("Catálogos", "view_list", "Tipos, roles y permisos", "#/catalogs")}
      ${tile("Métricas", "monitoring", "KPIs y actividad", "#/metrics")}
    </div>
  `;
	function tile(title, icon, desc, href) {
		return `
      <a class="tile" href="${href}">
        <span class="icon material-symbols-rounded">${icon}</span>
        <span class="title">${title}</span>
        <span class="desc">${desc}</span>
      </a>
    `;
	}
});

/* ---------- COMPONENTES AUX ---------- */
function panelScaffold(icon, title, actionsHtml = "", bodyHtml = "") {
	return `
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title"><span class="material-symbols-rounded">${icon}</span>${title}</div>
        <div class="panel-actions">${actionsHtml}</div>
      </div>
      ${bodyHtml}
    </div>
  `;
}
function tabs(names) {
	const id = "tab-" + Math.random().toString(36).slice(2, 8);
	const headers = names.map((n, i) => `<button class="tab ${i === 0 ? "active" : ""}" data-t="${id}" data-idx="${i}">${n}</button>`).join("");
	return { id, html: `<div class="tabs">${headers}</div><div class="tabpanes" id="${id}"></div>` };
}
function bindTabs(onChange) {
	$$(".tab").forEach((btn) => {
		btn.addEventListener("click", () => {
			const t = btn.dataset.t,
				idx = +btn.dataset.idx;
			$$(".tab").forEach((x) => x.dataset.t === t && x.classList.remove("active"));
			btn.classList.add("active");
			onChange(t, idx);
		});
	});
}

/* ---------- ORGANIZATIONS ---------- */
Router.register("/organizations", async (el) => {
	const t = tabs(["Listado", "Crear", "Actualizar", "Eliminar"]);
	el.innerHTML = panelScaffold("groups", "Organizaciones", `<button class="btn" id="backHome"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`, `${t.html}`);
	$("#backHome").onclick = () => (location.hash = "/");

	const panes = $("#" + t.id);

	async function list() {
		const data = await api("/v1/superadmin/organizations", { query: { limit: 50 } });
		panes.innerHTML = `
      <table class="table">
        <thead><tr><th>ID</th><th>Código</th><th>Nombre</th><th>Creado</th></tr></thead>
        <tbody>
          ${(data || [])
				.map(
					(o) => `
            <tr>
              <td>${o.id}</td>
              <td><span class="badge">${o.code}</span></td>
              <td>${o.name}</td>
              <td>${new Date(o.created_at || o.createdAt || Date.now()).toLocaleString()}</td>
            </tr>`
				)
				.join("")}
        </tbody>
      </table>
    `;
	}
	function create() {
		panes.innerHTML = `
      <form id="orgCreate" class="form-grid">
        <div class="form-field"><label>Código</label><input required id="code" type="text" placeholder="FAM-001" /></div>
        <div class="form-field"><label>Nombre</label><input required id="name" type="text" placeholder="Familia Demo" /></div>
        <div class="form-field full"><button class="btn"><span class="material-symbols-rounded">add</span> Crear</button></div>
      </form>`;
		$("#orgCreate").onsubmit = async (e) => {
			e.preventDefault();
			const payload = { code: $("#code").value.trim(), name: $("#name").value.trim() };
			try {
				await api("/v1/superadmin/organizations", { method: "POST", data: payload });
				toast("Organización", "Creada", "ok");
				await list();
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}
	function update() {
		panes.innerHTML = `
      <form id="orgUpdate" class="form-grid">
        <div class="form-field full"><label>Organization ID</label><input required id="oid" type="text" placeholder="uuid" /></div>
        <div class="form-field"><label>Nuevo código (opcional)</label><input id="ncode" type="text" /></div>
        <div class="form-field"><label>Nuevo nombre (opcional)</label><input id="nname" type="text" /></div>
        <div class="form-field full"><button class="btn"><span class="material-symbols-rounded">save</span> Actualizar</button></div>
      </form>`;
		$("#orgUpdate").onsubmit = async (e) => {
			e.preventDefault();
			const id = $("#oid").value.trim();
			const payload = {};
			if ($("#ncode").value.trim()) payload.code = $("#ncode").value.trim();
			if ($("#nname").value.trim()) payload.name = $("#nname").value.trim();
			try {
				await api(`/v1/superadmin/organizations/${id}`, { method: "PATCH", data: payload });
				toast("Organización", "Actualizada", "ok");
				await list();
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}
	function remove() {
		panes.innerHTML = `
      <form id="orgDelete" class="form-grid">
        <div class="form-field full"><label>Organization ID</label><input required id="oidDel" type="text" placeholder="uuid" /></div>
        <div class="form-field full"><button class="btn danger"><span class="material-symbols-rounded">delete</span> Eliminar</button></div>
      </form>`;
		$("#orgDelete").onsubmit = async (e) => {
			e.preventDefault();
			const id = $("#oidDel").value.trim();
			modal({
				title: "Eliminar organización",
				content: `<p>Se eliminará la organización <code>${id}</code>.</p>`,
				okText: "Eliminar",
				onOk: async () => {
					try {
						await api(`/v1/superadmin/organizations/${id}`, { method: "DELETE" });
						toast("Organización", "Eliminada", "ok");
						await list();
					} catch (err) {
						toast("Error", err.message, "error");
					}
				},
			});
		};
	}

	await list(); // default
	bindTabs((tid, idx) => [list, create, update, remove][idx]?.());
});

/* ---------- USERS (read + status) ---------- */
Router.register("/users", async (el) => {
	const t = tabs(["Buscar", "Cambiar estado"]);
	el.innerHTML = panelScaffold(
		"supervised_user_circle",
		"Usuarios",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`${t.html}`
	);
	const panes = $("#" + t.id);

	function search() {
		panes.innerHTML = `
      <form id="uSearch" class="form-grid">
        <div class="form-field"><label>Query</label><input id="q" type="text" placeholder="nombre o email"/></div>
        <div class="form-field"><label>Limit</label><input id="limit" type="number" value="20"/></div>
        <div class="form-field"><label>&nbsp;</label><button class="btn"><span class="material-symbols-rounded">search</span> Buscar</button></div>
      </form>
      <div id="uResults" style="margin-top:10px"></div>
    `;
		$("#uSearch").onsubmit = async (e) => {
			e.preventDefault();
			const q = $("#q").value.trim();
			const limit = +$("#limit").value || 20;
			try {
				const data = await api("/v1/superadmin/users", { query: { q, limit } });
				$("#uResults").innerHTML = `
          <table class="table">
            <thead><tr><th>ID</th><th>Nombre</th><th>Email</th><th>Status</th></tr></thead>
            <tbody>
              ${(data || [])
					.map(
						(u) => `
                <tr>
                  <td>${u.id}</td>
                  <td>${u.name || ""}</td>
                  <td>${u.email || ""}</td>
                  <td><span class="badge ${u.status === "active" ? "success" : u.status === "blocked" ? "danger" : "warn"}">${u.status}</span></td>
                </tr>`
					)
					.join("")}
            </tbody>
          </table>`;
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}

	function status() {
		panes.innerHTML = `
      <form id="uStatus" class="form-grid">
        <div class="form-field full"><label>User ID</label><input id="uid" type="text" required placeholder="uuid"/></div>
        <div class="form-field"><label>Nuevo estado</label>
          <select id="ustatus">
            <option value="active">active</option>
            <option value="blocked">blocked</option>
            <option value="pending">pending</option>
          </select>
        </div>
        <div class="form-field full"><button class="btn"><span class="material-symbols-rounded">save</span> Cambiar</button></div>
      </form>`;
		$("#uStatus").onsubmit = async (e) => {
			e.preventDefault();
			const id = $("#uid").value.trim();
			const status = $("#ustatus").value;
			try {
				await api(`/v1/superadmin/users/${id}/status`, { method: "PATCH", data: { status } });
				toast("Usuario", "Estado actualizado", "ok");
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}

	search();
	bindTabs((tid, idx) => [search, status][idx]?.());
});

/* ---------- API KEYS ---------- */
Router.register("/apikeys", async (el) => {
	const t = tabs(["Listado", "Crear", "Permisos", "Eliminar"]);
	el.innerHTML = panelScaffold("vpn_key", "API Keys", `<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`, `${t.html}`);
	const panes = $("#" + t.id);

	// Filtro: 'all' | 'active' | 'revoked'
	let filterMode = "all";

	function renderFilterBar() {
		const id = "f-" + Math.random().toString(36).slice(2, 8);
		return `
      <div class="toolbar" id="${id}">
        <span class="toolbar-label">Filtro:</span>
        <label class="chip"><input type="radio" name="kfilter" value="all" ${filterMode === "all" ? "checked" : ""}/> Todo</label>
        <label class="chip"><input type="radio" name="kfilter" value="active" ${filterMode === "active" ? "checked" : ""}/> Solo activas</label>
        <label class="chip"><input type="radio" name="kfilter" value="revoked" ${filterMode === "revoked" ? "checked" : ""}/> Solo revocadas</label>
      </div>
    `;
	}

	async function list() {
		let data;
		if (filterMode === "active") {
			data = await api("/v1/superadmin/api-keys", { query: { limit: 100, active_only: "true" } });
		} else {
			data = await api("/v1/superadmin/api-keys", { query: { limit: 100 } });
		}
		data = data || [];
		if (filterMode === "revoked") {
			data = data.filter((k) => k.revoked || !!k.revoked_at || !!k.revokedAt);
		}

		panes.innerHTML = `
      ${renderFilterBar()}
      <table class="table">
        <thead>
          <tr>
            <th>ID</th><th>Label</th><th>Owner</th><th>Estado</th><th>Expira</th><th>Creada</th>
          </tr>
        </thead>
        <tbody>
          ${data
				.map((k) => {
					const revoked = k.revoked || !!k.revoked_at || !!k.revokedAt;
					const state = revoked ? '<span class="badge danger">revocada</span>' : '<span class="badge success">activa</span>';
					return `
              <tr>
                <td>${k.id}</td>
                <td>${k.label || ""}</td>
                <td>${k.owner_user_id || ""}</td>
                <td>${state}</td>
                <td>${k.expires_at ? new Date(k.expires_at).toLocaleString() : "-"}</td>
                <td>${new Date(k.created_at || Date.now()).toLocaleString()}</td>
              </tr>
            `;
				})
				.join("")}
        </tbody>
      </table>
    `;

		// Bind de los radios
		panes.querySelectorAll('input[name="kfilter"]').forEach((r) => {
			r.addEventListener("change", async (e) => {
				filterMode = e.target.value;
				await list();
			});
		});
	}

	function create() {
		panes.innerHTML = `
      <form id="kCreate" class="form-grid">
        <div class="form-field"><label>Label</label><input id="klabel" type="text" required placeholder="demo"/></div>
        <div class="form-field"><label>Owner User (uuid, opcional)</label><input id="kowner" type="text"/></div>
        <div class="form-field"><label>Raw Key (min 32 chars)</label><input id="kraw" type="text" required placeholder="openssl rand -hex 32"/></div>
        <div class="form-field"><label>Expira (opcional)</label><input id="kexp" type="datetime-local"/></div>
        <div class="form-field full"><button class="btn"><span class="material-symbols-rounded">add</span> Crear</button></div>
      </form>`;
		$("#kCreate").onsubmit = async (e) => {
			e.preventDefault();
			const payload = {
				label: $("#klabel").value.trim(),
				raw_key: $("#kraw").value.trim(),
				owner_user_id: $("#kowner").value.trim() || null,
				expires_at: $("#kexp").value ? new Date($("#kexp").value).toISOString() : null,
			};
			try {
				await api("/v1/superadmin/api-keys", { method: "POST", data: payload });
				toast("API Key", "Creada", "ok");
				filterMode = "all";
				await list();
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}

	function perms() {
		panes.innerHTML = `
      <form id="kPerms" class="form-grid">
        <div class="form-field full"><label>API Key ID</label><input id="kid" type="text" required /></div>
        <div class="form-field full"><label>Permisos (comma-separated)</label><input id="kperms" type="text" placeholder="alerts.read,patients.read" /></div>
        <div class="form-field full"><button class="btn"><span class="material-symbols-rounded">playlist_add</span> Asignar</button></div>
      </form>`;
		$("#kPerms").onsubmit = async (e) => {
			e.preventDefault();
			const id = $("#kid").value.trim();
			const permissions = $("#kperms")
				.value.split(",")
				.map((s) => s.trim())
				.filter(Boolean);
			try {
				await api(`/v1/superadmin/api-keys/${id}/permissions`, { method: "POST", data: { permissions } });
				toast("API Key", "Permisos asignados", "ok");
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}

	function remove() {
		panes.innerHTML = `
      <form id="kDelete" class="form-grid">
        <div class="form-field full"><label>API Key ID</label><input id="kidDel" type="text" required /></div>
        <div class="form-field full"><button class="btn danger"><span class="material-symbols-rounded">delete</span> Revocar</button></div>
      </form>`;
		$("#kDelete").onsubmit = async (e) => {
			e.preventDefault();
			const id = $("#kidDel").value.trim();
			modal({
				title: "Revocar API Key",
				content: `<p>Se revocará la API key <code>${id}</code>.</p>`,
				okText: "Revocar",
				onOk: async () => {
					try {
						await api(`/v1/superadmin/api-keys/${id}`, { method: "DELETE" });
						toast("API Key", "Revocada", "ok");
						await list();
					} catch (err) {
						toast("Error", err.message, "error");
					}
				},
			});
		};
	}

	await list();
	bindTabs((tid, idx) => [list, create, perms, remove][idx]?.());
});

/* ---------- AUDIT LOGS ---------- */
Router.register("/audit", async (el) => {
	const t = tabs(["Listado", "Filtrar"]);
	el.innerHTML = panelScaffold(
		"fact_check",
		"Logs de Auditoría",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`${t.html}`
	);
	const panes = $("#" + t.id);

	async function list(params = {}) {
		const data = await api("/v1/superadmin/audit-logs", { query: { limit: 50, ...params } });
		panes.innerHTML = `
      <table class="table">
        <thead><tr><th>TS</th><th>Action</th><th>User</th><th>Entity</th><th>Entity ID</th><th>Details</th></tr></thead>
        <tbody>${(data || [])
			.map(
				(a) => `
          <tr>
            <td>${new Date(a.ts || a.timestamp || Date.now()).toLocaleString()}</td>
            <td><span class="badge">${a.action}</span></td>
            <td>${a.user_id || "-"}</td>
            <td>${a.entity || "-"}</td>
            <td>${a.entity_id || "-"}</td>
            <td><code style="font-size:12px">${escapeHtml(JSON.stringify(a.details || {}, null, 0)).slice(0, 120)}</code></td>
          </tr>`
			)
			.join("")}
        </tbody></table>`;
	}

	function filter() {
		panes.innerHTML = `
      <form id="aFilter" class="form-grid">
        <div class="form-field"><label>Desde</label><input id="from" type="datetime-local"/></div>
        <div class="form-field"><label>Hasta</label><input id="to" type="datetime-local"/></div>
        <div class="form-field"><label>Acción</label><input id="action" type="text" placeholder="ORG_CREATE"/></div>
        <div class="form-field"><label>Limit</label><input id="limit" type="number" value="50"/></div>
        <div class="form-field"><label>&nbsp;</label><button class="btn"><span class="material-symbols-rounded">filter_alt</span> Filtrar</button></div>
      </form>
      <div id="aRes" style="margin-top:10px"></div>
    `;
		$("#aFilter").onsubmit = async (e) => {
			e.preventDefault();
			const params = {};
			if ($("#from").value) params.from = new Date($("#from").value).toISOString();
			if ($("#to").value) params.to = new Date($("#to").value).toISOString();
			if ($("#action").value.trim()) params.action = $("#action").value.trim();
			params.limit = +$("#limit").value || 50;
			try {
				const data = await api("/v1/superadmin/audit-logs", { query: params });
				$("#aRes").textContent = JSON.stringify(data, null, 2);
			} catch (err) {
				toast("Error", err.message, "error");
			}
		};
	}

	await list();
	bindTabs((tid, idx) => [list, filter][idx]?.());
});

/* ---------- PLACEHOLDERS (para cuando integres endpoints) ---------- */
Router.register("/invitations", async (el) => {
	el.innerHTML = panelScaffold(
		"mail",
		"Invitaciones",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`<div class="tabs"><button class="tab active">Próximamente</button></div><div class="tabpanes"><p class="help">Integra aquí los endpoints de invitaciones.</p></div>`
	);
});
Router.register("/services", async (el) => {
	el.innerHTML = panelScaffold(
		"hub",
		"Servicios",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`<div class="tabs"><button class="tab active">Próximamente</button></div><div class="tabpanes"><p class="help">Integra health checks y métricas por servicio.</p></div>`
	);
});
Router.register("/catalogs", async (el) => {
	el.innerHTML = panelScaffold(
		"view_list",
		"Catálogos",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`<div class="tabs"><button class="tab active">Próximamente</button></div><div class="tabpanes"><p class="help">Muestra org_roles, permissions, event_types, etc.</p></div>`
	);
});
Router.register("/metrics", async (el) => {
	el.innerHTML = panelScaffold(
		"monitoring",
		"Métricas",
		`<button class="btn ghost" onclick="location.hash='/'"><span class="material-symbols-rounded">arrow_back</span>Inicio</button>`,
		`<div class="tabs"><button class="tab active">Próximamente</button></div><div class="tabpanes"><p class="help">Incluye KPIs, actividad reciente y conteos (consultas al backend).</p></div>`
	);
});

/* ---------- UTILS ---------- */
function escapeHtml(str) {
	return (str || "").replace(/[&<>"'`=\/]/g, (s) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;", "/": "&#x2F;", "`": "&#x60;", "=": "&#x3D;" }[s]));
}

/* ---------- INIT ---------- */
window.addEventListener("DOMContentLoaded", () => {
	// Persist base URL on click label
	const envBase = $("#envBase");
	envBase.title = "Click para cambiar base URL";
	envBase.style.cursor = "pointer";
	envBase.addEventListener("click", () => {
		const v = prompt("Base URL del backend (vacío = mismo origen):", CONFIG.BASE_URL || "");
		if (v === null) return; // cancel
		CONFIG.BASE_URL = v.trim().replace(/\/+$/, ""); // puede quedar ''
		localStorage.setItem("hg_base", CONFIG.BASE_URL);
		updateEnvLabel();
		toast("Backend", `Base: ${CONFIG.BASE_URL || "same-origin"}`, "ok");
	});

	Router.render();
});
