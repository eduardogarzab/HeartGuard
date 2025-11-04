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
        renderTable(
            container,
            ["Nombre", "Correo", "Rol", "Miembro desde"],
            data,
            (member) => `
                <tr>
                    <td>${escapeHtml(member.name)}</td>
                    <td>${escapeHtml(member.email)}</td>
                    <td>${escapeHtml(member.roleLabel || member.roleCode)}</td>
                    <td>${escapeHtml(formatDate(member.joinedAt))}</td>
                </tr>` ,
            "No se encontraron miembros del staff"
        );
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
            ["Equipo", "Creado el", "ID"],
            careTeams,
            (team) => `
                <tr>
                    <td>${escapeHtml(team.name)}</td>
                    <td>${escapeHtml(formatDate(team.createdAt))}</td>
                    <td><code>${escapeHtml(team.id)}</code></td>
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
                    data = await Api.admin.listStaff(state.token, state.selectedOrgId);
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
