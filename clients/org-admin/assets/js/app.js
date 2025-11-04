(() => {
    const storageKeys = {
        token: "org_admin_access_token",
        user: "org_admin_user_info",
        selectedOrg: "org_admin_selected_org",
    };

    const state = {
        token: null,
        user: null,
        organizations: [],
        selectedOrgId: null,
        orgSummary: null,
        orgDashboard: null,
        tabCache: new Map(),
        charts: {},
        relationshipTypesCache: [],
        careTeamRoles: [],
        activeCareTeamDetail: null,
        availableStaff: [],
        availablePatients: [],
    };

    const el = {
        loginView: document.querySelector("#loginView"),
        dashboardView: document.querySelector("#dashboardView"),
        loginForm: document.querySelector("#loginForm"),
        loginError: document.querySelector("#loginError"),
        logoutButton: document.querySelector("#logoutButton"),
        sessionInfo: document.querySelector("#sessionInfo"),
        sessionUserName: document.querySelector("#sessionUserName"),
        sessionOrgContext: document.querySelector("#sessionOrgContext"),
        welcomeName: document.querySelector("#welcomeName"),
        welcomeEmail: document.querySelector("#welcomeEmail"),
        orgStatus: document.querySelector("#orgStatus"),
        orgGrid: document.querySelector("#orgGrid"),
        orgEmptyState: document.querySelector("#orgEmptyState"),
        orgListSection: document.querySelector("#orgListSection"),
        refreshOrgs: document.querySelector("#refreshOrgs"),
        orgDetailSection: document.querySelector("#orgDetailSection"),
        backToOrgs: document.querySelector("#backToOrgs"),
        orgBreadcrumbName: document.querySelector("#orgBreadcrumbName"),
        orgTitle: document.querySelector("#orgTitle"),
        orgMeta: document.querySelector("#orgMeta"),
        orgMetrics: document.querySelector("#orgMetrics"),
        tabBar: document.querySelector(".tab-bar"),
        overviewCards: document.querySelector("#overviewCards"),
        overviewCharts: document.querySelector("#overviewCharts"),
        tabPanels: {
            overview: document.querySelector("#tab-overview"),
            staff: document.querySelector("#tab-staff"),
            patients: document.querySelector("#tab-patients"),
            "care-teams": document.querySelector("#tab-care-teams"),
            caregivers: document.querySelector("#tab-caregivers"),
            alerts: document.querySelector("#tab-alerts"),
            devices: document.querySelector("#tab-devices"),
            "push-devices": document.querySelector("#tab-push-devices"),
        },
        tabBodies: {
            staff: document.querySelector("#staffTable"),
            patients: document.querySelector("#patientsTable"),
            "care-teams": document.querySelector("#careTeamsTable"),
            caregivers: document.querySelector("#caregiversTable"),
            alerts: document.querySelector("#alertsTable"),
            devices: document.querySelector("#devicesTable"),
            "push-devices": document.querySelector("#pushDevicesTable"),
        },
        tabs: Array.from(document.querySelectorAll(".tab-bar .tab")),
        buttons: {
            inviteStaff: document.querySelector("#btnInviteStaff"),
            createPatient: document.querySelector("#btnCreatePatient"),
            createCareTeam: document.querySelector("#btnCreateCareTeam"),
            assignCaregiver: document.querySelector("#btnAssignCaregiver"),
            createAlert: document.querySelector("#btnCreateAlert"),
            refreshAlerts: document.querySelector("#btnRefreshAlerts"),
            createDevice: document.querySelector("#btnCreateDevice"),
            refreshPushDevices: document.querySelector("#btnRefreshPushDevices"),
        },
        modal: {
            overlay: document.querySelector("#modalOverlay"),
            title: document.querySelector("#modalTitle"),
            body: document.querySelector("#modalBody"),
            footer: document.querySelector("#modalFooter"),
            close: document.querySelector("#modalClose"),
        },
        toast: document.querySelector("#globalToast"),
    };

    const escapeHtml = (value) => {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    const formatDateTime = (value) => {
        if (!value) return "-";
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return value;
            }
            return date.toLocaleString("es-MX", {
                year: "numeric",
                month: "short",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch (err) {
            return value;
        }
    };

    const formatDate = (value) => {
        if (!value) return "-";
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return value;
            }
            return date.toLocaleDateString("es-MX", {
                year: "numeric",
                month: "short",
                day: "2-digit",
            });
        } catch (err) {
            return value;
        }
    };

    const formatSeconds = (value) => {
        if (value === null || value === undefined || value === "") {
            return "-";
        }
        const numeric = Number(value);
        if (Number.isNaN(numeric)) {
            return value;
        }
        if (numeric >= 3600) {
            const hours = numeric / 3600;
            return `${hours.toFixed(1)} h`;
        }
        if (numeric >= 60) {
            const minutes = numeric / 60;
            return `${minutes.toFixed(1)} min`;
        }
        return `${numeric.toFixed(0)} s`;
    };

    const showView = (viewName) => {
        if (viewName === "login") {
            el.loginView?.classList.remove("hidden");
            el.dashboardView?.classList.add("hidden");
        } else if (viewName === "dashboard") {
            el.loginView?.classList.add("hidden");
            el.dashboardView?.classList.remove("hidden");
        }
    };

    const showToast = (message, type = "info") => {
        if (!el.toast) return;
        el.toast.textContent = message;
        el.toast.setAttribute("data-type", type);
        el.toast.classList.remove("hidden");
        setTimeout(() => {
            el.toast.classList.add("hidden");
        }, 5000);
    };

    const persistState = () => {
        if (state.token) {
            sessionStorage.setItem(storageKeys.token, state.token);
        } else {
            sessionStorage.removeItem(storageKeys.token);
        }
        if (state.user) {
            sessionStorage.setItem(storageKeys.user, JSON.stringify(state.user));
        } else {
            sessionStorage.removeItem(storageKeys.user);
        }
        if (state.selectedOrgId) {
            sessionStorage.setItem(storageKeys.selectedOrg, state.selectedOrgId);
        } else {
            sessionStorage.removeItem(storageKeys.selectedOrg);
        }
    };

    const restoreState = () => {
        const token = sessionStorage.getItem(storageKeys.token);
        const userJson = sessionStorage.getItem(storageKeys.user);
        const orgId = sessionStorage.getItem(storageKeys.selectedOrg);
        if (token) {
            state.token = token;
        }
        if (userJson) {
            try {
                state.user = JSON.parse(userJson);
            } catch (err) {
                console.warn("No se pudo restaurar usuario", err);
            }
        }
        if (orgId) {
            state.selectedOrgId = orgId;
        }
    };

    const destroyCharts = () => {
        if (!state.charts) {
            state.charts = {};
            return;
        }
        Object.values(state.charts).forEach((chart) => {
            if (chart && typeof chart.destroy === "function") {
                chart.destroy();
            }
        });
        state.charts = {};
    };

    const renderOverview = () => {
        if (!el.overviewCards || !el.overviewCharts) return;
        if (!state.orgSummary || !state.orgDashboard) {
            if (el.overviewCards) {
                setLoadingContainer(el.overviewCards, "Cargando resumen...");
            }
            if (el.overviewCharts) {
                el.overviewCharts.innerHTML = "";
            }
            destroyCharts();
            return;
        }

        const { organization, stats = {} } = state.orgSummary;
        const dashboard = state.orgDashboard || {};
        const responseStats = dashboard.responseStats || {};
        const riskLevels = dashboard.riskLevels || [];
        const deviceStatus = dashboard.deviceStatus || [];
        const alertOutcomes = dashboard.alertOutcomes || [];
        const periodDays = dashboard.periodDays ?? "-";

        el.overviewCards.innerHTML = `
            <article class="chart-card kpi-card kpi-primary">
                <div class="kpi-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="kpi-content">
                    <div class="kpi-value">${escapeHtml(dashboard.alertsCreated ?? 0)}</div>
                    <div class="kpi-label">Alertas generadas</div>
                    <div class="kpi-period">últimos ${escapeHtml(periodDays)} días</div>
                </div>
            </article>
            <article class="chart-card kpi-card kpi-success">
                <div class="kpi-icon"><i class="fas fa-stopwatch"></i></div>
                <div class="kpi-content">
                    <div class="kpi-value">${escapeHtml(formatSeconds(responseStats.avgAckSeconds))}</div>
                    <div class="kpi-label">Tiempo promedio de acuse</div>
                    <div class="kpi-period">últimos ${escapeHtml(periodDays)} días</div>
                </div>
            </article>
            <article class="chart-card kpi-card kpi-info">
                <div class="kpi-icon"><i class="fas fa-check-circle"></i></div>
                <div class="kpi-content">
                    <div class="kpi-value">${escapeHtml(formatSeconds(responseStats.avgResolveSeconds))}</div>
                    <div class="kpi-label">Tiempo promedio de resolución</div>
                    <div class="kpi-period">últimos ${escapeHtml(periodDays)} días</div>
                </div>
            </article>
        `;

        destroyCharts();
        el.overviewCharts.innerHTML = "";

        const buildDoughnutData = (items) => ({
            labels: items.map((item, index) => item.label || item.code || `Item ${index + 1}`),
            values: items.map((item) => item.count ?? 0),
        });

        const appendChart = (id, title, type, dataset, palette, opts = {}) => {
            const card = document.createElement("article");
            card.className = "chart-card";
            card.innerHTML = `<h4 class="section-title">${escapeHtml(title)}</h4>`;
            const noData = !dataset.values.length || dataset.values.every((value) => Number(value) === 0);
            if (noData) {
                card.insertAdjacentHTML("beforeend", '<p class="muted">Sin datos disponibles</p>');
                el.overviewCharts.appendChild(card);
                return;
            }
            const canvas = document.createElement("canvas");
            canvas.id = id;
            card.appendChild(canvas);
            el.overviewCharts.appendChild(card);
            
            if (typeof Chart === 'undefined' && typeof window.Chart === 'undefined') {
                console.error('Chart.js no está disponible');
                canvas.insertAdjacentHTML("afterend", '<p class="muted">Cargando graficas...</p>');
                return;
            }
            
            const ChartConstructor = window.Chart || Chart;
            const chart = new ChartConstructor(canvas, {
                type,
                data: {
                    labels: dataset.labels,
                    datasets: [
                        {
                            data: dataset.values,
                            backgroundColor: palette,
                            borderWidth: 0,
                        },
                    ],
                },
                options: Object.assign(
                    {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: "bottom",
                            },
                        },
                        scales: type === "bar"
                            ? {
                                  x: {
                                      ticks: { color: "#4b5563" },
                                  },
                                  y: {
                                      ticks: { color: "#4b5563" },
                                      beginAtZero: true,
                                  },
                              }
                            : {},
                    },
                    opts
                ),
            });
            state.charts[id] = chart;
        };

        const palettePrimary = ["#2563eb", "#4f46e5", "#0ea5e9", "#0891b2", "#10b981"];
        const paletteSecondary = ["#f97316", "#facc15", "#22c55e", "#14b8a6", "#6366f1"];

        if (riskLevels.length) {
            const data = buildDoughnutData(riskLevels);
            appendChart("chartRiskLevels", "Distribucion de riesgo", "doughnut", data, palettePrimary);
        } else {
            el.overviewCharts.insertAdjacentHTML(
                "beforeend",
                '<article class="chart-card"><h4 class="section-title">Distribucion de riesgo</h4><p class="muted">Sin datos recientes</p></article>'
            );
        }

        if (deviceStatus.length) {
            const data = buildDoughnutData(deviceStatus);
            appendChart("chartDeviceStatus", "Estado de dispositivos", "doughnut", data, paletteSecondary);
        } else {
            el.overviewCharts.insertAdjacentHTML(
                "beforeend",
                '<article class="chart-card"><h4 class="section-title">Estado de dispositivos</h4><p class="muted">No hay dispositivos registrados</p></article>'
            );
        }

        if (alertOutcomes.length) {
            const data = buildDoughnutData(alertOutcomes);
            appendChart("chartAlertOutcomes", "Resultados de alertas", "bar", data, palettePrimary, {
                plugins: {
                    legend: { display: false },
                },
            });
        } else {
            el.overviewCharts.insertAdjacentHTML(
                "beforeend",
                '<article class="chart-card"><h4 class="section-title">Resultados de alertas</h4><p class="muted">Sin resoluciones registradas</p></article>'
            );
        }
    };

    const resetOrgView = () => {
        destroyCharts();
        state.orgSummary = null;
        state.orgDashboard = null;
        state.tabCache.clear();
        state.selectedOrgId = null;
        if (el.overviewCards) {
            el.overviewCards.innerHTML = "";
        }
        if (el.overviewCharts) {
            el.overviewCharts.innerHTML = "";
        }
        el.orgDetailSection.classList.add("hidden");
        el.sessionOrgContext.textContent = "";
        el.sessionOrgContext.classList.add("hidden");
        persistState();
    };

    const handleApiError = (error) => {
        console.error("API error", error);
        const message = error?.message || "Ocurrió un error inesperado";
        if (error?.status === 401 || error?.status === 403) {
            showToast("Sesión expirada o sin permisos", "danger");
            logout();
            return;
        }
        showToast(message, "danger");
    };

    const setLoadingContainer = (container, message = "Cargando...") => {
        container.innerHTML = `<div class="loader"><span class="spinner"></span>${escapeHtml(message)}</div>`;
    };

    const renderOrganizations = () => {
        if (!el.orgGrid) return;
        if (!state.organizations.length) {
            el.orgGrid.innerHTML = "";
            el.orgEmptyState.classList.remove("hidden");
            el.orgDetailSection.classList.add("hidden");
            el.orgStatus.classList.add("hidden");
            return;
        }
        el.orgEmptyState.classList.add("hidden");
        el.orgGrid.innerHTML = state.organizations
            .map((org) => {
                return `
                <article class="org-card" data-org-id="${escapeHtml(org.id)}">
                    <h4>${escapeHtml(org.name)}</h4>
                    <span class="badge">${escapeHtml(org.code)}</span>
                    <p>Rol asignado: <strong>${escapeHtml(org.roleLabel || org.roleCode)}</strong></p>
                    <p>Miembro desde: ${escapeHtml(formatDate(org.joinedAt))}</p>
                </article>`;
            })
            .join("");
        el.orgStatus.classList.remove("hidden");
        el.orgStatus.textContent = `${state.organizations.length} organización${state.organizations.length === 1 ? "" : "es"}`;
    };

    const renderMetricCards = (stats) => {
        if (!el.orgMetrics) return;
        if (!stats) {
            el.orgMetrics.innerHTML = "";
            return;
        }
        const entries = [
            { label: "Staff", value: stats.memberCount },
            { label: "Pacientes", value: stats.patientCount },
            { label: "Equipos", value: stats.careTeamCount },
            { label: "Cuidadores", value: stats.caregiverCount },
            { label: "Alertas", value: stats.alertCount },
        ];
        el.orgMetrics.innerHTML = entries
            .map(
                (item) => `
            <div class="metric-card">
                <span class="metric-label">${escapeHtml(item.label)}</span>
                <span class="metric-value">${escapeHtml(item.value ?? 0)}</span>
            </div>`
            )
            .join("");
    };

    const renderTable = (container, columns, rows, renderRow, emptyText) => {
        if (!container) return;
        if (!rows.length) {
            container.innerHTML = `<p class="muted">${escapeHtml(emptyText)}</p>`;
            return;
        }
        const thead = `<thead><tr>${columns.map((col) => `<th>${escapeHtml(col)}</th>`).join("")}</tr></thead>`;
        const tbody = `<tbody>${rows.map(renderRow).join("")}</tbody>`;
        container.innerHTML = `<div class="table-wrapper"><table>${thead}${tbody}</table></div>`;
    };

    const renderStaff = (data) => {
        const container = el.tabBodies.staff || el.tabPanels.staff;
        
        // Split into two sections: staff members and invitations
        const staffHtml = `
            <div class="staff-section">
                <h4 class="section-subtitle">Miembros del Staff</h4>
                ${!data.members || !data.members.length ? '<p class="muted">No se encontraron miembros del staff</p>' : `
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Correo</th>
                                    <th>Rol</th>
                                    <th>Miembro desde</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.members.map(member => `
                                    <tr>
                                        <td>${escapeHtml(member.name)}</td>
                                        <td>${escapeHtml(member.email)}</td>
                                        <td>${escapeHtml(member.roleLabel || member.roleCode)}</td>
                                        <td>${escapeHtml(formatDate(member.joinedAt))}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `}
            </div>
            <div class="staff-section">
                <h4 class="section-subtitle">Invitaciones</h4>
                ${!data.invitations || !data.invitations.length ? '<p class="muted">No hay invitaciones</p>' : `
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Rol</th>
                                    <th>Token</th>
                                    <th>Expira</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.invitations.map(inv => {
                                    const statusClass = inv.status === 'pending' ? 'status-warning' : 
                                                       inv.status === 'used' ? 'status-success' : 
                                                       inv.status === 'expired' ? 'status-muted' : 
                                                       inv.status === 'revoked' ? 'status-danger' : '';
                                    const statusLabel = inv.status === 'pending' ? 'Pendiente' : 
                                                       inv.status === 'used' ? 'Usada' : 
                                                       inv.status === 'expired' ? 'Expirada' : 
                                                       inv.status === 'revoked' ? 'Revocada' : inv.status;
                                    return `
                                    <tr>
                                        <td>${escapeHtml(inv.email)}</td>
                                        <td>${escapeHtml(inv.roleLabel || inv.roleCode)}</td>
                                        <td><code class="token-display">${escapeHtml(inv.token?.substring(0, 16))}...</code></td>
                                        <td>${escapeHtml(formatDateTime(inv.expiresAt))}</td>
                                        <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                                        <td>
                                            ${inv.status === 'pending' ? 
                                                `<button class="btn btn-sm btn-danger" onclick="window.app.revokeInvitation('${escapeHtml(inv.id)}')">Revocar</button>` : 
                                                '<span class="muted">—</span>'
                                            }
                                        </td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    </div>
                `}
            </div>
        `;
        
        container.innerHTML = staffHtml;
    };

    const renderPatients = (patients) => {
        const container = el.tabBodies.patients || el.tabPanels.patients;
        renderTable(
            container,
            ["Nombre", "Correo", "Fecha de nacimiento", "Riesgo", "Fecha de ingreso", "Acciones"],
            patients,
            (patient) => `
                <tr>
                    <td>${escapeHtml(patient.name)}</td>
                    <td>${escapeHtml(patient.email)}</td>
                    <td>${escapeHtml(formatDate(patient.birthdate))}</td>
                    <td><span class="status-badge">${escapeHtml(patient.riskLevelLabel || patient.riskLevelCode || "-")}</span></td>
                    <td>${escapeHtml(formatDate(patient.createdAt))}</td>
                    <td>
                        <button class="btn btn-sm" onclick="window.app.editPatient('${escapeHtml(patient.id)}')">Editar</button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deletePatient('${escapeHtml(patient.id)}')">Eliminar</button>
                    </td>
                </tr>` ,
            "No se encontraron pacientes"
        );
    };

    const renderCareTeams = (careTeams) => {
        const container = el.tabBodies["care-teams"] || el.tabPanels["care-teams"];
        renderTable(
            container,
            ["Equipo", "Creado el", "ID", "Acciones"],
            careTeams,
            (team) => `
                <tr>
                    <td>${escapeHtml(team.name)}</td>
                    <td>${escapeHtml(formatDate(team.createdAt))}</td>
                    <td><code>${escapeHtml(team.id)}</code></td>
                    <td>
                        <button class="btn btn-sm" onclick="window.app.openCareTeamDetail('${escapeHtml(team.id)}')">Ver detalles</button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deleteCareTeam('${escapeHtml(team.id)}', '${escapeHtml(team.name)}')">Eliminar</button>
                    </td>
                </tr>` ,
            "No se encontraron equipos de cuidado"
        );
    };

    const renderCaregivers = (assignments) => {
        const container = el.tabBodies.caregivers || el.tabPanels.caregivers;
        renderTable(
            container,
            ["Paciente", "Cuidador", "Relación", "Principal", "Inicio", "Nota"],
            assignments,
            (assignment) => `
                <tr>
                    <td>${escapeHtml(assignment.patientName)}</td>
                    <td>${escapeHtml(assignment.caregiverName)}<br><span class="muted">${escapeHtml(assignment.caregiverEmail)}</span></td>
                    <td>${escapeHtml(assignment.relationshipLabel || assignment.relationshipCode)}</td>
                    <td>${assignment.isPrimary ? "Sí" : "No"}</td>
                    <td>${escapeHtml(formatDateTime(assignment.startedAt))}</td>
                    <td>${escapeHtml(assignment.note)}</td>
                </tr>` ,
            "No hay cuidadores asignados"
        );
    };

    const renderAlerts = (alerts) => {
        const container = el.tabBodies.alerts || el.tabPanels.alerts;
        renderTable(
            container,
            ["Fecha", "Paciente", "Descripción", "Nivel", "Estado", "Acciones"],
            alerts,
            (alert) => `
                <tr>
                    <td>${escapeHtml(formatDateTime(alert.createdAt))}</td>
                    <td>${escapeHtml(alert.patientName)}</td>
                    <td>${escapeHtml(alert.description)}</td>
                    <td><span class="status-badge ${alert.levelCode === "critical" ? "danger" : alert.levelCode === "high" ? "warning" : ""}">${escapeHtml(alert.levelLabel || alert.levelCode)}</span></td>
                    <td>${escapeHtml(alert.statusDescription || alert.statusCode)}</td>
                    <td>
                        <button class="btn btn-sm" onclick="window.app.editAlert('${escapeHtml(alert.id)}')">Editar</button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deleteAlert('${escapeHtml(alert.id)}')">Eliminar</button>
                    </td>
                </tr>` ,
            "No se han generado alertas"
        );
    };

    const renderDevices = (devices) => {
        const container = el.tabBodies.devices || el.tabPanels.devices;
        renderTable(
            container,
            ["Serial", "Tipo", "Paciente", "Estado", "Firmware", "Última conexión", "Acciones"],
            devices,
            (device) => `
                <tr>
                    <td><code>${escapeHtml(device.serialNumber)}</code></td>
                    <td>${escapeHtml(device.deviceTypeLabel || device.deviceTypeCode)}</td>
                    <td>${escapeHtml(device.patientName || "-")}</td>
                    <td><span class="status-badge ${device.statusCode === "ACTIVE" ? "success" : ""}">${escapeHtml(device.statusLabel || device.statusCode)}</span></td>
                    <td>${escapeHtml(device.firmwareVersion || "-")}</td>
                    <td>${escapeHtml(formatDateTime(device.lastSeen))}</td>
                    <td>
                        <button class="btn btn-sm" onclick="window.app.editDevice('${escapeHtml(device.id)}')">Editar</button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deleteDevice('${escapeHtml(device.id)}')">Eliminar</button>
                    </td>
                </tr>` ,
            "No se encontraron dispositivos"
        );
    };

    const renderPushDevices = (pushDevices) => {
        const container = el.tabBodies["push-devices"] || el.tabPanels["push-devices"];
        renderTable(
            container,
            ["Usuario", "Plataforma", "Token", "Estado", "Última uso", "Acciones"],
            pushDevices,
            (pd) => `
                <tr>
                    <td>${escapeHtml(pd.userName)}</td>
                    <td><span class="status-badge">${escapeHtml(pd.platform)}</span></td>
                    <td><code>${escapeHtml(pd.deviceToken?.substring(0, 20))}...</code></td>
                    <td><span class="status-badge ${pd.isActive ? "success" : ""}">${pd.isActive ? "Activo" : "Inactivo"}</span></td>
                    <td>${escapeHtml(formatDateTime(pd.lastUsed))}</td>
                    <td>
                        <button class="btn btn-sm" onclick="window.app.togglePushDevice('${escapeHtml(pd.id)}', ${!pd.isActive})">${pd.isActive ? "Desactivar" : "Activar"}</button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deletePushDevice('${escapeHtml(pd.id)}')">Eliminar</button>
                    </td>
                </tr>` ,
            "No se encontraron push devices"
        );
    };

    const tabRenderers = {
        staff: renderStaff,
        patients: renderPatients,
        "care-teams": renderCareTeams,
        caregivers: renderCaregivers,
        alerts: renderAlerts,
        devices: renderDevices,
        "push-devices": renderPushDevices,
    };

    const activateTab = async (tabName) => {
        el.tabs.forEach((tab) => {
            tab.classList.toggle("active", tab.dataset.tab === tabName);
        });
        Object.entries(el.tabPanels).forEach(([key, panel]) => {
            panel.classList.toggle("active", key === tabName);
        });

        if (tabName === "overview") {
            renderOverview();
            return;
        }

        if (state.tabCache.has(tabName)) {
            tabRenderers[tabName]?.(state.tabCache.get(tabName));
            return;
        }

        const panel = el.tabPanels[tabName];
        const body = el.tabBodies[tabName] || panel;
        setLoadingContainer(body, "Cargando datos...");
        try {
            let data;
            switch (tabName) {
                case "staff":
                    // Fetch both staff members and invitations
                    const [members, invitations] = await Promise.all([
                        Api.admin.listStaff(state.token, state.selectedOrgId),
                        Api.admin.listInvitations(state.token, state.selectedOrgId)
                    ]);
                    data = { members, invitations };
                    break;
                case "patients":
                    data = await Api.admin.listPatients(state.token, state.selectedOrgId);
                    break;
                case "care-teams":
                    data = await Api.admin.listCareTeams(state.token, state.selectedOrgId);
                    break;
                case "caregivers":
                    data = await Api.admin.listCaregiverAssignments(state.token, state.selectedOrgId);
                    break;
                case "alerts":
                    data = await Api.admin.listAlerts(state.token, state.selectedOrgId);
                    break;
                case "devices":
                    data = await Api.admin.listDevices(state.token, state.selectedOrgId);
                    break;
                case "push-devices":
                    data = await Api.admin.listPushDevices(state.token, state.selectedOrgId);
                    break;
                default:
                    data = [];
            }
            state.tabCache.set(tabName, data);
            tabRenderers[tabName]?.(data);
        } catch (error) {
            handleApiError(error);
            body.innerHTML = `<p class="form-error">${escapeHtml(error.message || "No se pudieron cargar los datos")}</p>`;
        }
    };

    const openOrganization = async (orgId) => {
        const org = state.organizations.find((item) => item.id === orgId);
        if (!org) return;
        state.selectedOrgId = orgId;
        persistState();
        state.orgSummary = null;
        state.orgDashboard = null;
        state.tabCache.clear();

        el.orgDetailSection.classList.remove("hidden");
        el.orgBreadcrumbName.textContent = org.name;
        el.orgTitle.textContent = org.name;
        el.orgMeta.textContent = `Código ${org.code}`;
        el.sessionOrgContext.textContent = org.name;
        el.sessionOrgContext.classList.remove("hidden");
        renderMetricCards(null);
        renderOverview();
        el.tabs[0].click();

        try {
            const [summary, dashboard] = await Promise.all([
                Api.admin.organizationSummary(state.token, orgId),
                Api.admin.dashboard(state.token, orgId),
            ]);
            state.orgSummary = summary;
            state.orgDashboard = dashboard;
            
            // Actualizar el encabezado con la fecha de creación
            if (summary.organization) {
                const createdDate = summary.organization.createdAt || summary.organization.joinedAt;
                el.orgMeta.textContent = `Código ${summary.organization.code} · Creada el ${formatDate(createdDate)}`;
            }
            
            renderMetricCards(summary.stats);
            renderOverview();
        } catch (error) {
            handleApiError(error);
        }
    };

    const loadOrganizations = async () => {
        setLoadingContainer(el.orgGrid, "Cargando organizaciones...");
        try {
            const organizations = await Api.admin.listOrganizations(state.token);
            const hasOrgAdminRole = organizations.some((org) => (org.roleCode || "").toLowerCase() === "org_admin");
            if (!hasOrgAdminRole && organizations.length) {
                showToast("No se encontró rol org_admin en las organizaciones", "warning");
            }
            state.organizations = organizations;
            renderOrganizations();
            if (state.selectedOrgId && organizations.some((org) => org.id === state.selectedOrgId)) {
                openOrganization(state.selectedOrgId);
            } else {
                resetOrgView();
            }
        } catch (error) {
            handleApiError(error);
            el.orgGrid.innerHTML = `<p class="form-error">${escapeHtml(error.message || "No se pudieron obtener las organizaciones")}</p>`;
        }
    };

    const logout = () => {
        state.token = null;
        state.user = null;
        state.organizations = [];
        resetOrgView();
        persistState();
        el.sessionInfo.classList.add("hidden");
        el.logoutButton.classList.add("hidden");
        el.orgGrid.innerHTML = "";
        el.loginForm.reset();
        showView("login");
    };

    const login = async (email, password) => {
        el.loginError.classList.add("hidden");
        try {
            const { access_token: accessToken } = await Api.auth.login(email, password);
            if (!accessToken) {
                throw new Error("El servicio de autenticación no devolvió un token válido");
            }
            state.token = accessToken;
            persistState();
            const me = await Api.auth.me(accessToken);
            state.user = me?.data || null;
            persistState();
            el.sessionUserName.textContent = state.user?.name || state.user?.email || "Administrador";
            el.sessionInfo.classList.remove("hidden");
            el.logoutButton.classList.remove("hidden");
            el.welcomeName.textContent = state.user?.name || "Administrador";
            el.welcomeEmail.textContent = state.user?.email || "";
            showView("dashboard");
            await loadOrganizations();
        } catch (error) {
            handleApiError(error);
            el.loginError.textContent = error.message || "No fue posible iniciar sesión";
            el.loginError.classList.remove("hidden");
        }
    };

    const showPatientModal = (patient = null) => {
        const isEdit = !!patient;
        const modalHtml = `
            <div class="modal-overlay" id="patientModalOverlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${isEdit ? 'Editar Paciente' : 'Nuevo Paciente'}</h3>
                        <button class="modal-close" onclick="document.getElementById('patientModalOverlay').remove()">&times;</button>
                    </div>
                    <form id="patientForm" class="modal-form">
                        <div class="form-group">
                            <label for="patientName">Nombre completo *</label>
                            <input type="text" id="patientName" name="name" value="${escapeHtml(patient?.name || '')}" required>
                        </div>
                        <div class="form-group">
                            <label for="patientEmail">Correo electrónico *</label>
                            <input type="email" id="patientEmail" name="email" value="${escapeHtml(patient?.email || '')}" ${isEdit ? 'disabled' : 'required'}>
                        </div>
                        ${!isEdit ? `
                        <div class="form-group">
                            <label for="patientPassword">Contraseña *</label>
                            <input type="password" id="patientPassword" name="password" required minlength="6">
                        </div>
                        ` : ''}
                        <div class="form-group">
                            <label for="patientBirthdate">Fecha de nacimiento</label>
                            <input type="date" id="patientBirthdate" name="birthdate" value="${patient?.birthdate || ''}">
                        </div>
                        <div class="form-group">
                            <label for="patientRiskLevel">Nivel de riesgo</label>
                            <select id="patientRiskLevel" name="risk_level_id">
                                <option value="">-- Sin especificar --</option>
                                <option value="low" ${patient?.riskLevelCode === 'low' ? 'selected' : ''}>Bajo</option>
                                <option value="medium" ${patient?.riskLevelCode === 'medium' ? 'selected' : ''}>Medio</option>
                                <option value="high" ${patient?.riskLevelCode === 'high' ? 'selected' : ''}>Alto</option>
                            </select>
                        </div>
                        <div class="form-error hidden" id="patientFormError"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('patientModalOverlay').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">${isEdit ? 'Actualizar' : 'Crear'}</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const form = document.getElementById('patientForm');
        const errorEl = document.getElementById('patientFormError');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.add('hidden');
            
            const formData = new FormData(form);
            const payload = {
                name: formData.get('name'),
                birthdate: formData.get('birthdate') || null,
                risk_level_id: formData.get('risk_level_id') || null,
            };
            
            if (!isEdit) {
                payload.email = formData.get('email');
                payload.password = formData.get('password');
            }
            
            try {
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = isEdit ? 'Actualizando...' : 'Creando...';
                
                if (isEdit) {
                    await Api.admin.updatePatient(state.token, state.selectedOrgId, patient.id, payload);
                } else {
                    await Api.admin.createPatient(state.token, state.selectedOrgId, payload);
                }
                
                document.getElementById('patientModalOverlay').remove();
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('patients');
                await activateTab('patients');
            } catch (error) {
                errorEl.textContent = error.message || 'Error al guardar el paciente';
                errorEl.classList.remove('hidden');
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? 'Actualizar' : 'Crear';
            }
        });
    };

    const showInvitationModal = async () => {
        let roles = [];
        try {
            roles = await Api.admin.listRoles(state.token);
        } catch (error) {
            console.error('Error loading roles:', error);
        }
        
        const modalHtml = `
            <div class="modal-overlay" id="invitationModalOverlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Invitar Miembro del Staff</h3>
                        <button class="modal-close" onclick="document.getElementById('invitationModalOverlay').remove()">&times;</button>
                    </div>
                    <form id="invitationForm" class="modal-form">
                        <div class="form-group">
                            <label for="invitationEmail">Correo electrónico *</label>
                            <input type="email" id="invitationEmail" name="email" placeholder="usuario@ejemplo.com" required>
                            <small class="form-hint">Se enviará una invitación a este correo</small>
                        </div>
                        <div class="form-group">
                            <label for="invitationRole">Rol *</label>
                            <select id="invitationRole" name="role_code" required>
                                <option value="">-- Selecciona un rol --</option>
                                ${roles.map(role => `
                                    <option value="${escapeHtml(role.code)}">${escapeHtml(role.label)}</option>
                                `).join('')}
                            </select>
                            <small class="form-hint">El rol determina los permisos del usuario</small>
                        </div>
                        <div class="form-group">
                            <label for="invitationTTL">Vigencia (horas)</label>
                            <input type="number" id="invitationTTL" name="ttl_hours" value="24" min="1" max="720">
                            <small class="form-hint">Tiempo en horas que la invitación estará activa (máximo 720)</small>
                        </div>
                        <div class="form-error hidden" id="invitationFormError"></div>
                        <div class="form-success hidden" id="invitationFormSuccess"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('invitationModalOverlay').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">Crear Invitación</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const form = document.getElementById('invitationForm');
        const errorEl = document.getElementById('invitationFormError');
        const successEl = document.getElementById('invitationFormSuccess');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.add('hidden');
            successEl.classList.add('hidden');
            
            const formData = new FormData(form);
            const payload = {
                email: formData.get('email'),
                role_code: formData.get('role_code'),
                ttl_hours: parseInt(formData.get('ttl_hours')) || 24,
            };
            
            try {
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Generando invitación...';
                
                const invitation = await Api.admin.createStaffInvitation(state.token, state.selectedOrgId, payload);
                
                successEl.innerHTML = `
                    <strong>¡Invitación creada exitosamente!</strong><br>
                    Token: <code style="word-break: break-all;">${escapeHtml(invitation.token)}</code><br>
                    Expira: ${escapeHtml(formatDateTime(invitation.expiresAt))}
                `;
                successEl.classList.remove('hidden');
                
                // Reset form
                form.reset();
                submitBtn.disabled = false;
                submitBtn.textContent = 'Crear Invitación';
                
                // Clear cache to reload staff data
                state.tabCache.delete('staff');
                
                // Show success toast
                showToast('Invitación creada exitosamente', 'success');
                
                // Close modal after 3 seconds
                setTimeout(() => {
                    document.getElementById('invitationModalOverlay')?.remove();
                    activateTab('staff');
                }, 3000);
                
            } catch (error) {
                errorEl.textContent = error.message || 'Error al crear la invitación';
                errorEl.classList.remove('hidden');
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Crear Invitación';
            }
        });
    };

    const showCareTeamCreateModal = () => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización antes de crear un equipo", "warning");
            return;
        }

        const modalHtml = `
            <div class="modal-overlay" id="careTeamCreateModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Nuevo equipo de cuidado</h3>
                        <button class="modal-close" type="button" onclick="document.getElementById('careTeamCreateModal').remove()">&times;</button>
                    </div>
                    <form id="careTeamCreateForm" class="modal-form">
                        <div class="form-group">
                            <label for="careTeamName">Nombre del equipo *</label>
                            <input type="text" id="careTeamName" name="name" maxlength="80" required>
                        </div>
                        <div class="form-error hidden" id="careTeamCreateError"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('careTeamCreateModal').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">Crear</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const form = document.getElementById('careTeamCreateForm');
        const errorEl = document.getElementById('careTeamCreateError');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorEl.classList.add('hidden');

            const formData = new FormData(form);
            const name = (formData.get('name') || '').toString().trim();
            if (!name) {
                errorEl.textContent = 'Ingresa el nombre del equipo';
                errorEl.classList.remove('hidden');
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creando...';

            try {
                await Api.admin.createCareTeam(state.token, state.selectedOrgId, { name });
                document.getElementById('careTeamCreateModal')?.remove();
                showToast('Equipo creado correctamente', 'success');
                state.tabCache.delete('care-teams');
                await activateTab('care-teams');
            } catch (error) {
                errorEl.textContent = error.message || 'No se pudo crear el equipo';
                errorEl.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Crear';
            }
        });
    };

    const CARE_TEAM_DETAIL_OVERLAY_ID = 'careTeamDetailOverlay';

    const closeCareTeamDetailModal = () => {
        document.getElementById(CARE_TEAM_DETAIL_OVERLAY_ID)?.remove();
        state.activeCareTeamDetail = null;
    };

    const loadCareTeamSupportData = async () => {
        const [roles, staff, patients] = await Promise.all([
            Api.admin.listCareTeamRoles(state.token, state.selectedOrgId),
            Api.admin.listStaff(state.token, state.selectedOrgId),
            Api.admin.listPatients(state.token, state.selectedOrgId),
        ]);
        state.careTeamRoles = roles || [];
        state.availableStaff = Array.isArray(staff) ? staff : [];
        state.availablePatients = Array.isArray(patients) ? patients : [];
    };

    const renderCareTeamDetailModal = () => {
        const overlay = document.getElementById(CARE_TEAM_DETAIL_OVERLAY_ID);
        if (!overlay) return;
        const contentEl = overlay.querySelector('#careTeamDetailContent');
        if (!contentEl) return;

        const detail = state.activeCareTeamDetail;
        if (!detail?.team) {
            contentEl.innerHTML = '<p class="form-error">No se pudo cargar la información del equipo.</p>';
            return;
        }

        const { team, members = [], patients = [] } = detail;
        const assignedUserIds = new Set(members.map((member) => member.userId));
        const assignedPatientIds = new Set(patients.map((patient) => patient.patientId));

        const availableMemberOptions = state.availableStaff
            .filter((staffMember) => !assignedUserIds.has(staffMember.userId))
            .map((staffMember) => `<option value="${escapeHtml(staffMember.userId)}">${escapeHtml(staffMember.name)} (${escapeHtml(staffMember.email)})</option>`) // eslint-disable-line max-len
            .join('');

        const roleOptions = state.careTeamRoles
            .map((role) => `<option value="${escapeHtml(role.id)}">${escapeHtml(role.label)}</option>`)
            .join('');

        const availablePatientOptions = state.availablePatients
            .filter((patient) => !assignedPatientIds.has(patient.id))
            .map((patient) => `<option value="${escapeHtml(patient.id)}">${escapeHtml(patient.name)} (${escapeHtml(patient.email || 'Sin correo')})</option>`) // eslint-disable-line max-len
            .join('');

        const membersTable = members.length
            ? `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Correo</th>
                                <th>Rol</th>
                                <th>Miembro desde</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${members.map((member) => `
                                <tr>
                                    <td>${escapeHtml(member.name)}</td>
                                    <td>${escapeHtml(member.email)}</td>
                                    <td>${escapeHtml(member.roleLabel || member.roleCode)}</td>
                                    <td>${escapeHtml(formatDate(member.joinedAt))}</td>
                                    <td>
                                        <button class="btn btn-sm btn-danger" onclick="window.app.removeCareTeamMember('${escapeHtml(team.id)}', '${escapeHtml(member.userId)}')">Quitar</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `
            : '<p class="muted">No hay miembros asignados.</p>';

        const patientsTable = patients.length
            ? `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Paciente</th>
                                <th>Correo</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${patients.map((patient) => `
                                <tr>
                                    <td>${escapeHtml(patient.name)}</td>
                                    <td>${escapeHtml(patient.email)}</td>
                                    <td>
                                        <button class="btn btn-sm btn-danger" onclick="window.app.removeCareTeamPatient('${escapeHtml(team.id)}', '${escapeHtml(patient.patientId)}')">Quitar</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `
            : '<p class="muted">No hay pacientes asignados.</p>';

        const memberForm = availableMemberOptions && roleOptions
            ? `
                <form id="careTeamAddMemberForm" class="care-team-inline-form">
                    <div class="form-group">
                        <label for="careTeamMemberSelect">Selecciona un usuario</label>
                        <select id="careTeamMemberSelect" name="user_id" required>
                            <option value="">-- Selecciona un miembro --</option>
                            ${availableMemberOptions}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="careTeamRoleSelect">Rol</label>
                        <select id="careTeamRoleSelect" name="role_id" required>
                            <option value="">-- Selecciona un rol --</option>
                            ${roleOptions}
                        </select>
                    </div>
                    <div class="form-error hidden" id="careTeamMemberFormError"></div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Agregar miembro</button>
                    </div>
                </form>
            `
            : '<p class="muted">No hay usuarios disponibles para asignar o faltan roles configurados.</p>';

        const patientForm = availablePatientOptions
            ? `
                <form id="careTeamAddPatientForm" class="care-team-inline-form">
                    <div class="form-group">
                        <label for="careTeamPatientSelect">Selecciona un paciente</label>
                        <select id="careTeamPatientSelect" name="patient_id" required>
                            <option value="">-- Selecciona un paciente --</option>
                            ${availablePatientOptions}
                        </select>
                    </div>
                    <div class="form-error hidden" id="careTeamPatientFormError"></div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Agregar paciente</button>
                    </div>
                </form>
            `
            : '<p class="muted">No hay pacientes disponibles para asignar.</p>';

        contentEl.innerHTML = `
            <section class="care-team-summary">
                <p><strong>Nombre:</strong> ${escapeHtml(team.name)}</p>
                <p><strong>ID:</strong> <code>${escapeHtml(team.id)}</code></p>
                <p><strong>Creado el:</strong> ${escapeHtml(formatDate(team.createdAt))}</p>
                <p><strong>Miembros asignados:</strong> ${members.length}</p>
                <p><strong>Pacientes asignados:</strong> ${patients.length}</p>
            </section>
            <section class="care-team-section">
                <header class="care-team-section__header">
                    <h4>Miembros del equipo</h4>
                </header>
                ${membersTable}
                ${memberForm}
            </section>
            <section class="care-team-section">
                <header class="care-team-section__header">
                    <h4>Pacientes asignados</h4>
                </header>
                ${patientsTable}
                ${patientForm}
            </section>
        `;

        const memberFormEl = contentEl.querySelector('#careTeamAddMemberForm');
        if (memberFormEl) {
            memberFormEl.addEventListener('submit', async (event) => {
                event.preventDefault();
                const formData = new FormData(memberFormEl);
                const payload = {
                    user_id: formData.get('user_id'),
                    role_id: formData.get('role_id'),
                };
                const errorEl = memberFormEl.querySelector('#careTeamMemberFormError');
                const submitBtn = memberFormEl.querySelector('button[type="submit"]');
                errorEl.classList.add('hidden');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Agregando...';
                try {
                    await Api.admin.addCareTeamMember(state.token, state.selectedOrgId, team.id, payload);
                    showToast('Miembro asignado correctamente', 'success');
                    await refreshCareTeamDetail(team.id);
                } catch (error) {
                    errorEl.textContent = error.message || 'No se pudo asignar el miembro';
                    errorEl.classList.remove('hidden');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Agregar miembro';
                }
            });
        }

        const patientFormEl = contentEl.querySelector('#careTeamAddPatientForm');
        if (patientFormEl) {
            patientFormEl.addEventListener('submit', async (event) => {
                event.preventDefault();
                const formData = new FormData(patientFormEl);
                const payload = {
                    patient_id: formData.get('patient_id'),
                };
                const errorEl = patientFormEl.querySelector('#careTeamPatientFormError');
                const submitBtn = patientFormEl.querySelector('button[type="submit"]');
                errorEl.classList.add('hidden');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Agregando...';
                try {
                    await Api.admin.addCareTeamPatient(state.token, state.selectedOrgId, team.id, payload);
                    showToast('Paciente asignado correctamente', 'success');
                    await refreshCareTeamDetail(team.id);
                } catch (error) {
                    errorEl.textContent = error.message || 'No se pudo asignar el paciente';
                    errorEl.classList.remove('hidden');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Agregar paciente';
                }
            });
        }
    };

    const refreshCareTeamDetail = async (careTeamId) => {
        try {
            const detail = await Api.admin.getCareTeam(state.token, state.selectedOrgId, careTeamId);
            state.activeCareTeamDetail = detail;
            await loadCareTeamSupportData();
            renderCareTeamDetailModal();
        } catch (error) {
            handleApiError(error);
            const contentEl = document.getElementById('careTeamDetailContent');
            if (contentEl) {
                contentEl.innerHTML = `<p class="form-error">${escapeHtml(error.message || 'No se pudo actualizar el equipo')}</p>`;
            }
        }
    };

    const showCareTeamDetailModal = async (careTeamId) => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización para ver los equipos", "warning");
            return;
        }

        const existingOverlay = document.getElementById(CARE_TEAM_DETAIL_OVERLAY_ID);
        if (existingOverlay) existingOverlay.remove();

        const modalHtml = `
            <div class="modal-overlay" id="${CARE_TEAM_DETAIL_OVERLAY_ID}">
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <h3>Equipo de cuidado</h3>
                        <button class="modal-close" type="button" id="careTeamDetailCloseBtn">&times;</button>
                    </div>
                    <div class="modal-body" id="careTeamDetailContent">
                        <div class="loader"><span class="spinner"></span>Cargando equipo...</div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-ghost" id="careTeamDetailCloseFooter">Cerrar</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('careTeamDetailCloseBtn')?.addEventListener('click', closeCareTeamDetailModal);
        document.getElementById('careTeamDetailCloseFooter')?.addEventListener('click', closeCareTeamDetailModal);

        try {
            const [detail] = await Promise.all([
                Api.admin.getCareTeam(state.token, state.selectedOrgId, careTeamId),
                loadCareTeamSupportData(),
            ]);
            state.activeCareTeamDetail = detail;
            if (!detail) {
                const contentEl = document.getElementById('careTeamDetailContent');
                if (contentEl) {
                    contentEl.innerHTML = '<p class="form-error">No se encontró el equipo solicitado.</p>';
                }
                return;
            }
            renderCareTeamDetailModal();
        } catch (error) {
            handleApiError(error);
            const contentEl = document.getElementById('careTeamDetailContent');
            if (contentEl) {
                contentEl.innerHTML = `<p class="form-error">${escapeHtml(error.message || 'No se pudo cargar el equipo')}</p>`;
            }
        }
    };

    const bindEvents = () => {
        el.loginForm?.addEventListener("submit", (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const email = form.email.value;
            const password = form.password.value;
            if (!email || !password) {
                el.loginError.textContent = "Completa correo y contraseña";
                el.loginError.classList.remove("hidden");
                return;
            }
            const submitButton = form.querySelector("button[type=submit]");
            const previousText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = "Validando...";
            login(email, password).finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = previousText;
            });
        });

        el.logoutButton?.addEventListener("click", () => {
            logout();
        });

        el.refreshOrgs?.addEventListener("click", () => {
            loadOrganizations();
        });

        el.orgGrid?.addEventListener("click", (event) => {
            const card = event.target.closest(".org-card");
            if (!card) return;
            const orgId = card.dataset.orgId;
            openOrganization(orgId);
        });

        el.backToOrgs?.addEventListener("click", () => {
            resetOrgView();
        });

        el.tabs.forEach((tab) => {
            tab.addEventListener("click", () => {
                const tabName = tab.dataset.tab;
                activateTab(tabName);
            });
        });

        // New CRUD button handlers
        el.buttons.inviteStaff?.addEventListener("click", () => {
            showInvitationModal();
        });

        el.buttons.createCareTeam?.addEventListener("click", () => {
            showCareTeamCreateModal();
        });

        el.buttons.createPatient?.addEventListener("click", () => {
            showPatientModal();
        });

        el.buttons.createAlert?.addEventListener("click", () => {
            // TODO: Open modal form for creating alert
            console.log("Create alert clicked");
        });

        el.buttons.createDevice?.addEventListener("click", () => {
            // TODO: Open modal form for creating device
            console.log("Create device clicked");
        });

        el.buttons.refreshPushDevices?.addEventListener("click", () => {
            activateTab("push-devices");
        });
    };

    const bootstrap = async () => {
        restoreState();
        bindEvents();
        if (state.token) {
            try {
                const me = await Api.auth.me(state.token);
                state.user = me?.data || null;
                el.sessionUserName.textContent = state.user?.name || state.user?.email || "Administrador";
                el.sessionInfo.classList.remove("hidden");
                el.logoutButton.classList.remove("hidden");
                el.welcomeName.textContent = state.user?.name || "Administrador";
                el.welcomeEmail.textContent = state.user?.email || "";
                showView("dashboard");
                await loadOrganizations();
            } catch (error) {
                console.warn("Sesión inválida, se pedirá login", error);
                logout();
            }
        } else {
            showView("login");
        }
    };

    // Expose global functions for inline onclick handlers
    window.app = {
        editPatient: async (patientId) => {
            try {
                const patient = await Api.admin.getPatient(state.token, state.selectedOrgId, patientId);
                if (patient) {
                    showPatientModal(patient);
                }
            } catch (error) {
                handleApiError(error);
            }
        },
        deletePatient: async (patientId) => {
            if (!confirm("¿Está seguro de eliminar este paciente? Esta acción no se puede deshacer.")) return;
            try {
                await Api.admin.deletePatient(state.token, state.selectedOrgId, patientId);
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('patients');
                await activateTab("patients");
            } catch (error) {
                handleApiError(error);
            }
        },
        revokeInvitation: async (invitationId) => {
            if (!confirm("¿Está seguro de revocar esta invitación? Esta acción no se puede deshacer.")) return;
            try {
                await Api.admin.revokeInvitation(state.token, state.selectedOrgId, invitationId);
                showToast('Invitación revocada exitosamente', 'success');
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('staff');
                await activateTab("staff");
            } catch (error) {
                handleApiError(error);
            }
        },
        openCareTeamDetail: async (careTeamId) => {
            try {
                await showCareTeamDetailModal(careTeamId);
            } catch (error) {
                handleApiError(error);
            }
        },
        deleteCareTeam: async (careTeamId, teamName = '') => {
            const label = teamName ? ` "${teamName}"` : '';
            if (!confirm(`¿Eliminar el equipo${label}? Debe estar vacío para poder eliminarlo.`)) return;
            try {
                await Api.admin.deleteCareTeam(state.token, state.selectedOrgId, careTeamId);
                showToast('Equipo eliminado correctamente', 'success');
                closeCareTeamDetailModal();
                state.tabCache.delete('care-teams');
                await activateTab('care-teams');
            } catch (error) {
                if (error?.status === 409) {
                    showToast(error.message || 'El equipo aún tiene miembros o pacientes asignados', 'warning');
                } else {
                    handleApiError(error);
                }
            }
        },
        removeCareTeamMember: async (careTeamId, userId) => {
            if (!confirm('¿Quitar este miembro del equipo?')) return;
            try {
                await Api.admin.removeCareTeamMember(state.token, state.selectedOrgId, careTeamId, userId);
                showToast('Miembro eliminado del equipo', 'success');
                await refreshCareTeamDetail(careTeamId);
            } catch (error) {
                handleApiError(error);
            }
        },
        removeCareTeamPatient: async (careTeamId, patientId) => {
            if (!confirm('¿Quitar este paciente del equipo?')) return;
            try {
                await Api.admin.removeCareTeamPatient(state.token, state.selectedOrgId, careTeamId, patientId);
                showToast('Paciente desvinculado del equipo', 'success');
                await refreshCareTeamDetail(careTeamId);
            } catch (error) {
                handleApiError(error);
            }
        },
        editAlert: async (alertId) => {
            console.log("Edit alert:", alertId);
            // TODO: Open modal form with alert data
        },
        deleteAlert: async (alertId) => {
            if (!confirm("¿Está seguro de eliminar esta alerta?")) return;
            try {
                await Api.admin.deleteAlert(state.token, state.selectedOrgId, alertId);
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('alerts');
                await activateTab("alerts");
            } catch (error) {
                handleApiError(error);
            }
        },
        editDevice: async (deviceId) => {
            console.log("Edit device:", deviceId);
            // TODO: Open modal form with device data
        },
        deleteDevice: async (deviceId) => {
            if (!confirm("¿Está seguro de eliminar este dispositivo?")) return;
            try {
                await Api.admin.deleteDevice(state.token, state.selectedOrgId, deviceId);
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('devices');
                await activateTab("devices");
            } catch (error) {
                handleApiError(error);
            }
        },
        togglePushDevice: async (pushDeviceId, activate) => {
            try {
                await Api.admin.togglePushDevice(state.token, state.selectedOrgId, pushDeviceId, activate);
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('push-devices');
                await activateTab("push-devices");
            } catch (error) {
                handleApiError(error);
            }
        },
        deletePushDevice: async (pushDeviceId) => {
            if (!confirm("¿Está seguro de eliminar este push device?")) return;
            try {
                await Api.admin.deletePushDevice(state.token, state.selectedOrgId, pushDeviceId);
                // Limpiar caché para forzar recarga de datos
                state.tabCache.delete('push-devices');
                await activateTab("push-devices");
            } catch (error) {
                handleApiError(error);
            }
        }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootstrap);
    } else {
        bootstrap();
    }
})();
