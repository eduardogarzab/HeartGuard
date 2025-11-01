import { sendXMLRequest } from "./xmlClient.js";
import { API_CONFIG } from "./config.js";

// ====================================================
// DASHBOARD - HEARTGUARD ADMIN PANEL (SPA MODULAR)
// ====================================================

// Validación inicial de sesión
window.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("jwt");
  const userId = localStorage.getItem("user_id");
  const userName = localStorage.getItem("user_name");
  const currentOrgName = localStorage.getItem("current_org_name");

  if (!token || !userId) {
    window.location.href = "index.html";
    return;
  }

  // Mostrar información del usuario y organización
  const orgLabel = currentOrgName ? `${userName} - ${currentOrgName}` : userName || "Cargando...";
  document.getElementById("orgLabel").textContent = orgLabel;
  
  await loadView("overview");
});

// ====================================================
// NAVEGACIÓN ENTRE VISTAS
// ====================================================
const contentContainer = document.getElementById("content-container");
const menuItems = document.querySelectorAll(".sidebar nav li");

async function loadView(viewName) {
  try {
    const res = await fetch(`views/${viewName}.html`);
    const html = await res.text();
    contentContainer.innerHTML = html;

    const token = localStorage.getItem("jwt");
    const orgCode = localStorage.getItem("current_org_code");
    
    if (!orgCode) {
      console.warn("No se encontró código de organización. El usuario puede no tener organizaciones asignadas.");
    }

    switch (viewName) {
      case "overview":
        await loadCounts(`<request><org_id>${orgCode || ""}</org_id></request>`, token);
        break;
      case "users":
        await loadUsers();
        break;
      case "patients":
        await loadPatients();
        break;
      case "devices":
        await loadDevices();
        break;
      case "inferences":
        await loadInferences();
        break;
      case "influx":
        await loadInfluxMetrics(); // sigue mostrando los valores en texto
        const module = await import("./influxChart.js");
        await module.initInfluxCharts();
        break;
    }
  } catch (err) {
    console.error("Error al cargar vista:", viewName, err);
    contentContainer.innerHTML = `<p>Error al cargar ${viewName}</p>`;
  }
}

menuItems.forEach((item) => {
  item.addEventListener("click", async () => {
    menuItems.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
    const viewName = item.id.replace("menu-", "");
    await loadView(viewName);
  });
});

// ====================================================
// FUNCIONES DE CARGA DE DATOS
// ====================================================

// --- Resumen General ---
async function loadCounts(xmlReq, token) {
  const endpoints = [
    { id: "usersCount", url: API_CONFIG.ENDPOINTS.USERS.COUNT, label: "usuarios" },
    { id: "patientsCount", url: API_CONFIG.ENDPOINTS.PATIENTS.COUNT, label: "pacientes" },
    { id: "devicesCount", url: API_CONFIG.ENDPOINTS.DEVICES.COUNT, label: "dispositivos" },
    { id: "inferencesCount", url: API_CONFIG.ENDPOINTS.INFERENCES.COUNT, label: "inferencias" }
  ];

  // Cargar todas las cuentas en paralelo para mejor rendimiento
  const promises = endpoints.map(async (e) => {
    try {
      const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}${e.url}`, "POST", xmlReq, token);
      const xml = new DOMParser().parseFromString(res, "application/xml");
      const count = xml.querySelector("count")?.textContent || "-";
      return { id: e.id, count };
    } catch (err) {
      console.error(`Error al cargar ${e.label}:`, err);
      return { id: e.id, count: "Error" };
    }
  });

  // Esperar a que todas las peticiones se completen
  const results = await Promise.all(promises);
  
  // Actualizar el DOM con los resultados
  results.forEach(result => {
    const element = document.getElementById(result.id);
    if (element) {
      element.textContent = result.count;
    }
  });
}

// --- USERS ---
async function loadUsers() {
  const token = localStorage.getItem("jwt");
  const orgCode = localStorage.getItem("current_org_code");
  
  if (!orgCode) {
    const tbody = document.querySelector("#usersTable tbody");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:orange;">No se encontró organización asignada al usuario</td></tr>`;
    return;
  }
  
  try {
    // Usar query parameter para filtrar por organización
    const res = await sendXMLRequest(
      `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.USERS.LIST}?org_code=${orgCode}`, 
      "GET", 
      null, 
      token
    );
    
    console.log("Users Response:", res);
    
    const xml = new DOMParser().parseFromString(res, "application/xml");
    const tbody = document.querySelector("#usersTable tbody");
    tbody.innerHTML = "";
    
    // Verificar si hay error en la respuesta
    const errorNode = xml.querySelector("error message");
    if (errorNode) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:red;">Error: ${errorNode.textContent}</td></tr>`;
      return;
    }
    
    // Buscar usuarios en la respuesta XML
    const dataNode = xml.querySelector("data");
    if (!dataNode) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No se encontraron usuarios</td></tr>`;
      return;
    }
    
    const users = dataNode.querySelectorAll("users item") || dataNode.querySelectorAll("user");
    
    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No hay usuarios en esta organización</td></tr>`;
      return;
    }
    
    // Usar un array y un solo innerHTML para mejor rendimiento
    const rows = [];
    
    users.forEach((user) => {
      const name = user.querySelector("name")?.textContent || "-";
      const email = user.querySelector("email")?.textContent || "-";
      const status = user.querySelector("status")?.textContent || "-";
      const createdAt = user.querySelector("created_at")?.textContent || "-";
      
      // Obtener roles de la organización
      const orgRoles = [];
      const orgs = user.querySelectorAll("organizations item") || user.querySelectorAll("organization");
      orgs.forEach(org => {
        const orgRole = org.querySelector("role")?.textContent;
        if (orgRole) orgRoles.push(orgRole);
      });
      
      // Si no hay roles de org, buscar roles globales
      const globalRoles = [];
      const roles = user.querySelectorAll("roles item") || user.querySelectorAll("role");
      roles.forEach(role => {
        const roleName = role.textContent;
        if (roleName) globalRoles.push(roleName);
      });
      
      const roleDisplay = orgRoles.length > 0 ? orgRoles.join(", ") : globalRoles.join(", ") || "-";
      
      // Formatear fecha solo si es válida
      let formattedDate = "-";
      if (createdAt && createdAt !== "-") {
        try {
          formattedDate = new Date(createdAt).toLocaleDateString('es-MX');
        } catch (e) {
          formattedDate = createdAt;
        }
      }
      
      rows.push(`
        <tr>
          <td>${name}</td>
          <td>${email}</td>
          <td>${roleDisplay}</td>
          <td>${status}</td>
          <td>${formattedDate}</td>
        </tr>`);
    });
    
    // Una sola asignación de innerHTML en lugar de concatenaciones múltiples
    tbody.innerHTML = rows.join('');
    
  } catch (err) {
    console.error("Error al cargar usuarios:", err);
    const tbody = document.querySelector("#usersTable tbody");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:red;">Error al cargar usuarios: ${err.message}</td></tr>`;
  }
}

// --- PATIENTS ---
async function loadPatients() {
  const token = localStorage.getItem("jwt");
  const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PATIENTS.LIST}`, "GET", "", token);
  const xml = new DOMParser().parseFromString(res, "application/xml");
  const tbody = document.querySelector("#patientsTable tbody");
  
  const patients = xml.querySelectorAll("patient");
  if (patients.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No hay pacientes</td></tr>';
    return;
  }
  
  const rows = [];
  patients.forEach((p) => {
    rows.push(`
      <tr>
        <td>${p.querySelector("first_name")?.textContent || ""} ${p.querySelector("last_name")?.textContent || ""}</td>
        <td>${p.querySelector("sex")?.textContent || "-"}</td>
        <td>${p.querySelector("risk_level")?.textContent || "-"}</td>
        <td>${p.querySelector("created_at")?.textContent || "-"}</td>
      </tr>`);
  });
  tbody.innerHTML = rows.join('');
}

// --- DEVICES ---
async function loadDevices() {
  const token = localStorage.getItem("jwt");
  const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DEVICES.LIST}`, "GET", "", token);
  const xml = new DOMParser().parseFromString(res, "application/xml");
  const tbody = document.querySelector("#devicesTable tbody");
  
  const devices = xml.querySelectorAll("device");
  if (devices.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No hay dispositivos</td></tr>';
    return;
  }
  
  const rows = [];
  devices.forEach((d) => {
    rows.push(`
      <tr>
        <td>${d.querySelector("serial_number")?.textContent || "-"}</td>
        <td>${d.querySelector("device_type label")?.textContent || "-"}</td>
        <td>${d.querySelector("status")?.textContent || "-"}</td>
        <td>${d.querySelector("last_seen_at")?.textContent || "-"}</td>
      </tr>`);
  });
  tbody.innerHTML = rows.join('');
}

// --- INFERENCES ---
async function loadInferences() {
  const token = localStorage.getItem("jwt");
  const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.INFERENCES.LIST}`, "GET", "", token);
  const xml = new DOMParser().parseFromString(res, "application/xml");
  const tbody = document.querySelector("#inferencesTable tbody");
  
  const inferences = xml.querySelectorAll("inference");
  if (inferences.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No hay inferencias</td></tr>';
    return;
  }
  
  const rows = [];
  inferences.forEach((i) => {
    rows.push(`
      <tr>
        <td>${i.querySelector("id")?.textContent || "-"}</td>
        <td>${i.querySelector("model_id")?.textContent || "-"}</td>
        <td>${i.querySelector("event_type")?.textContent || "-"}</td>
        <td>${i.querySelector("score")?.textContent || "-"}</td>
        <td>${i.querySelector("created_at")?.textContent || "-"}</td>
      </tr>`);
  });
  tbody.innerHTML = rows.join('');
}

// --- INFLUX METRICS ---
async function loadInfluxMetrics() {
  const token = localStorage.getItem("jwt");
  const res = await sendXMLRequest(`${API_CONFIG.BASE_URL}/influx/metrics`, "GET", "", token);
  const xml = new DOMParser().parseFromString(res, "application/xml");
  const container = document.getElementById("influxMetrics");
  
  const metrics = xml.querySelectorAll("metric");
  if (metrics.length === 0) {
    container.innerHTML = '<div style="text-align:center;">No hay métricas disponibles</div>';
    return;
  }
  
  const items = [];
  metrics.forEach((m) => {
    items.push(`<div><strong>${m.querySelector("name")?.textContent}:</strong> ${m.querySelector("value")?.textContent}</div>`);
  });
  container.innerHTML = items.join('');
}

// ====================================================
// LOGOUT
// ====================================================
document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.clear();
  window.location.href = "index.html";
});
