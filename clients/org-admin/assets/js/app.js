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
        groundTruthSelectedPatientId: null,
        groundTruthEventTypes: [],
        alertsFilterStatus: null,
        alertsFilterLevel: null,
        devicesFilterStatus: null,
        pushDevicesFilterStatus: null,
        invitationsFilterStatus: null,
        patientsSearchQuery: '',
        staffSearchQuery: '',
        pagination: {
            patients: { page: 1, perPage: 10 },
            staff: { page: 1, perPage: 10 },
            invitations: { page: 1, perPage: 10 },
            alerts: { page: 1, perPage: 10 },
            devices: { page: 1, perPage: 10 },
            pushDevices: { page: 1, perPage: 10 },
            caregivers: { page: 1, perPage: 10 },
        },
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
            "ground-truth": document.querySelector("#tab-ground-truth"),
            devices: document.querySelector("#tab-devices"),
            "push-devices": document.querySelector("#tab-push-devices"),
        },
        tabBodies: {
            staff: document.querySelector("#staffTable"),
            patients: document.querySelector("#patientsTable"),
            "care-teams": document.querySelector("#careTeamsTable"),
            caregivers: document.querySelector("#caregiversTable"),
            alerts: document.querySelector("#alertsTable"),
            "ground-truth": document.querySelector("#groundTruthTable"),
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
            createGroundTruth: document.querySelector("#btnCreateGroundTruth"),
            refreshGroundTruth: document.querySelector("#btnRefreshGroundTruth"),
            createDevice: document.querySelector("#btnCreateDevice"),
            refreshPushDevices: document.querySelector("#btnRefreshPushDevices"),
        },
        groundTruthPatientFilter: document.querySelector("#groundTruthPatientFilter"),
        patientsSearchInput: document.querySelector("#patientsSearchInput"),
        staffSearchInput: document.querySelector("#staffSearchInput"),
        alertsStatusFilter: document.querySelector("#alertsStatusFilter"),
        alertsLevelFilter: document.querySelector("#alertsLevelFilter"),
        devicesStatusFilter: document.querySelector("#devicesStatusFilter"),
        pushDevicesStatusFilter: document.querySelector("#pushDevicesStatusFilter"),
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

    const toDatetimeLocalValue = (value) => {
        if (!value) return "";
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return "";
            }
            const pad = (num) => String(num).padStart(2, "0");
            const year = date.getFullYear();
            const month = pad(date.getMonth() + 1);
            const day = pad(date.getDate());
            const hours = pad(date.getHours());
            const minutes = pad(date.getMinutes());
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        } catch (err) {
            return "";
        }
    };

    const fromDatetimeLocalValue = (value) => {
        if (!value) return null;
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return null;
            }
            return date.toISOString();
        } catch (err) {
            return null;
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

    const modalSizeClassMap = {
        sm: "modal-sm",
        md: "",
        lg: "modal-lg",
        xl: "modal-xl",
        wide: "modal-wide",
    };

    let modalEventsBound = false;

    const getModalContent = () => el.modal.overlay?.querySelector(".modal-content");

    const setModalTitle = (text) => {
        if (!el.modal.title) return;
        el.modal.title.textContent = text || "";
    };

    const setModalBody = (html) => {
        if (!el.modal.body) return;
        el.modal.body.innerHTML = html || "";
    };

    const setModalFooter = (html) => {
        if (!el.modal.footer) return;
        el.modal.footer.innerHTML = html || "";
    };

    const closeModal = () => {
        if (!el.modal.overlay) return;
        
        // Limpiar timers de actualizaci\u00f3n de signos vitales
        vitalSignsState.timers.forEach((timer) => {
            clearInterval(timer);
        });
        vitalSignsState.timers.clear();
        
        // Destruir instancias de gr\u00e1ficas
        vitalSignsState.charts.forEach((chart) => {
            chart.destroy();
        });
        vitalSignsState.charts.clear();
        
        el.modal.overlay.classList.add("hidden");
        const content = getModalContent();
        if (content) {
            Object.values(modalSizeClassMap)
                .filter(Boolean)
                .forEach((cls) => content.classList.remove(cls));
        }
        setModalTitle("");
        setModalBody("");
        setModalFooter("");
    };

    const openModal = ({
        title = "",
        body = "",
        footer,
        size = "lg",
    } = {}) => {
        if (!el.modal.overlay) return;
        const content = getModalContent();
        if (!content) return;
        Object.values(modalSizeClassMap)
            .filter(Boolean)
            .forEach((cls) => content.classList.remove(cls));
        const sizeClass = modalSizeClassMap[size] || modalSizeClassMap.lg;
        if (sizeClass) {
            content.classList.add(sizeClass);
        }
        setModalTitle(title);
        setModalBody(body);
        if (footer === undefined) {
            setModalFooter('<button type="button" class="btn btn-secondary" data-modal-close>Cerrar</button>');
        } else {
            setModalFooter(footer);
        }
        el.modal.overlay.classList.remove("hidden");
        const modalContent = getModalContent();
        if (modalContent) {
            modalContent.scrollTop = 0;
        }
    };

    const hasItems = (value) => Array.isArray(value) && value.length > 0;

    const paginateArray = (array, page, perPage) => {
        const start = (page - 1) * perPage;
        const end = start + perPage;
        return array.slice(start, end);
    };

    const renderPagination = (totalItems, currentPage, perPage, onPageChange) => {
        if (totalItems <= perPage) return "";
        const totalPages = Math.ceil(totalItems / perPage);
        if (totalPages <= 1) return "";

        const pages = [];
        for (let i = 1; i <= totalPages; i++) {
            pages.push(i);
        }

        const buttons = pages.map((page) => {
            const activeClass = page === currentPage ? "pagination-btn--active" : "";
            return `<button class="pagination-btn ${activeClass}" data-page="${page}" type="button">${page}</button>`;
        });

        return `
            <div class="pagination">
                <button class="pagination-btn" data-page="${currentPage - 1}" type="button" ${currentPage === 1 ? "disabled" : ""}>‹ Anterior</button>
                ${buttons.join("")}
                <button class="pagination-btn" data-page="${currentPage + 1}" type="button" ${currentPage === totalPages ? "disabled" : ""}>Siguiente ›</button>
            </div>
        `;
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
        state.availablePatients = [];
        state.availableStaff = [];
        state.groundTruthEventTypes = [];
        state.groundTruthSelectedPatientId = null;
        if (el.overviewCards) {
            el.overviewCards.innerHTML = "";
        }
        if (el.overviewCharts) {
            el.overviewCharts.innerHTML = "";
        }
        el.orgDetailSection.classList.add("hidden");
        el.sessionOrgContext.textContent = "";
        el.sessionOrgContext.classList.add("hidden");
        if (el.groundTruthPatientFilter) {
            el.groundTruthPatientFilter.value = "";
            el.groundTruthPatientFilter.disabled = true;
        }
        if (el.buttons.createGroundTruth) {
            el.buttons.createGroundTruth.disabled = true;
        }
        if (el.buttons.refreshGroundTruth) {
            el.buttons.refreshGroundTruth.disabled = true;
        }
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
        
        // Filter staff by search query
        let staffMembers = data.members || [];
        if (state.staffSearchQuery) {
            const query = state.staffSearchQuery.toLowerCase();
            staffMembers = staffMembers.filter((m) =>
                (m.name && m.name.toLowerCase().includes(query)) ||
                (m.email && m.email.toLowerCase().includes(query))
            );
        }
        
        // Paginate staff members
        const staffPage = state.pagination.staff.page;
        const staffPerPage = state.pagination.staff.perPage;
        const paginatedStaff = paginateArray(staffMembers, staffPage, staffPerPage);
        
        // Filter invitations by status
        let invitations = data.invitations || [];
        if (state.invitationsFilterStatus) {
            invitations = invitations.filter((inv) => inv.status === state.invitationsFilterStatus);
        }
        
        // Paginate invitations
        const invitationsPage = state.pagination.invitations.page;
        const invitationsPerPage = state.pagination.invitations.perPage;
        const paginatedInvitations = paginateArray(invitations, invitationsPage, invitationsPerPage);
        
        // Build pagination controls
        const staffPagination = renderPagination(staffMembers.length, staffPage, staffPerPage, (page) => {
            state.pagination.staff.page = page;
            renderStaff(data);
        });
        
        const invitationsPagination = renderPagination(invitations.length, invitationsPage, invitationsPerPage, (page) => {
            state.pagination.invitations.page = page;
            renderStaff(data);
        });
        
        // Split into two sections: staff members and invitations
        const staffHtml = `
            <div class="staff-section">
                <h4 class="section-subtitle">Miembros del Staff (${staffMembers.length})</h4>
                ${!paginatedStaff.length ? '<p class="muted">No se encontraron miembros del staff</p>' : `
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
                                ${paginatedStaff.map(member => `
                                    <tr class="table-row-clickable" onclick="window.app.viewStaffProfile('${escapeHtml(member.userId || "")}')">
                                        <td>${escapeHtml(member.name)}</td>
                                        <td>${escapeHtml(member.email)}</td>
                                        <td>${escapeHtml(member.roleLabel || member.roleCode)}</td>
                                        <td>${escapeHtml(formatDate(member.joinedAt))}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${staffPagination}
                `}
            </div>
            <div class="staff-section">
                <h4 class="section-subtitle">Invitaciones (${invitations.length})</h4>
                <div class="filter-row" style="margin-bottom: 1rem;">
                    <label for="invitationsStatusFilterInline">Filtrar por estado:</label>
                    <select id="invitationsStatusFilterInline" class="form-select" style="max-width: 200px;">
                        <option value="">Todos</option>
                        <option value="pending" ${state.invitationsFilterStatus === 'pending' ? 'selected' : ''}>Pendiente</option>
                        <option value="used" ${state.invitationsFilterStatus === 'used' ? 'selected' : ''}>Usada</option>
                        <option value="expired" ${state.invitationsFilterStatus === 'expired' ? 'selected' : ''}>Expirada</option>
                        <option value="revoked" ${state.invitationsFilterStatus === 'revoked' ? 'selected' : ''}>Revocada</option>
                    </select>
                </div>
                ${!paginatedInvitations.length ? '<p class="muted">No hay invitaciones</p>' : `
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
                                ${paginatedInvitations.map(inv => {
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
                    ${invitationsPagination}
                `}
            </div>
        `;
        
        container.innerHTML = staffHtml;
        
        // Bind inline filter
        const inlineFilter = container.querySelector('#invitationsStatusFilterInline');
        if (inlineFilter) {
            inlineFilter.addEventListener('change', (e) => {
                state.invitationsFilterStatus = e.target.value || null;
                state.pagination.invitations.page = 1;
                renderStaff(data);
            });
        }
        
        // Bind pagination clicks
        container.querySelectorAll('.pagination-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page, 10);
                if (Number.isNaN(page) || page < 1) return;
                const section = btn.closest('.staff-section');
                if (section && section.querySelector('.section-subtitle')?.textContent.includes('Miembros')) {
                    state.pagination.staff.page = page;
                } else {
                    state.pagination.invitations.page = page;
                }
                renderStaff(data);
            });
        });
    };

    const renderPatients = (allPatients) => {
        const container = el.tabBodies.patients || el.tabPanels.patients;
        
        let patients = allPatients || [];
        
        // Filter by search query
        if (state.patientsSearchQuery) {
            const query = state.patientsSearchQuery.toLowerCase();
            patients = patients.filter((p) => 
                (p.name && p.name.toLowerCase().includes(query)) ||
                (p.email && p.email.toLowerCase().includes(query))
            );
        }
        
        // Paginate
        const page = state.pagination.patients.page;
        const perPage = state.pagination.patients.perPage;
        const paginated = paginateArray(patients, page, perPage);
        
        const pagination = renderPagination(patients.length, page, perPage, (newPage) => {
            state.pagination.patients.page = newPage;
            renderPatients(allPatients);
        });
        
        if (!paginated.length) {
            container.innerHTML = '<p class="muted">No se encontraron pacientes</p>';
        } else {
            const tableHtml = `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Correo</th>
                                <th>Fecha de nacimiento</th>
                                <th>Riesgo</th>
                                <th>Fecha de ingreso</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${paginated.map(patient => `
                                <tr class="table-row-clickable" onclick="window.app.viewPatientProfile('${escapeHtml(patient.id || "")}')">
                                    <td>${escapeHtml(patient.name)}</td>
                                    <td>${escapeHtml(patient.email)}</td>
                                    <td>${escapeHtml(formatDate(patient.birthdate))}</td>
                                    <td>${buildRiskBadge(patient.riskLevelCode, patient.riskLevelLabel) || '<span class="status-badge">-</span>'}</td>
                                    <td>${escapeHtml(formatDate(patient.createdAt))}</td>
                                    <td onclick="event.stopPropagation();">
                                        <button class="btn btn-sm" onclick="window.app.editPatient('${escapeHtml(patient.id || "")}')">Editar</button>
                                        <button class="btn btn-sm btn-danger" onclick="window.app.deletePatient('${escapeHtml(patient.id || "")}')">Eliminar</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            container.innerHTML = tableHtml + pagination;
        }
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
        
        if (!assignments || assignments.length === 0) {
            container.innerHTML = '<p class="muted">No hay cuidadores asignados</p>';
            return;
        }

        const cardsHtml = assignments.map((assignment) => {
            const isPrimary = assignment.isPrimary;
            const hasEnded = assignment.endedAt && new Date(assignment.endedAt) < new Date();
            const relationshipBadge = assignment.relationshipLabel 
                ? `<span class="status-badge info">${escapeHtml(assignment.relationshipLabel)}</span>`
                : '<span class="status-badge" style="background: #f3f4f6; color: #6b7280;">Sin relación</span>';
            const primaryBadge = isPrimary 
                ? '<span class="status-badge status-success">Principal</span>' 
                : '';
            const endedBadge = hasEnded 
                ? '<span class="status-badge status-danger">Finalizado</span>'
                : '<span class="status-badge" style="background: #d1fae5; color: #059669;">Activo</span>';
            const careTeamBadge = assignment.careTeamName 
                ? `<span class="status-badge" style="background: #dbeafe; color: #1e40af;">👥 ${escapeHtml(assignment.careTeamName)}</span>`
                : '<span class="status-badge" style="background: #f3f4f6; color: #6b7280;">Sin equipo</span>';

            const hasDetails = assignment.endedAt || assignment.note;
            const detailsId = `details-${escapeHtml(assignment.patientId)}-${escapeHtml(assignment.caregiverId)}`;

            return `
                <div class="caregiver-card">
                    <div class="caregiver-card__status-badges">
                        ${primaryBadge}
                        ${endedBadge}
                    </div>
                    
                    <div class="caregiver-card__people">
                        <div class="caregiver-card__person">
                            <div class="caregiver-card__avatar caregiver-card__avatar--caregiver">
                                ${escapeHtml(assignment.caregiverName.charAt(0).toUpperCase())}
                            </div>
                            <div class="caregiver-card__person-info">
                                <div class="caregiver-card__person-header">
                                    <span class="caregiver-card__label">Cuidador</span>
                                    ${relationshipBadge}
                                </div>
                                <h5>${escapeHtml(assignment.caregiverName)}</h5>
                                <p class="card-email">${escapeHtml(assignment.caregiverEmail)}</p>
                            </div>
                        </div>
                        
                        <div class="caregiver-card__arrow">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 5V19M12 19L5 12M12 19L19 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        
                        <div class="caregiver-card__person">
                            <div class="caregiver-card__avatar caregiver-card__avatar--patient">
                                ${escapeHtml(assignment.patientName.charAt(0).toUpperCase())}
                            </div>
                            <div class="caregiver-card__person-info">
                                <span class="caregiver-card__label">Paciente</span>
                                <h5>${escapeHtml(assignment.patientName)}</h5>
                                <p class="card-email">${escapeHtml(assignment.patientEmail || 'Sin correo')}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="caregiver-card__summary">
                        <div class="caregiver-card__summary-item">
                            <span class="caregiver-card__summary-label">Equipo:</span>
                            ${careTeamBadge}
                        </div>
                        <div class="caregiver-card__summary-dates">
                            <div class="caregiver-card__summary-item">
                                <span class="caregiver-card__summary-label">Inicio:</span>
                                <span class="caregiver-card__summary-value">${escapeHtml(formatDate(assignment.startedAt))}</span>
                            </div>
                            ${assignment.endedAt ? `
                                <div class="caregiver-card__summary-item caregiver-card__summary-item--end-date">
                                    <span class="caregiver-card__summary-label">Fin:</span>
                                    <span class="caregiver-card__summary-value">${escapeHtml(formatDate(assignment.endedAt))}</span>
                                </div>
                            ` : ''}
                        </div>
                        <button class="caregiver-card__toggle" onclick="this.closest('.caregiver-card').classList.toggle('expanded')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19 9L12 16L5 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span class="toggle-text-show">Detalles</span>
                            <span class="toggle-text-hide">Ocultar</span>
                        </button>
                    </div>
                    
                    <div class="caregiver-card__details">
                        ${assignment.note ? `
                            <div class="caregiver-card__detail-item">
                                <span class="caregiver-card__detail-label">Nota:</span>
                                <p class="caregiver-card__note-text">${escapeHtml(assignment.note)}</p>
                            </div>
                        ` : '<p class="caregiver-card__no-details">Sin notas adicionales</p>'}
                    </div>
                    
                    <div class="caregiver-card__actions">
                        <button class="btn btn-sm" onclick="window.app.editCaregiverAssignment('${escapeHtml(assignment.patientId)}', '${escapeHtml(assignment.caregiverId)}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M18.5 2.50001C18.8978 2.10219 19.4374 1.87869 20 1.87869C20.5626 1.87869 21.1022 2.10219 21.5 2.50001C21.8978 2.89784 22.1213 3.4374 22.1213 4.00001C22.1213 4.56262 21.8978 5.10219 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Editar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="window.app.deleteCaregiverAssignment('${escapeHtml(assignment.patientId)}', '${escapeHtml(assignment.caregiverId)}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Eliminar
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="caregiver-cards">${cardsHtml}</div>`;
    };

    const renderAlerts = (allAlerts) => {
        const container = el.tabBodies.alerts || el.tabPanels.alerts;
        
        // Filter alerts by status and level
        let alerts = allAlerts || [];
        if (state.alertsFilterStatus) {
            alerts = alerts.filter((alert) => alert.statusCode === state.alertsFilterStatus);
        }
        if (state.alertsFilterLevel) {
            alerts = alerts.filter((alert) => alert.levelCode === state.alertsFilterLevel);
        }
        
        // Paginate
        const page = state.pagination.alerts.page;
        const perPage = state.pagination.alerts.perPage;
        const paginated = paginateArray(alerts, page, perPage);
        
        const pagination = renderPagination(alerts.length, page, perPage, (newPage) => {
            state.pagination.alerts.page = newPage;
            renderAlerts(allAlerts);
        });
        
        if (!paginated.length) {
            container.innerHTML = '<p class="muted">No se han generado alertas</p>';
        } else {
            const tableHtml = `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Paciente</th>
                                <th>Descripción</th>
                                <th>Nivel</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${paginated.map(alert => `
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
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            container.innerHTML = tableHtml + pagination;
        }
    };

    const renderGroundTruth = (data) => {
        const container = el.tabBodies["ground-truth"] || el.tabPanels["ground-truth"];
        if (!container) return;

        const labels = Array.isArray(data) ? data : data?.labels ?? [];

        if (el.groundTruthPatientFilter) {
            el.groundTruthPatientFilter.value = state.groundTruthSelectedPatientId || "";
        }

        if (!state.availablePatients.length) {
            container.innerHTML = '<p class="muted">No hay pacientes registrados en la organización.</p>';
            return;
        }

        if (!state.groundTruthSelectedPatientId) {
            container.innerHTML = '<p class="muted">Selecciona un paciente para ver sus etiquetas.</p>';
            return;
        }

        if (!labels.length) {
            container.innerHTML = '<p class="muted">No se encontraron etiquetas ground truth para este paciente.</p>';
            return;
        }

        renderTable(
            container,
            ["Evento", "Inicio", "Fin", "Anotado por", "Fuente", "Nota", "Acciones"],
            labels,
            (label) => {
                const noteFull = label.note || "-";
                const notePreview = noteFull.length > 80 ? `${noteFull.slice(0, 77)}...` : noteFull;
                const annotatedBy = label.annotatedByName || label.annotatedByUserId || "No especificado";
                const eventLabel = label.eventTypeLabel || label.eventTypeCode || "-";
                const patientId = label.patientId || state.groundTruthSelectedPatientId || "";
                const onset = label.onset ? formatDateTime(label.onset) : "-";
                const offset = label.offsetAt ? formatDateTime(label.offsetAt) : "-";
                const source = label.source || "-";

                return `
                    <tr>
                        <td>${escapeHtml(eventLabel)}</td>
                        <td>${escapeHtml(onset)}</td>
                        <td>${escapeHtml(offset)}</td>
                        <td>${escapeHtml(annotatedBy)}</td>
                        <td>${escapeHtml(source)}</td>
                        <td title="${escapeHtml(noteFull)}">${escapeHtml(notePreview)}</td>
                        <td>
                            <button class="btn btn-sm" onclick="window.app.editGroundTruth('${escapeHtml(patientId)}', '${escapeHtml(label.id)}')">Editar</button>
                            <button class="btn btn-sm btn-danger" onclick="window.app.deleteGroundTruth('${escapeHtml(patientId)}', '${escapeHtml(label.id)}')">Eliminar</button>
                        </td>
                    </tr>`;
            },
            "No se encontraron etiquetas ground truth"
        );
    };

    const renderDevices = (allDevices) => {
        const container = el.tabBodies.devices || el.tabPanels.devices;
        
        // Filter by status
        let devices = allDevices || [];
        if (state.devicesFilterStatus) {
            const isActive = state.devicesFilterStatus === 'active';
            devices = devices.filter((device) => device.active === isActive);
        }
        
        // Paginate
        const page = state.pagination.devices.page;
        const perPage = state.pagination.devices.perPage;
        const paginated = paginateArray(devices, page, perPage);
        
        const pagination = renderPagination(devices.length, page, perPage, (newPage) => {
            state.pagination.devices.page = newPage;
            renderDevices(allDevices);
        });
        
        if (!paginated.length) {
            container.innerHTML = '<p class="muted">No se encontraron dispositivos</p>';
        } else {
            const tableHtml = `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Serial</th>
                                <th>Tipo</th>
                                <th>Marca</th>
                                <th>Modelo</th>
                                <th>Paciente asignado</th>
                                <th>Estado</th>
                                <th>Registrado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${paginated.map(device => `
                                <tr>
                                    <td><code>${escapeHtml(device.serial)}</code></td>
                                    <td>${escapeHtml(device.deviceTypeLabel || device.deviceTypeCode || "-")}</td>
                                    <td>${escapeHtml(device.brand || "-")}</td>
                                    <td>${escapeHtml(device.model || "-")}</td>
                                    <td>${escapeHtml(device.ownerPatientName || "-")}</td>
                                    <td><span class="status-badge ${device.active ? "success" : ""}">${device.active ? "Activo" : "Inactivo"}</span></td>
                                    <td>${escapeHtml(formatDateTime(device.registeredAt))}</td>
                                    <td>
                                        <button class="btn btn-sm" onclick="window.app.editDevice('${escapeHtml(device.id)}')">Editar</button>
                                        <button class="btn btn-sm btn-danger" onclick="window.app.deleteDevice('${escapeHtml(device.id)}')">Eliminar</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            container.innerHTML = tableHtml + pagination;
        }
    };

    const renderPushDevices = (allPushDevices) => {
        const container = el.tabBodies["push-devices"] || el.tabPanels["push-devices"];
        
        // Filter by status
        let pushDevices = allPushDevices || [];
        if (state.pushDevicesFilterStatus) {
            const isActive = state.pushDevicesFilterStatus === 'active';
            pushDevices = pushDevices.filter((pd) => pd.active === isActive);
        }
        
        // Paginate
        const page = state.pagination.pushDevices.page;
        const perPage = state.pagination.pushDevices.perPage;
        const paginated = paginateArray(pushDevices, page, perPage);
        
        const pagination = renderPagination(pushDevices.length, page, perPage, (newPage) => {
            state.pagination.pushDevices.page = newPage;
            renderPushDevices(allPushDevices);
        });
        
        if (!paginated.length) {
            container.innerHTML = '<p class="muted">No se encontraron push devices</p>';
        } else {
            const tableHtml = `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Usuario</th>
                                <th>Plataforma</th>
                                <th>Token</th>
                                <th>Estado</th>
                                <th>Último uso</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${paginated.map(pd => {
                                const tokenPreview = pd.pushToken ? `${escapeHtml(pd.pushToken.slice(0, 20))}…` : "-";
                                const statusBadge = pd.active
                                    ? buildStatusBadge('Activo', 'status-success')
                                    : buildStatusBadge('Inactivo', 'status-muted');
                                return `
                                <tr>
                                    <td>${escapeHtml(pd.userName || pd.userEmail || "-")}</td>
                                    <td><span class="status-badge">${escapeHtml(pd.platformLabel || pd.platformCode || "-")}</span></td>
                                    <td><code title="${escapeHtml(pd.pushToken || "Sin token")}">${tokenPreview}</code></td>
                                    <td>${statusBadge}</td>
                                    <td>${escapeHtml(formatDateTime(pd.lastSeenAt))}</td>
                                    <td>
                                        <button class="btn btn-sm" onclick="window.app.togglePushDevice('${escapeHtml(pd.id)}', ${!pd.active})">${pd.active ? "Desactivar" : "Activar"}</button>
                                        <button class="btn btn-sm btn-danger" onclick="window.app.deletePushDevice('${escapeHtml(pd.id)}')">Eliminar</button>
                                    </td>
                                </tr>`;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            container.innerHTML = tableHtml + pagination;
        }
    };

    const buildStatusBadge = (label, variant = "") => {
        if (!label) return "";
        const classes = ["status-badge"];
        if (variant) classes.push(variant);
        return `<span class="${classes.join(" ")}">${escapeHtml(label)}</span>`;
    };

    const buildRiskBadge = (riskCode, riskLabel) => {
        if (!riskCode && !riskLabel) return "";
        const code = (riskCode || "").toLowerCase();
        let variant = "";
        if (code === "high" || code === "critical") {
            variant = "status-danger";
        } else if (code === "medium" || code === "moderate") {
            variant = "status-warning";
        } else if (code === "low") {
            variant = "status-success";
        }
        return buildStatusBadge(riskLabel || riskCode, variant);
    };

    const buildAlertLevelBadge = (levelCode, levelLabel) => {
        if (!levelCode && !levelLabel) return "";
        const code = (levelCode || "").toLowerCase();
        let variant = "";
        if (code === "critical" || code === "high") {
            variant = "status-danger";
        } else if (code === "medium" || code === "moderate") {
            variant = "status-warning";
        } else if (code === "low") {
            variant = "status-success";
        }
        return buildStatusBadge(levelLabel || levelCode, variant);
    };

    const buildChips = (items) => {
        if (!hasItems(items)) return "";
        const chips = items.map((item) => `<span class="profile-chip">${escapeHtml(item)}</span>`);
        return `<div class="profile-chips">${chips.join("")}</div>`;
    };

    const truncate = (value, length = 24) => {
        if (!value) return "-";
        const stringValue = String(value);
        if (stringValue.length <= length) {
            return stringValue;
        }
        return `${stringValue.slice(0, length)}…`;
    };

    const renderListOrEmpty = (items, renderItem, emptyMessage) => {
        if (!hasItems(items)) {
            return `<p class="muted">${escapeHtml(emptyMessage)}</p>`;
        }
        return `<ul class="profile-list">${items.map((item) => renderItem(item).trim()).join("")}</ul>`;
    };

    const renderProfileStats = (items) => {
        const rows = (items || []).filter((item) => item && item.label !== undefined);
        if (!rows.length) return "";
        return `<div class="profile-stats">${rows
            .map((item) => `
                <div class="profile-stat">
                    <span class="profile-stat__value">${escapeHtml(String(item.value ?? 0))}</span>
                    <span class="profile-stat__label">${escapeHtml(item.label)}</span>
                </div>
            `.trim())
            .join("")}</div>`;
    };

    const buildDetailList = (rows = []) => {
        const safeRows = rows.filter((row) => row && row.label);
        if (!safeRows.length) return "";
        return `<dl class="profile-dl">${safeRows
            .map((row) => {
                const value = row.html ? row.value : escapeHtml(row.value ?? "-");
                return `
                    <dt>${escapeHtml(row.label)}</dt>
                    <dd>${value}</dd>
                `.trim();
            })
            .join("")}</dl>`;
    };

    const formatCoordinate = (value) => {
        const num = Number(value);
        if (!Number.isFinite(num)) return "-";
        return num.toFixed(5);
    };

    const buildMapSection = (location) => {
        if (!location) {
            return '<p class="muted">Sin ubicaciones recientes registradas.</p>';
        }
        const lat = Number(location.latitude);
        const lon = Number(location.longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            return '<p class="muted">Ubicación más reciente sin coordenadas válidas.</p>';
        }
        const delta = 0.01;
        const bboxCoords = [
            lon - delta,
            lat - delta,
            lon + delta,
            lat + delta,
        ].map((value) => value.toFixed(5));
        const bbox = bboxCoords.join(',');
        const marker = `${lat.toFixed(5)},${lon.toFixed(5)}`;
        const embedSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${encodeURIComponent(marker)}`;
        const mapHref = `https://www.openstreetmap.org/?mlat=${lat.toFixed(5)}&mlon=${lon.toFixed(5)}#map=16/${lat.toFixed(5)}/${lon.toFixed(5)}`;
        const timestampLabel = location.timestamp ? formatDateTime(location.timestamp) : null;
        const accuracyLabel = Number.isFinite(location.accuracyMeters) ? `±${location.accuracyMeters.toFixed(1)} m` : null;
        return `
            <div class="profile-map">
                <iframe src="${escapeHtml(embedSrc)}" title="Mapa de ubicación" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
                <div class="profile-map__meta">
                    ${timestampLabel ? `<span>${escapeHtml(timestampLabel)}</span>` : ""}
                    ${location.source ? `<span>Fuente: ${escapeHtml(location.source)}</span>` : ""}
                    ${accuracyLabel ? `<span>Precisión: ${escapeHtml(accuracyLabel)}</span>` : ""}
                    <a href="${escapeHtml(mapHref)}" target="_blank" rel="noopener" class="profile-map__link">Abrir en OpenStreetMap</a>
                </div>
            </div>
        `.trim();
    };

    const renderLocationHistoryTable = (locations) => {
        if (!hasItems(locations)) {
            return '<p class="muted">No hay ubicaciones anteriores registradas.</p>';
        }
        const rows = locations
            .slice(0, 10)
            .map((location) => {
                const timestampLabel = location.timestamp ? formatDateTime(location.timestamp) : 'Sin registro';
                const accuracyLabel = Number.isFinite(location.accuracyMeters) ? `${location.accuracyMeters.toFixed(1)} m` : 'N/D';
                return `
                    <tr>
                        <td>${escapeHtml(timestampLabel)}</td>
                        <td>${escapeHtml(formatCoordinate(location.latitude))}, ${escapeHtml(formatCoordinate(location.longitude))}</td>
                        <td>${escapeHtml(location.source || 'Sin fuente')}</td>
                        <td>${escapeHtml(accuracyLabel)}</td>
                    </tr>
                `.trim();
            })
            .join("");
        return `
            <div class="table-wrapper profile-table-wrapper">
                <table class="profile-table">
                    <thead>
                        <tr>
                            <th>Registrado</th>
                            <th>Coordenadas</th>
                            <th>Fuente</th>
                            <th>Precisión</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `.trim();
    };

    const renderVitalSignsCharts = (patientId, devices = []) => {
        console.log('🎨 renderVitalSignsCharts llamado:', { patientId, deviceCount: devices.length });
        
        if (!hasItems(devices)) {
            console.log('⚠️ No hay dispositivos disponibles');
            return `
                <div class="vital-signs-placeholder">
                    <p class="muted">📊 No hay dispositivos con datos de signos vitales disponibles</p>
                </div>
            `.trim();
        }

        // ID único para el contenedor
        const containerId = `vital-signs-${patientId}`;
        const deviceSelectId = `device-select-${patientId}`;
        
        console.log('✅ Generando contenedor de signos vitales:', containerId);
        
        // Si solo hay un dispositivo, lo mostramos directamente
        const deviceOptions = devices
            .map((device, idx) => {
                const label = device.deviceTypeLabel || device.serial || `Dispositivo ${idx + 1}`;
                return `<option value="${escapeHtml(device.id)}">${escapeHtml(label)} (${escapeHtml(device.serial || 'S/N')})</option>`;
            })
            .join('');

        const selectorHtml = devices.length > 1
            ? `
                <div class="vital-signs-selector">
                    <label for="${deviceSelectId}">Seleccionar dispositivo:</label>
                    <select id="${deviceSelectId}" class="form-select">
                        ${deviceOptions}
                    </select>
                </div>
            `
            : '';

        return `
            <div class="vital-signs-container" id="${containerId}">
                ${selectorHtml}
                <div class="vital-signs-charts" id="${containerId}-charts">
                    <div class="vital-signs-loading">
                        <p>⏳ Cargando datos de signos vitales...</p>
                    </div>
                </div>
                <div class="vital-signs-update-indicator" style="text-align: center; padding: 0.5rem; font-size: 0.75rem; color: #10b981;">
                    <span class="pulse-dot" style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 6px; animation: pulse 2s infinite;"></span>
                    Actualización en tiempo real activa
                </div>
            </div>
        `.trim();
    };

    // Objeto global para almacenar las instancias de gráficas y timers
    const vitalSignsState = {
        charts: new Map(),
        timers: new Map(),
        isUpdating: new Map() // Para evitar peticiones simultáneas
    };

    const loadVitalSignsData = async (patientId, deviceId, containerId, isUpdate = false) => {
        const chartsContainer = document.querySelector(`#${containerId}-charts`);
        if (!chartsContainer) {
            console.error('❌ No se encontró el contenedor de gráficas:', `${containerId}-charts`);
            return;
        }

        // Evitar peticiones simultáneas
        const updateKey = `${patientId}-${deviceId}`;
        if (isUpdate && vitalSignsState.isUpdating.get(updateKey)) {
            return; // Ya hay una actualización en curso
        }

        try {
            if (isUpdate) {
                vitalSignsState.isUpdating.set(updateKey, true);
            }
            
            if (!isUpdate) {
                console.log('🔍 Iniciando carga de signos vitales:', { patientId, deviceId, containerId });
                chartsContainer.innerHTML = '<div class="vital-signs-loading"><p>⏳ Cargando datos...</p></div>';
            }
            
            const response = await Api.admin.getPatientVitalSigns(state.token, patientId, deviceId, 100);
            
            console.log('📊 Respuesta completa de signos vitales:', {
                response,
                patientId: response?.patient_id,
                deviceId: response?.device_id,
                measurement: response?.measurement,
                readingsCount: response?.readings?.length,
                readings: response?.readings
            });
            
            if (!response) {
                console.error('❌ Response es null o undefined');
                chartsContainer.innerHTML = '<p class="form-error">❌ Error: No se recibió respuesta del servidor</p>';
                return;
            }
            
            if (!response.readings) {
                console.warn('⚠️ No hay propiedad "readings" en la respuesta');
                chartsContainer.innerHTML = '<p class="muted">📊 No hay estructura de lecturas en la respuesta</p>';
                return;
            }
            
            if (response.readings.length === 0) {
                console.warn('⚠️ Array de readings está vacío');
                chartsContainer.innerHTML = '<p class="muted">📊 No hay lecturas recientes de signos vitales</p>';
                return;
            }

            const readings = response.readings;
            console.log('✅ Procesando', readings.length, 'lecturas');
            console.log('📝 Primera lectura:', readings[0]);
            console.log('📝 Última lectura:', readings[readings.length - 1]);
            
            // Procesar datos por tipo de signo vital
            const vitalSignsData = {
                heart_rate: { labels: [], values: [], unit: 'bpm', color: '#ef4444', label: 'Frecuencia Cardíaca' },
                spo2: { labels: [], values: [], unit: '%', color: '#3b82f6', label: 'SpO₂' },
                temperature: { labels: [], values: [], unit: '°C', color: '#f97316', label: 'Temperatura' },
                systolic_bp: { labels: [], values: [], unit: 'mmHg', color: '#8b5cf6', label: 'Presión Sistólica' },
                diastolic_bp: { labels: [], values: [], unit: 'mmHg', color: '#6366f1', label: 'Presión Diastólica' },
                respiratory_rate: { labels: [], values: [], unit: 'rpm', color: '#10b981', label: 'Frecuencia Respiratoria' },
            };

            // Extraer datos de las lecturas
            readings.forEach((reading, idx) => {
                // El timestamp puede venir como 'time', '_time' o 'timestamp'
                const timestamp = new Date(reading.timestamp || reading.time || reading._time);
                const timeLabel = timestamp.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
                
                if (idx === 0) {
                    console.log('🔬 Analizando primera lectura:', {
                        timestamp,
                        timeLabel,
                        keys: Object.keys(reading),
                        reading
                    });
                }
                
                Object.keys(vitalSignsData).forEach(key => {
                    if (reading[key] !== undefined && reading[key] !== null) {
                        vitalSignsData[key].labels.push(timeLabel);
                        vitalSignsData[key].values.push(Number(reading[key]));
                        
                        if (idx === 0) {
                            console.log(`   ✅ ${key}: ${reading[key]}`);
                        }
                    }
                });
            });
            
            // Log de datos procesados
            Object.entries(vitalSignsData).forEach(([key, data]) => {
                if (data.values.length > 0) {
                    console.log(`📈 ${data.label}: ${data.values.length} puntos de datos`);
                }
            });

            // Renderizar gráficas solo para signos vitales con datos
            const chartsHtml = Object.entries(vitalSignsData)
                .filter(([_, data]) => data.values.length > 0)
                .map(([key, data]) => {
                    const canvasId = `chart-${patientId}-${deviceId}-${key}`;
                    const statsId = `stats-${patientId}-${deviceId}-${key}`;
                    const avgValue = (data.values.reduce((a, b) => a + b, 0) / data.values.length).toFixed(1);
                    const minValue = Math.min(...data.values).toFixed(1);
                    const maxValue = Math.max(...data.values).toFixed(1);
                    const latestValue = data.values[data.values.length - 1].toFixed(1);
                    
                    return `
                        <div class="vital-sign-card">
                            <div class="vital-sign-header">
                                <h5>${data.label}</h5>
                                <div class="vital-sign-stats" id="${statsId}">
                                    <span class="vital-sign-current" style="color: ${data.color}; font-weight: bold; font-size: 1.2em;">
                                        ${latestValue} ${data.unit}
                                    </span>
                                    <span class="vital-sign-range" style="font-size: 0.85em; color: #6b7280;">
                                        Min: ${minValue} | Max: ${maxValue} | Prom: ${avgValue}
                                    </span>
                                </div>
                            </div>
                            <div class="vital-sign-chart-wrapper">
                                <canvas id="${canvasId}"></canvas>
                            </div>
                        </div>
                    `;
                })
                .join('');

            if (!chartsHtml) {
                console.warn('⚠️ No se generó HTML para las gráficas (no hay datos)');
                chartsContainer.innerHTML = '<p class="muted">📊 No hay datos de signos vitales para mostrar</p>';
                return;
            }
            
            if (!isUpdate) {
                console.log('✅ Renderizando gráficas HTML');
                chartsContainer.innerHTML = `<div class="vital-signs-grid">${chartsHtml}</div>`;
            }

            // Crear o actualizar gráficas con Chart.js
            if (!isUpdate) {
                console.log('🎨 Iniciando creación de gráficas con Chart.js');
            }
            
            Object.entries(vitalSignsData)
                .filter(([_, data]) => data.values.length > 0)
                .forEach(([key, data]) => {
                    const canvasId = `chart-${patientId}-${deviceId}-${key}`;
                    const chartKey = `${patientId}-${deviceId}-${key}`;
                    const statsId = `stats-${patientId}-${deviceId}-${key}`;
                    
                    if (!isUpdate) {
                        console.log(`   🖼️ Creando gráfica: ${canvasId}`);
                    }
                    
                    const canvas = document.getElementById(canvasId);
                    if (!canvas) {
                        if (!isUpdate) console.error(`   ❌ No se encontró canvas: ${canvasId}`);
                        return;
                    }

                    if (typeof Chart === 'undefined') {
                        console.error('   ❌ Chart.js no está cargado');
                        chartsContainer.innerHTML = '<p class="form-error">❌ Error: Chart.js no está disponible. Recarga la página.</p>';
                        return;
                    }
                    
                    // Calcular estadísticas
                    const avgValue = (data.values.reduce((a, b) => a + b, 0) / data.values.length).toFixed(1);
                    const minValue = Math.min(...data.values).toFixed(1);
                    const maxValue = Math.max(...data.values).toFixed(1);
                    const latestValue = data.values[data.values.length - 1].toFixed(1);
                    
                    // Actualizar estadísticas en el DOM
                    const statsElement = document.getElementById(statsId);
                    if (statsElement) {
                        statsElement.innerHTML = `
                            <span class="vital-sign-current" style="color: ${data.color}; font-weight: bold; font-size: 1.2em;">
                                ${latestValue} ${data.unit}
                            </span>
                            <span class="vital-sign-range" style="font-size: 0.85em; color: #6b7280;">
                                Min: ${minValue} | Max: ${maxValue} | Prom: ${avgValue}
                            </span>
                        `;
                    }
                    
                    // Actualizar gráfica existente o crear nueva
                    if (isUpdate && vitalSignsState.charts.has(chartKey)) {
                        const chart = vitalSignsState.charts.get(chartKey);
                        chart.data.labels = data.labels;
                        chart.data.datasets[0].data = data.values;
                        chart.update('none'); // Actualización sin animación para ser más fluido
                    } else {
                        if (!isUpdate) console.log(`   ✅ Renderizando ${data.label} con ${data.values.length} puntos`);
                        
                        const chart = new Chart(canvas, {
                            type: 'line',
                            data: {
                                labels: data.labels,
                                datasets: [{
                                    label: `${data.label} (${data.unit})`,
                                    data: data.values,
                                    borderColor: data.color,
                                    backgroundColor: data.color + '15',
                                    borderWidth: 3,
                                    fill: true,
                                    tension: 0.4,
                                    pointRadius: 0,
                                    pointHoverRadius: 6,
                                    pointHoverBackgroundColor: data.color,
                                    pointHoverBorderColor: '#fff',
                                    pointHoverBorderWidth: 2,
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                animation: {
                                    duration: 0
                                },
                                plugins: {
                                    legend: {
                                        display: false
                                    },
                                    tooltip: {
                                        mode: 'index',
                                        intersect: false,
                                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                        padding: 12,
                                        cornerRadius: 8,
                                        titleFont: {
                                            size: 13,
                                            weight: '600'
                                        },
                                        bodyFont: {
                                            size: 14,
                                            weight: '700'
                                        },
                                        displayColors: false,
                                        callbacks: {
                                            label: function(context) {
                                                return `${context.parsed.y} ${data.unit}`;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    x: {
                                        ticks: { 
                                            color: '#6b7280',
                                            font: {
                                                size: 11
                                            },
                                            maxRotation: 0,
                                            minRotation: 0,
                                            maxTicksLimit: 8
                                        },
                                        grid: {
                                            display: false
                                        }
                                    },
                                    y: {
                                        ticks: { 
                                            color: '#6b7280',
                                            font: {
                                                size: 11,
                                                weight: '600'
                                            },
                                            padding: 8
                                        },
                                        beginAtZero: false,
                                        grid: {
                                            color: 'rgba(15, 23, 42, 0.05)',
                                            lineWidth: 1
                                        }
                                    }
                                },
                                interaction: {
                                    mode: 'index',
                                    intersect: false
                                }
                            }
                        });
                        
                        vitalSignsState.charts.set(chartKey, chart);
                    }
                });
            
            // Configurar actualización automática cada segundo (solo en la primera carga)
            if (!isUpdate) {
                // Limpiar timer anterior si existe
                const timerKey = `${patientId}-${deviceId}`;
                if (vitalSignsState.timers.has(timerKey)) {
                    clearInterval(vitalSignsState.timers.get(timerKey));
                }
                
                // Crear nuevo timer para actualización automática - EXACTAMENTE CADA 1 SEGUNDO
                const timer = setInterval(() => {
                    loadVitalSignsData(patientId, deviceId, containerId, true);
                }, 1000); // 1000ms = 1 segundo
                
                vitalSignsState.timers.set(timerKey, timer);
                console.log('⏰ Actualización automática activada (cada 1 segundo exacto)');
            }
            
            // Liberar bandera de actualización
            if (isUpdate) {
                vitalSignsState.isUpdating.set(updateKey, false);
            }

        } catch (error) {
            console.error('❌ Error crítico cargando signos vitales:', error);
            console.error('   Stack:', error.stack);
            console.error('   Tipo:', error.constructor.name);
            console.error('   Status:', error.status);
            
            // Liberar bandera de actualización en caso de error
            if (isUpdate) {
                vitalSignsState.isUpdating.set(updateKey, false);
            }
            
            if (!isUpdate) {
                chartsContainer.innerHTML = `
                    <div class="vital-signs-error">
                        <p class="form-error">❌ Error al cargar los datos de signos vitales</p>
                        <p class="muted">Error: ${escapeHtml(error.message || 'Error desconocido')}</p>
                        ${error.status ? `<p class="muted">Status HTTP: ${error.status}</p>` : ''}
                        <p class="muted" style="font-size: 0.8em; margin-top: 10px;">
                            💡 Abre la consola del navegador (F12) para más detalles
                        </p>
                    </div>
                `;
            }
        }
    };

    const renderPatientProfileView = (profile) => {
        if (!profile || !profile.patient) {
            return '<p class="form-error">No se encontró la información del paciente.</p>';
        }
        const {
            patient,
            caregivers = [],
            careTeams = [],
            devices = [],
            groundTruthLabels = [],
            alerts = [],
            locations = {},
        } = profile;

        const patientName = patient.name || 'Paciente sin nombre';
        const email = patient.email || 'Sin correo registrado';
        const birthdateLabel = patient.birthdate ? formatDate(patient.birthdate) : 'No especificado';
        const createdLabel = patient.createdAt ? formatDateTime(patient.createdAt) : 'No especificado';
        const latestLocation = locations.latest || null;
        const locationHistory = hasItems(locations.recent) ? locations.recent : [];

        const caregiversHtml = renderListOrEmpty(
            caregivers,
            (item) => {
                const relation = item.relationshipLabel || item.relationshipCode || 'Sin relación definida';
                const startLabel = item.startedAt ? formatDate(item.startedAt) : 'No registrado';
                const endLabel = item.endedAt ? formatDate(item.endedAt) : null;
                const periodLabel = endLabel ? `${startLabel} – ${endLabel}` : startLabel;
                const note = item.note ? `<p class="profile-list__note">${escapeHtml(item.note)}</p>` : '';
                const badges = [];
                if (item.isPrimary) {
                    badges.push(buildStatusBadge('Principal', 'status-success'));
                }
                badges.push(`<span>${escapeHtml(item.caregiverEmail || 'Sin correo')}</span>`);
                badges.push(`<span>Vigencia: ${escapeHtml(periodLabel)}</span>`);
                if (item.careTeamName) {
                    badges.push(`<span class="profile-chip profile-chip--accent">${escapeHtml(item.careTeamName)}</span>`);
                }
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(item.caregiverName)}</div>
                        <div class="profile-list__subtitle">${escapeHtml(relation)}</div>
                        <div class="profile-list__meta">${badges.join("")}</div>
                        ${note}
                    </li>
                `;
            },
            'No hay cuidadores asignados a este paciente.'
        );

        const careTeamsHtml = renderListOrEmpty(
            careTeams,
            (team) => {
                const memberCount = hasItems(team.members) ? team.members.length : 0;
                let membersPreview = '';
                if (memberCount) {
                    const preview = team.members.map((member) => member.name).slice(0, 3);
                    const chips = preview.map((name) => `<span class="profile-chip">${escapeHtml(name)}</span>`);
                    const remaining = memberCount - preview.length;
                    if (remaining > 0) {
                        chips.push(`<span class="profile-chip profile-chip--muted">+${escapeHtml(String(remaining))}</span>`);
                    }
                    membersPreview = `<div class="profile-chips">${chips.join("")}</div>`;
                } else {
                    membersPreview = '<p class="muted">Sin miembros asignados</p>';
                }
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(team.name)}</div>
                        <div class="profile-list__meta">
                            <span>Miembros: ${escapeHtml(String(memberCount))}</span>
                            <span>ID: <code>${escapeHtml(team.id || '-')}</code></span>
                        </div>
                        ${membersPreview}
                    </li>
                `;
            },
            'El paciente no pertenece a equipos de cuidado.'
        );

        const devicesHtml = renderListOrEmpty(
            devices,
            (device) => {
                const typeLabel = device.deviceTypeLabel || device.deviceTypeCode || 'Sin tipo';
                const registeredLabel = device.registeredAt ? formatDateTime(device.registeredAt) : 'Sin registro';
                const status = device.active
                    ? buildStatusBadge('Activo', 'status-success')
                    : buildStatusBadge('Inactivo', 'status-muted');
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(typeLabel)}</div>
                        <div class="profile-list__meta">
                            <span>Serial: <code>${escapeHtml(device.serial || '-')}</code></span>
                            ${status}
                        </div>
                        <div class="profile-list__meta">
                            <span>Marca: ${escapeHtml(device.brand || '-')}</span>
                            <span>Modelo: ${escapeHtml(device.model || '-')}</span>
                            <span>Registrado: ${escapeHtml(registeredLabel)}</span>
                        </div>
                    </li>
                `;
            },
            'Este paciente no tiene dispositivos vinculados.'
        );

        const alertsHtml = renderListOrEmpty(
            alerts.slice(0, 6),
            (alert) => {
                const createdLabel = alert.createdAt ? formatDateTime(alert.createdAt) : 'Sin fecha';
                const levelBadge = buildAlertLevelBadge(alert.levelCode, alert.levelLabel);
                const statusBadge = buildStatusBadge(alert.statusDescription || alert.statusCode || 'Sin estado', 'status-muted');
                const description = alert.description || alert.typeDescription || alert.typeCode || 'Alerta sin descripción';
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(description)}</div>
                        <div class="profile-list__meta">
                            <span>${escapeHtml(createdLabel)}</span>
                            ${levelBadge}
                            ${statusBadge}
                        </div>
                    </li>
                `;
            },
            'No hay alertas recientes para este paciente.'
        );

        const groundTruthHtml = renderListOrEmpty(
            groundTruthLabels.slice(0, 6),
            (label) => {
                const eventLabel = label.eventTypeLabel || label.eventTypeCode || 'Evento sin etiqueta';
                const onsetLabel = label.onset ? formatDateTime(label.onset) : 'Sin inicio';
                const offsetLabel = label.offsetAt ? formatDateTime(label.offsetAt) : null;
                const author = label.annotatedByName || label.annotatedByUserId || 'Sin autor';
                const source = label.source || 'Sin fuente';
                const note = label.note ? `<p class="profile-list__note">${escapeHtml(label.note)}</p>` : '';
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(eventLabel)}</div>
                        <div class="profile-list__meta">
                            <span>Inicio: ${escapeHtml(onsetLabel)}</span>
                            ${offsetLabel ? `<span>Fin: ${escapeHtml(offsetLabel)}</span>` : ''}
                            <span>Fuente: ${escapeHtml(source)}</span>
                        </div>
                        <div class="profile-list__subtitle">Anotado por ${escapeHtml(author)}</div>
                        ${note}
                    </li>
                `;
            },
            'Sin etiquetas recientes registradas.'
        );

        const statsHtml = renderProfileStats([
            { label: 'Cuidadores', value: caregivers.length },
            { label: 'Equipos', value: careTeams.length },
            { label: 'Dispositivos', value: devices.length },
            { label: 'Alertas', value: alerts.length },
        ]);

        const detailRows = [
            { label: 'Correo', value: email },
            { label: 'Fecha de nacimiento', value: birthdateLabel },
            { label: 'Registrado', value: createdLabel },
        ];
        if (patient.id) {
            detailRows.push({ label: 'ID', value: `<code>${escapeHtml(patient.id)}</code>`, html: true });
        }
        const detailList = buildDetailList(detailRows);
        const riskBadge = buildRiskBadge(patient.riskLevelCode, patient.riskLevelLabel);
        const heroMeta = riskBadge ? `<div class="profile-hero__meta">${riskBadge}</div>` : '';
        const heroAvatar = `<span>${escapeHtml((patientName.charAt(0) || '?').toUpperCase())}</span>`;

        return `
            <div class="profile-modal">
                <section class="profile-hero">
                    <div class="profile-hero__avatar">${heroAvatar}</div>
                    <div class="profile-hero__info">
                        <h2 class="profile-hero__title">${escapeHtml(patientName)}</h2>
                        ${heroMeta}
                        ${detailList}
                    </div>
                </section>
                ${statsHtml}
                <section class="profile-section">
                    <h4>📊 Signos Vitales en Tiempo Real</h4>
                    ${renderVitalSignsCharts(patient.id, devices)}
                </section>
                <section class="profile-section">
                    <h4>Ubicación reciente</h4>
                    ${buildMapSection(latestLocation)}
                </section>
                <div class="profile-grid">
                    <section class="profile-section">
                        <h4>Cuidadores asignados</h4>
                        ${caregiversHtml}
                    </section>
                    <section class="profile-section">
                        <h4>Equipos de cuidado</h4>
                        ${careTeamsHtml}
                    </section>
                    <section class="profile-section">
                        <h4>Dispositivos vinculados</h4>
                        ${devicesHtml}
                    </section>
                </div>
                <div class="profile-grid">
                    <section class="profile-section">
                        <h4>Alertas recientes</h4>
                        ${alertsHtml}
                    </section>
                    <section class="profile-section">
                        <h4>Ground truth reciente</h4>
                        ${groundTruthHtml}
                    </section>
                </div>
                <section class="profile-section">
                    <h4>Historial de ubicaciones</h4>
                    ${renderLocationHistoryTable(locationHistory)}
                </section>
            </div>
        `.trim();
    };

    const renderStaffProfileView = (profile) => {
        if (!profile || !profile.member) {
            return '<p class="form-error">No se encontró la información del miembro del staff.</p>';
        }
        const {
            member,
            careTeams = [],
            caregiverAssignments = [],
            groundTruthAnnotations = [],
            pushDevices = [],
        } = profile;

        const name = member.name || 'Miembro sin nombre';
        const email = member.email || 'Sin correo';
        const joinedLabel = member.joinedAt ? formatDate(member.joinedAt) : 'No especificado';
        const updatedLabel = member.updatedAt ? formatDateTime(member.updatedAt) : null;
        const roleLabel = member.roleLabel || member.roleCode || 'Sin rol asignado';

        const avatarContent = member.profilePhotoUrl
            ? `<img src="${escapeHtml(member.profilePhotoUrl)}" alt="${escapeHtml(name)}">`
            : `<span>${escapeHtml((name.charAt(0) || '?').toUpperCase())}</span>`;

        const detailRows = [
            { label: 'Correo', value: email },
            { label: 'Fecha de ingreso', value: joinedLabel },
        ];
        if (updatedLabel) {
            detailRows.push({ label: 'Actualizado', value: updatedLabel });
        }
        detailRows.push({ label: 'ID', value: `<code>${escapeHtml(member.userId || '-')}</code>`, html: true });
        const detailList = buildDetailList(detailRows);
        const roleBadge = buildStatusBadge(roleLabel, 'info');

        const careTeamsHtml = renderListOrEmpty(
            careTeams,
            (team) => {
                const joined = team.joinedAt ? formatDate(team.joinedAt) : 'Sin registro';
                const patientsCount = hasItems(team.patients) ? team.patients.length : 0;
                let patientsPreview = '';
                if (patientsCount) {
                    const preview = team.patients.map((patientItem) => patientItem.name).slice(0, 3);
                    const chips = preview.map((item) => `<span class="profile-chip profile-chip--patient">${escapeHtml(item)}</span>`);
                    const remaining = patientsCount - preview.length;
                    if (remaining > 0) {
                        chips.push(`<span class="profile-chip profile-chip--muted">+${escapeHtml(String(remaining))}</span>`);
                    }
                    patientsPreview = `<div class="profile-chips">${chips.join("")}</div>`;
                } else {
                    patientsPreview = '<p class="muted">Sin pacientes asignados</p>';
                }
                const roleInfo = team.roleLabel || team.roleCode ? `<span>${escapeHtml(team.roleLabel || team.roleCode)}</span>` : '';
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(team.name)}</div>
                        <div class="profile-list__meta">
                            ${roleInfo}
                            <span>Miembro desde: ${escapeHtml(joined)}</span>
                        </div>
                        ${patientsPreview}
                    </li>
                `;
            },
            'Este usuario no pertenece a equipos de cuidado.'
        );

        const caregiverAssignmentsHtml = renderListOrEmpty(
            caregiverAssignments,
            (assignment) => {
                const relation = assignment.relationshipLabel || assignment.relationshipCode || 'Sin relación definida';
                const startLabel = assignment.startedAt ? formatDate(assignment.startedAt) : 'No registrado';
                const endLabel = assignment.endedAt ? formatDate(assignment.endedAt) : null;
                const periodLabel = endLabel ? `${startLabel} – ${endLabel}` : startLabel;
                const note = assignment.note ? `<p class="profile-list__note">${escapeHtml(assignment.note)}</p>` : '';
                const badges = [];
                if (assignment.isPrimary) {
                    badges.push(buildStatusBadge('Principal', 'status-success'));
                }
                if (assignment.careTeamName) {
                    badges.push(`<span class="profile-chip profile-chip--accent">${escapeHtml(assignment.careTeamName)}</span>`);
                }
                badges.push(`<span>Paciente: ${escapeHtml(assignment.patientName || assignment.patientEmail || '-')}</span>`);
                badges.push(`<span>Vigencia: ${escapeHtml(periodLabel)}</span>`);
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(relation)}</div>
                        <div class="profile-list__meta">${badges.join("")}</div>
                        ${note}
                    </li>
                `;
            },
            'Este miembro no tiene asignaciones activas como cuidador.'
        );

        const groundTruthHtml = renderListOrEmpty(
            groundTruthAnnotations.slice(0, 6),
            (label) => {
                const eventLabel = label.eventTypeLabel || label.eventTypeCode || 'Evento sin etiqueta';
                const onsetLabel = label.onset ? formatDateTime(label.onset) : 'Sin inicio';
                const offsetLabel = label.offsetAt ? formatDateTime(label.offsetAt) : null;
                const patientInfo = label.patientId ? `Paciente: ${label.patientId}` : 'Paciente no disponible';
                const note = label.note ? `<p class="profile-list__note">${escapeHtml(label.note)}</p>` : '';
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(eventLabel)}</div>
                        <div class="profile-list__meta">
                            <span>Inicio: ${escapeHtml(onsetLabel)}</span>
                            ${offsetLabel ? `<span>Fin: ${escapeHtml(offsetLabel)}</span>` : ''}
                            <span>${escapeHtml(patientInfo)}</span>
                        </div>
                        ${note}
                    </li>
                `;
            },
            'Sin anotaciones recientes registradas por este usuario.'
        );

        const pushDevicesHtml = renderListOrEmpty(
            pushDevices,
            (device) => {
                const platformLabel = device.platformLabel || device.platformCode || 'Sin plataforma';
                const tokenPreview = truncate(device.pushToken, 28);
                const lastSeenLabel = device.lastSeenAt ? formatDateTime(device.lastSeenAt) : 'Sin uso reciente';
                const status = device.active
                    ? buildStatusBadge('Activo', 'status-success')
                    : buildStatusBadge('Inactivo', 'status-muted');
                return `
                    <li class="profile-list__item">
                        <div class="profile-list__title">${escapeHtml(platformLabel)}</div>
                        <div class="profile-list__meta">
                            ${status}
                            <span>Token: <code>${escapeHtml(tokenPreview)}</code></span>
                        </div>
                        <div class="profile-list__meta">
                            <span>${escapeHtml(lastSeenLabel)}</span>
                        </div>
                    </li>
                `;
            },
            'Sin dispositivos push registrados.'
        );

        const statsHtml = renderProfileStats([
            { label: 'Equipos', value: careTeams.length },
            { label: 'Asignaciones de cuidador', value: caregiverAssignments.length },
            { label: 'Etiquetas ground truth', value: groundTruthAnnotations.length },
            { label: 'Push devices', value: pushDevices.length },
        ]);

        return `
            <div class="profile-modal">
                <section class="profile-hero profile-hero--staff">
                    <div class="profile-hero__avatar">${avatarContent}</div>
                    <div class="profile-hero__info">
                        <h2 class="profile-hero__title">${escapeHtml(name)}</h2>
                        <div class="profile-hero__meta">${roleBadge}</div>
                        ${detailList}
                    </div>
                </section>
                ${statsHtml}
                <div class="profile-grid">
                    <section class="profile-section">
                        <h4>Equipos de cuidado</h4>
                        ${careTeamsHtml}
                    </section>
                    <section class="profile-section">
                        <h4>Asignaciones como cuidador</h4>
                        ${caregiverAssignmentsHtml}
                    </section>
                </div>
                <div class="profile-grid">
                    <section class="profile-section">
                        <h4>Ground truth reciente</h4>
                        ${groundTruthHtml}
                    </section>
                    <section class="profile-section">
                        <h4>Push devices registrados</h4>
                        ${pushDevicesHtml}
                    </section>
                </div>
            </div>
        `.trim();
    };

    const viewPatientProfile = async (patientId) => {
        if (!state.selectedOrgId) {
            showToast('Selecciona una organización para consultar perfiles.', 'warning');
            return;
        }
        if (!patientId) {
            showToast('Paciente no válido.', 'warning');
            return;
        }
        openModal({
            title: 'Perfil del paciente',
            size: 'wide',
            body: '<div class="loader"><span class="spinner"></span>Cargando perfil...</div>',
        });
        try {
            const profile = await Api.admin.getPatientProfile(state.token, state.selectedOrgId, patientId);
            if (!profile) {
                setModalBody('<p class="muted">No se encontró el paciente solicitado.</p>');
                return;
            }
            const title = profile.patient?.name ? `👤 ${profile.patient.name}` : 'Perfil del paciente';
            setModalTitle(title);
            setModalBody(renderPatientProfileView(profile));
            
            // Inicializar signos vitales si hay dispositivos
            console.log('🔍 Verificando dispositivos en perfil:', profile.devices?.length);
            if (profile.devices && profile.devices.length > 0) {
                const containerId = `vital-signs-${profile.patient.id}`;
                const deviceSelectId = `device-select-${profile.patient.id}`;
                const firstDeviceId = profile.devices[0].id;
                
                console.log('🚀 Iniciando carga de signos vitales para dispositivo:', firstDeviceId);
                
                // Cargar datos del primer dispositivo
                setTimeout(() => {
                    console.log('⏰ Ejecutando loadVitalSignsData...');
                    loadVitalSignsData(profile.patient.id, firstDeviceId, containerId);
                }, 100);
                
                // Si hay selector de dispositivos, agregar evento de cambio
                if (profile.devices.length > 1) {
                    setTimeout(() => {
                        const deviceSelect = document.getElementById(deviceSelectId);
                        if (deviceSelect) {
                            deviceSelect.addEventListener('change', (e) => {
                                const selectedDeviceId = e.target.value;
                                loadVitalSignsData(profile.patient.id, selectedDeviceId, containerId);
                            });
                        }
                    }, 100);
                }
            }
        } catch (error) {
            handleApiError(error);
            if (error?.status === 401 || error?.status === 403) {
                closeModal();
                return;
            }
            setModalBody(`<p class="form-error">${escapeHtml(error.message || 'No se pudo cargar el perfil del paciente')}</p>`);
        }
    };

    const viewStaffProfile = async (userId) => {
        if (!state.selectedOrgId) {
            showToast('Selecciona una organización para consultar perfiles.', 'warning');
            return;
        }
        if (!userId) {
            showToast('Miembro no válido.', 'warning');
            return;
        }
        openModal({
            title: 'Perfil del staff',
            size: 'wide',
            body: '<div class="loader"><span class="spinner"></span>Cargando perfil...</div>',
        });
        try {
            const profile = await Api.admin.getStaffProfile(state.token, state.selectedOrgId, userId);
            if (!profile) {
                setModalBody('<p class="muted">No se encontró el miembro solicitado.</p>');
                return;
            }
            const title = profile.member?.name ? `👥 ${profile.member.name}` : 'Perfil del staff';
            setModalTitle(title);
            setModalBody(renderStaffProfileView(profile));
        } catch (error) {
            handleApiError(error);
            if (error?.status === 401 || error?.status === 403) {
                closeModal();
                return;
            }
            setModalBody(`<p class="form-error">${escapeHtml(error.message || 'No se pudo cargar el perfil del staff')}</p>`);
        }
    };

    const tabRenderers = {
        staff: renderStaff,
        patients: renderPatients,
        "care-teams": renderCareTeams,
        caregivers: renderCaregivers,
        alerts: renderAlerts,
        "ground-truth": renderGroundTruth,
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

        if (tabName === "ground-truth") {
            await ensureGroundTruthSupportData();
            populateGroundTruthPatientFilter();

            const selectValue = el.groundTruthPatientFilter ? el.groundTruthPatientFilter.value : "";
            if (!state.groundTruthSelectedPatientId && selectValue) {
                state.groundTruthSelectedPatientId = selectValue;
            } else if (!state.groundTruthSelectedPatientId && state.availablePatients.length) {
                state.groundTruthSelectedPatientId = state.availablePatients[0].id;
                if (el.groundTruthPatientFilter) {
                    el.groundTruthPatientFilter.value = state.groundTruthSelectedPatientId;
                }
            }

            const activePatientId = state.groundTruthSelectedPatientId || selectValue || "";
            const cached = state.tabCache.get("ground-truth");
            if (cached && cached.patientId === activePatientId) {
                renderGroundTruth(cached);
                return;
            }

            await loadGroundTruthLabels(activePatientId, { showLoading: true });
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
        state.availablePatients = [];
        state.availableStaff = [];
        state.groundTruthEventTypes = [];
        state.groundTruthSelectedPatientId = null;

        if (el.groundTruthPatientFilter) {
            el.groundTruthPatientFilter.value = "";
            el.groundTruthPatientFilter.disabled = true;
        }
        if (el.buttons.createGroundTruth) {
            el.buttons.createGroundTruth.disabled = true;
        }
        if (el.buttons.refreshGroundTruth) {
            el.buttons.refreshGroundTruth.disabled = true;
        }

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
                state.availablePatients = [];
                state.tabCache.delete('ground-truth');
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

        // Actualizar título e ID del equipo
        const titleEl = overlay.querySelector('#careTeamDetailTitle');
        const idEl = overlay.querySelector('#careTeamDetailId');
        if (titleEl) titleEl.textContent = `💼 ${detail.team.name}`;
        if (idEl) {
            const shortId = detail.team.id.split('-')[0];
            idEl.innerHTML = `ID: <code class="id-display">${escapeHtml(shortId)}...</code>`;
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

        const membersList = members.length
            ? `
                <div class="care-team-cards">
                    ${members.map((member) => `
                        <div class="care-team-card">
                            <div class="care-team-card__header">
                                <div class="care-team-card__avatar">${escapeHtml(member.name.charAt(0).toUpperCase())}</div>
                                <div class="care-team-card__info">
                                    <h5>${escapeHtml(member.name)}</h5>
                                    <p class="muted card-email">${escapeHtml(member.email)}</p>
                                </div>
                            </div>
                            <div class="care-team-card__body">
                                <div class="care-team-card__meta">
                                    <span class="status-badge info">${escapeHtml(member.roleLabel || member.roleCode)}</span>
                                </div>
                                <p class="care-team-card__date">Miembro desde ${escapeHtml(formatDate(member.joinedAt))}</p>
                            </div>
                            <div class="care-team-card__actions">
                                <button class="btn btn-sm btn-danger" onclick="window.app.removeCareTeamMember('${escapeHtml(team.id)}', '${escapeHtml(member.userId)}')">Quitar del equipo</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `
            : '<p class="muted">No hay miembros asignados a este equipo.</p>';

        const patientsList = patients.length
            ? `
                <div class="care-team-cards">
                    ${patients.map((patient) => `
                        <div class="care-team-card">
                            <div class="care-team-card__header">
                                <div class="care-team-card__avatar care-team-card__avatar--patient">${escapeHtml(patient.name.charAt(0).toUpperCase())}</div>
                                <div class="care-team-card__info">
                                    <h5>${escapeHtml(patient.name)}</h5>
                                    <p class="muted card-email">${escapeHtml(patient.email || 'Sin correo electrónico')}</p>
                                </div>
                            </div>
                            <div class="care-team-card__body">
                                <p class="care-team-card__date">Paciente del equipo</p>
                            </div>
                            <div class="care-team-card__actions">
                                <button class="btn btn-sm btn-danger" onclick="window.app.removeCareTeamPatient('${escapeHtml(team.id)}', '${escapeHtml(patient.patientId)}')">Quitar del equipo</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `
            : '<p class="muted">No hay pacientes asignados a este equipo.</p>';

        const memberForm = availableMemberOptions && roleOptions
            ? `
                <div class="care-team-add-form">
                    <h5>Agregar nuevo miembro</h5>
                    <form id="careTeamAddMemberForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="careTeamMemberSelect">Usuario</label>
                                <select id="careTeamMemberSelect" name="user_id" required>
                                    <option value="">-- Selecciona --</option>
                                    ${availableMemberOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="careTeamRoleSelect">Rol</label>
                                <select id="careTeamRoleSelect" name="role_id" required>
                                    <option value="">-- Selecciona --</option>
                                    ${roleOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label>&nbsp;</label>
                                <button type="submit" class="btn btn-primary">Agregar</button>
                            </div>
                        </div>
                        <div class="form-error hidden" id="careTeamMemberFormError"></div>
                    </form>
                </div>
            `
            : '<div class="care-team-add-form"><p class="muted">No hay usuarios disponibles para asignar.</p></div>';

        const patientForm = availablePatientOptions
            ? `
                <div class="care-team-add-form">
                    <h5>Agregar nuevo paciente</h5>
                    <form id="careTeamAddPatientForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="careTeamPatientSelect">Paciente</label>
                                <select id="careTeamPatientSelect" name="patient_id" required>
                                    <option value="">-- Selecciona --</option>
                                    ${availablePatientOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label>&nbsp;</label>
                                <button type="submit" class="btn btn-primary">Agregar</button>
                            </div>
                        </div>
                        <div class="form-error hidden" id="careTeamPatientFormError"></div>
                    </form>
                </div>
            `
            : '<div class="care-team-add-form"><p class="muted">No hay pacientes disponibles para asignar.</p></div>';

        contentEl.innerHTML = `
            <div class="care-team-detail">
                <section class="care-team-summary">
                    <div class="care-team-summary__header">
                        <h3>${escapeHtml(team.name)}</h3>
                        <div class="care-team-summary__stats">
                            <div class="stat-badge">
                                <span class="stat-badge__value">${members.length}</span>
                                <span class="stat-badge__label">Miembros</span>
                            </div>
                            <div class="stat-badge">
                                <span class="stat-badge__value">${patients.length}</span>
                                <span class="stat-badge__label">Pacientes</span>
                            </div>
                        </div>
                    </div>
                    <div class="care-team-summary__meta">
                        <p><strong>ID:</strong> <code>${escapeHtml(team.id)}</code></p>
                        <p><strong>Creado:</strong> ${escapeHtml(formatDate(team.createdAt))}</p>
                    </div>
                </section>

                <section class="care-team-section">
                    <div class="care-team-section__header">
                        <h4>👥 Miembros del equipo</h4>
                    </div>
                    ${membersList}
                    ${memberForm}
                </section>

                <section class="care-team-section">
                    <div class="care-team-section__header">
                        <h4>🏥 Pacientes asignados</h4>
                    </div>
                    ${patientsList}
                    ${patientForm}
                </section>
            </div>
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
                <div class="modal-content modal-xl">
                    <div class="modal-header">
                        <div>
                            <h3 id="careTeamDetailTitle">💼 Equipo de cuidado</h3>
                            <p class="muted" id="careTeamDetailId"></p>
                        </div>
                        <button class="modal-close" type="button" id="careTeamDetailCloseBtn">&times;</button>
                    </div>
                    <div class="modal-body" id="careTeamDetailContent">
                        <div class="loader"><span class="spinner"></span>Cargando equipo...</div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-ghost" id="careTeamDetailCloseFooter">Cerrar</button>
                        <button type="button" class="btn btn-danger" onclick="window.app.deleteCareTeam('${careTeamId}')">Eliminar equipo</button>
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

    // ============================================
    // Alert Functions
    // ============================================

    const showAlertModal = async (alertId = null) => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización para gestionar alertas", "warning");
            return;
        }

        const isEdit = !!alertId;
        const modalTitle = isEdit ? "Editar alerta" : "Nueva alerta";

        try {
            // Load support data from database
            const [patients, alertTypes, alertLevels, alertStatuses, currentAlert] = await Promise.all([
                Api.admin.listPatients(state.token, state.selectedOrgId),
                Api.admin.listAlertTypes(state.token, state.selectedOrgId),
                Api.admin.listAlertLevels(state.token, state.selectedOrgId),
                Api.admin.listAlertStatuses(state.token, state.selectedOrgId),
                isEdit ? Api.admin.getAlert(state.token, state.selectedOrgId, alertId) : Promise.resolve(null)
            ]);

            const patientOptions = patients
                .map(p => `<option value="${escapeHtml(p.id)}" ${p.id === currentAlert?.patientId ? 'selected' : ''}>${escapeHtml(p.name)} (${escapeHtml(p.email || 'Sin correo')})</option>`)
                .join('');

            const typeOptions = alertTypes
                .map(t => `<option value="${escapeHtml(t.code)}" ${t.code === currentAlert?.typeCode ? 'selected' : ''}>${escapeHtml(t.description)}</option>`)
                .join('');

            const levelOptions = alertLevels
                .map(l => `<option value="${escapeHtml(l.code)}" ${l.code === currentAlert?.levelCode ? 'selected' : ''}>${escapeHtml(l.label)}</option>`)
                .join('');

            const statusOptions = alertStatuses
                .map(s => `<option value="${escapeHtml(s.code)}" ${s.code === currentAlert?.statusCode ? 'selected' : ''}>${escapeHtml(s.description || s.code)}</option>`)
                .join('');

        const modalHtml = `
            <div class="modal-overlay" id="alertModal">
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <h3>🚨 ${modalTitle}</h3>
                        <button class="modal-close" type="button" onclick="document.getElementById('alertModal').remove()">&times;</button>
                    </div>
                    <form id="alertForm" class="modal-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="alertPatientId">Paciente *</label>
                                <select id="alertPatientId" name="patient_id" required ${isEdit ? 'disabled' : ''}>
                                    <option value="">-- Selecciona un paciente --</option>
                                    ${patientOptions}
                                </select>
                                ${isEdit ? `<input type="hidden" name="patient_id" value="${escapeHtml(currentAlert.patientId)}">` : ''}
                            </div>
                            <div class="form-group">
                                <label for="alertType">Tipo de alerta *</label>
                                <select id="alertType" name="alert_type_code" required>
                                    <option value="">-- Selecciona un tipo --</option>
                                    ${typeOptions}
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="alertLevel">Nivel de severidad *</label>
                                <select id="alertLevel" name="alert_level_code" required>
                                    <option value="">-- Selecciona un nivel --</option>
                                    ${levelOptions}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="alertStatus">Estado *</label>
                                <select id="alertStatus" name="status_code" required>
                                    <option value="">-- Selecciona un estado --</option>
                                    ${statusOptions}
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="alertDescription">Descripción</label>
                            <textarea id="alertDescription" name="description" rows="3" maxlength="500">${escapeHtml(currentAlert?.description || '')}</textarea>
                        </div>
                        <div class="form-error hidden" id="alertError"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('alertModal').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">${isEdit ? 'Actualizar' : 'Crear'}</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const form = document.getElementById('alertForm');
        const errorEl = document.getElementById('alertError');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(form);
            const payload = {
                patient_id: formData.get('patient_id'),
                alert_type_code: formData.get('alert_type_code'),
                alert_level_code: formData.get('alert_level_code'),
                status_code: formData.get('status_code'),
                description: formData.get('description') || null,
            };

            errorEl.classList.add('hidden');
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = isEdit ? 'Actualizando...' : 'Creando...';

            try {
                if (isEdit) {
                    await Api.admin.updateAlert(state.token, state.selectedOrgId, alertId, payload);
                    showToast('Alerta actualizada correctamente', 'success');
                } else {
                    await Api.admin.createAlert(state.token, state.selectedOrgId, payload);
                    showToast('Alerta creada correctamente', 'success');
                }
                document.getElementById('alertModal').remove();
                state.tabCache.delete('alerts');
                await activateTab('alerts');
            } catch (error) {
                errorEl.textContent = error.message || 'No se pudo guardar la alerta';
                errorEl.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? 'Actualizar' : 'Crear';
            }
        });
        } catch (error) {
            console.error('Error loading alert modal:', error);
            showToast(`Error al cargar el formulario: ${error.message}`, 'error');
        }
    };

    const showDeviceModal = async (deviceId = null) => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización para gestionar dispositivos", "warning");
            return;
        }

        const isEdit = !!deviceId;
        const modalTitle = isEdit ? "Editar dispositivo" : "Registrar dispositivo";

        try {
            const [deviceTypes, patients, currentDevice] = await Promise.all([
                Api.admin.listDeviceTypes(state.token, state.selectedOrgId),
                Api.admin.listPatients(state.token, state.selectedOrgId),
                isEdit ? Api.admin.getDevice(state.token, state.selectedOrgId, deviceId) : Promise.resolve(null)
            ]);

            if (isEdit && !currentDevice) {
                showToast("No se encontró el dispositivo seleccionado", "warning");
                return;
            }

            const allDeviceTypes = [...deviceTypes];
            if (currentDevice?.deviceTypeCode && !allDeviceTypes.some((type) => type.code === currentDevice.deviceTypeCode)) {
                allDeviceTypes.push({
                    code: currentDevice.deviceTypeCode,
                    label: currentDevice.deviceTypeLabel || currentDevice.deviceTypeCode,
                });
            }

            if (!allDeviceTypes.length) {
                showToast("No hay tipos de dispositivo configurados. Crea al menos uno antes de continuar.", "warning");
                return;
            }

            const typeOptions = allDeviceTypes
                .map((type) => `<option value="${escapeHtml(type.code)}" ${type.code === currentDevice?.deviceTypeCode ? "selected" : ""}>${escapeHtml(type.label || type.code)}</option>`)
                .join("");

            const patientOptions = patients
                .map((patient) => `<option value="${escapeHtml(patient.id)}" ${patient.id === currentDevice?.ownerPatientId ? "selected" : ""}>${escapeHtml(patient.name)} (${escapeHtml(patient.email || "Sin correo")})</option>`)
                .join("");

            const modalHtml = `
            <div class="modal-overlay" id="deviceModal">
                <div class="modal-content modal-md">
                    <div class="modal-header">
                        <h3>🔧 ${modalTitle}</h3>
                        <button class="modal-close" type="button" onclick="document.getElementById('deviceModal').remove()">&times;</button>
                    </div>
                    <form id="deviceForm" class="modal-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="deviceSerial">Número de serie *</label>
                                <input id="deviceSerial" name="serial" type="text" required maxlength="80" value="${escapeHtml(currentDevice?.serial || "")}">
                            </div>
                            <div class="form-group">
                                <label for="deviceType">Tipo de dispositivo *</label>
                                <select id="deviceType" name="device_type_code" required>
                                    <option value="">-- Selecciona un tipo --</option>
                                    ${typeOptions}
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="deviceBrand">Marca</label>
                                <input id="deviceBrand" name="brand" type="text" maxlength="80" value="${escapeHtml(currentDevice?.brand || "")}">
                            </div>
                            <div class="form-group">
                                <label for="deviceModel">Modelo</label>
                                <input id="deviceModel" name="model" type="text" maxlength="80" value="${escapeHtml(currentDevice?.model || "")}">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="deviceOwner">Paciente asignado</label>
                            <select id="deviceOwner" name="owner_patient_id">
                                <option value="">-- Sin asignar --</option>
                                ${patientOptions}
                            </select>
                        </div>
                        <div class="form-group form-check">
                            <label class="checkbox">
                                <input type="checkbox" id="deviceActive" name="active" ${currentDevice ? (currentDevice.active ? "checked" : "") : "checked"}>
                                <span>Dispositivo activo</span>
                            </label>
                        </div>
                        ${currentDevice?.registeredAt ? `<p class="text-muted">Registrado el ${escapeHtml(formatDateTime(currentDevice.registeredAt))}</p>` : ""}
                        <div class="form-error hidden" id="deviceError"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('deviceModal').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">${isEdit ? "Actualizar" : "Registrar"}</button>
                        </div>
                    </form>
                </div>
            </div>`;

            document.body.insertAdjacentHTML("beforeend", modalHtml);

            const modal = document.getElementById("deviceModal");
            const form = document.getElementById("deviceForm");
            const errorEl = document.getElementById("deviceError");

            modal.addEventListener("click", (event) => {
                if (event.target === modal) {
                    modal.remove();
                }
            });

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                errorEl.classList.add("hidden");
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = isEdit ? "Actualizando..." : "Registrando...";

                const serial = form.serial.value.trim();
                const deviceTypeCode = form.device_type_code.value.trim();
                const brand = form.brand.value.trim();
                const model = form.model.value.trim();
                const ownerPatientId = form.owner_patient_id.value.trim();
                const active = form.active.checked;

                const payload = {
                    serial,
                    device_type_code: deviceTypeCode,
                    brand: brand || null,
                    model: model || null,
                    owner_patient_id: ownerPatientId || null,
                    active,
                };

                try {
                    if (isEdit) {
                        await Api.admin.updateDevice(state.token, state.selectedOrgId, deviceId, payload);
                        showToast("Dispositivo actualizado correctamente", "success");
                    } else {
                        await Api.admin.createDevice(state.token, state.selectedOrgId, payload);
                        showToast("Dispositivo registrado correctamente", "success");
                    }
                    modal.remove();
                    state.tabCache.delete("devices");
                    await activateTab("devices");
                } catch (error) {
                    console.error("Error saving device:", error);
                    errorEl.textContent = error.message || "No se pudo guardar el dispositivo";
                    errorEl.classList.remove("hidden");
                    submitBtn.disabled = false;
                    submitBtn.textContent = isEdit ? "Actualizar" : "Registrar";
                }
            });
        } catch (error) {
            console.error("Error loading device modal:", error);
            showToast(`Error al cargar el formulario: ${error.message}`, "error");
        }
    };

    const ensureGroundTruthSupportData = async () => {
        if (!state.selectedOrgId) return;
        const tasks = [];

        if (!state.availablePatients.length) {
            tasks.push(
                Api.admin.listPatients(state.token, state.selectedOrgId)
                    .then((patients) => {
                        state.availablePatients = Array.isArray(patients) ? patients : [];
                    })
            );
        }

        if (!state.availableStaff.length) {
            tasks.push(
                Api.admin.listStaff(state.token, state.selectedOrgId)
                    .then((staff) => {
                        state.availableStaff = Array.isArray(staff) ? staff : [];
                    })
            );
        }

        if (!state.groundTruthEventTypes.length) {
            tasks.push(
                Api.admin.listGroundTruthEventTypes(state.token, state.selectedOrgId)
                    .then((eventTypes) => {
                        state.groundTruthEventTypes = Array.isArray(eventTypes) ? eventTypes : [];
                    })
            );
        }

        if (!tasks.length) {
            return;
        }

        try {
            await Promise.all(tasks);
        } catch (error) {
            handleApiError(error);
        }
    };

    const populateGroundTruthPatientFilter = () => {
        const select = el.groundTruthPatientFilter;
        if (!select) return;

        const patients = state.availablePatients || [];
        const options = ['<option value="">-- Selecciona un paciente --</option>'];
        patients.forEach((patient) => {
            options.push(`<option value="${escapeHtml(patient.id)}">${escapeHtml(patient.name)} (${escapeHtml(patient.email || "Sin correo")})</option>`);
        });

        select.innerHTML = options.join("");

        if (state.groundTruthSelectedPatientId && patients.some((patient) => patient.id === state.groundTruthSelectedPatientId)) {
            select.value = state.groundTruthSelectedPatientId;
        } else if (patients.length) {
            state.groundTruthSelectedPatientId = patients[0].id;
            select.value = state.groundTruthSelectedPatientId;
        } else {
            state.groundTruthSelectedPatientId = null;
            select.value = "";
        }

        const disableActions = !patients.length;
        select.disabled = disableActions;
        if (el.buttons.createGroundTruth) {
            el.buttons.createGroundTruth.disabled = disableActions;
        }
        if (el.buttons.refreshGroundTruth) {
            el.buttons.refreshGroundTruth.disabled = disableActions;
        }
    };

    const loadGroundTruthLabels = async (patientId, { showLoading = true } = {}) => {
        const container = el.tabBodies["ground-truth"] || el.tabPanels["ground-truth"];
        if (!container) return;

        if (!patientId) {
            state.groundTruthSelectedPatientId = null;
            state.tabCache.set("ground-truth", { patientId: null, labels: [] });
            renderGroundTruth([]);
            return;
        }

        state.groundTruthSelectedPatientId = patientId;

        if (showLoading) {
            setLoadingContainer(container, "Cargando etiquetas...");
        }

        try {
            const labels = await Api.admin.listGroundTruthLabels(state.token, state.selectedOrgId, patientId);
            const payload = {
                patientId,
                labels: Array.isArray(labels) ? labels : [],
            };
            state.tabCache.set("ground-truth", payload);
            renderGroundTruth(payload);
        } catch (error) {
            console.error("Error loading ground truth labels:", error);
            handleApiError(error);
            container.innerHTML = `<p class="form-error">${escapeHtml(error.message || "No se pudieron cargar las etiquetas")}</p>`;
        }
    };

    const showGroundTruthModal = async (patientId = null, labelId = null) => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización para gestionar etiquetas", "warning");
            return;
        }

        await ensureGroundTruthSupportData();
        const targetPatientId = patientId || state.groundTruthSelectedPatientId;
        if (!targetPatientId) {
            showToast("Selecciona un paciente para gestionar sus etiquetas", "warning");
            return;
        }

        const patient = state.availablePatients.find((item) => item.id === targetPatientId);
        if (!patient) {
            showToast("No se encontró el paciente seleccionado", "error");
            return;
        }

        if (!state.groundTruthEventTypes.length) {
            showToast("No hay tipos de evento configurados para etiquetas ground truth", "warning");
            return;
        }

        const isEdit = !!labelId;
        let currentLabel = null;
        if (isEdit) {
            try {
                currentLabel = await Api.admin.getGroundTruthLabel(state.token, state.selectedOrgId, targetPatientId, labelId);
                if (!currentLabel) {
                    showToast("No se encontró la etiqueta seleccionada", "warning");
                    return;
                }
            } catch (error) {
                handleApiError(error);
                return;
            }
        }

        let eventTypes = [...state.groundTruthEventTypes];
        if (currentLabel?.eventTypeCode && !eventTypes.some((eventType) => eventType.code === currentLabel.eventTypeCode)) {
            eventTypes.push({
                code: currentLabel.eventTypeCode,
                description: currentLabel.eventTypeLabel || currentLabel.eventTypeCode,
            });
        }
        const eventTypeOptions = eventTypes
            .map((eventType) => {
                const selected = eventType.code === currentLabel?.eventTypeCode ? "selected" : "";
                const label = eventType.description || eventType.code;
                return `<option value="${escapeHtml(eventType.code)}" ${selected}>${escapeHtml(label)}</option>`;
            })
            .join("");

        let staffMembers = [...state.availableStaff];
        if (currentLabel?.annotatedByUserId && !staffMembers.some((staff) => staff.userId === currentLabel.annotatedByUserId)) {
            staffMembers.push({
                userId: currentLabel.annotatedByUserId,
                name: currentLabel.annotatedByName || currentLabel.annotatedByUserId,
                email: null,
            });
        }

        const staffOptions = staffMembers
            .map((staff) => {
                const display = staff.name || staff.email || staff.userId;
                const selected = staff.userId === currentLabel?.annotatedByUserId ? "selected" : "";
                return `<option value="${escapeHtml(staff.userId)}" ${selected}>${escapeHtml(display)}</option>`;
            })
            .join("");

        const onsetValue = toDatetimeLocalValue(currentLabel?.onset);
        const offsetValue = toDatetimeLocalValue(currentLabel?.offsetAt);

        const modalHtml = `
        <div class="modal-overlay" id="groundTruthModal">
            <div class="modal-content modal-md">
                <div class="modal-header">
                    <h3>${isEdit ? "Editar etiqueta ground truth" : "Nueva etiqueta ground truth"}</h3>
                    <button class="modal-close" type="button" onclick="document.getElementById('groundTruthModal').remove()">&times;</button>
                </div>
                <form id="groundTruthForm" class="modal-form">
                    <div class="form-group">
                        <label>Paciente</label>
                        <input type="text" value="${escapeHtml(patient.name)}" readonly>
                    </div>
                    <div class="form-group">
                        <label for="groundTruthEventType">Tipo de evento *</label>
                        <select id="groundTruthEventType" name="event_type_code" required>
                            <option value="">-- Selecciona un tipo --</option>
                            ${eventTypeOptions}
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="groundTruthOnset">Inicio *</label>
                            <input id="groundTruthOnset" name="onset" type="datetime-local" required value="${escapeHtml(onsetValue)}">
                        </div>
                        <div class="form-group">
                            <label for="groundTruthOffset">Fin</label>
                            <input id="groundTruthOffset" name="offset_at" type="datetime-local" value="${escapeHtml(offsetValue)}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="groundTruthAnnotatedBy">Anotado por</label>
                        <select id="groundTruthAnnotatedBy" name="annotated_by_user_id">
                            <option value="">-- Sin especificar --</option>
                            ${staffOptions}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="groundTruthSource">Fuente</label>
                        <input id="groundTruthSource" name="source" type="text" maxlength="120" value="${escapeHtml(currentLabel?.source || "")}">
                    </div>
                    <div class="form-group">
                        <label for="groundTruthNote">Nota</label>
                        <textarea id="groundTruthNote" name="note" rows="3" maxlength="500">${escapeHtml(currentLabel?.note || "")}</textarea>
                    </div>
                    <div class="form-error hidden" id="groundTruthError"></div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-ghost" onclick="document.getElementById('groundTruthModal').remove()">Cancelar</button>
                        <button type="submit" class="btn btn-primary">${isEdit ? "Actualizar" : "Crear"}</button>
                    </div>
                </form>
            </div>
        </div>`;

        document.body.insertAdjacentHTML("beforeend", modalHtml);

        const modal = document.getElementById("groundTruthModal");
        const form = document.getElementById("groundTruthForm");
        const errorEl = document.getElementById("groundTruthError");

        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                modal.remove();
            }
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            errorEl.classList.add("hidden");

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = isEdit ? "Actualizando..." : "Creando...";

            const eventTypeCode = form.event_type_code.value.trim();
            const onsetIso = fromDatetimeLocalValue(form.onset.value);
            const offsetIso = fromDatetimeLocalValue(form.offset_at.value);
            const annotatedByUserId = form.annotated_by_user_id.value.trim();
            const sourceValue = form.source.value.trim();
            const noteValue = form.note.value.trim();

            if (!eventTypeCode) {
                errorEl.textContent = "Selecciona un tipo de evento";
                errorEl.classList.remove("hidden");
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? "Actualizar" : "Crear";
                return;
            }

            if (!onsetIso) {
                errorEl.textContent = "Proporciona una fecha de inicio válida";
                errorEl.classList.remove("hidden");
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? "Actualizar" : "Crear";
                return;
            }

            const payload = {
                event_type_code: eventTypeCode,
                onset: onsetIso,
            };

            if (offsetIso || isEdit) {
                payload.offset_at = offsetIso || null;
            }
            if (annotatedByUserId || isEdit) {
                payload.annotated_by_user_id = annotatedByUserId || null;
            }
            if (sourceValue || isEdit) {
                payload.source = sourceValue || null;
            }
            if (noteValue || isEdit) {
                payload.note = noteValue || null;
            }

            try {
                if (isEdit) {
                    await Api.admin.updateGroundTruthLabel(state.token, state.selectedOrgId, targetPatientId, labelId, payload);
                    showToast("Etiqueta actualizada correctamente", "success");
                } else {
                    await Api.admin.createGroundTruthLabel(state.token, state.selectedOrgId, targetPatientId, payload);
                    showToast("Etiqueta creada correctamente", "success");
                }
                modal.remove();
                state.tabCache.delete("ground-truth");
                await loadGroundTruthLabels(targetPatientId, { showLoading: true });
            } catch (error) {
                handleApiError(error);
                errorEl.textContent = error.message || "No se pudo guardar la etiqueta";
                errorEl.classList.remove("hidden");
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? "Actualizar" : "Crear";
            }
        });
    };

    // ============================================
    // Caregiver Assignment Functions
    // ============================================

    const showCaregiverAssignmentModal = async (patientId = null, caregiverId = null) => {
        if (!state.selectedOrgId) {
            showToast("Selecciona una organización para asignar cuidadores", "warning");
            return;
        }

        const isEdit = patientId && caregiverId;
        const modalTitle = isEdit ? "Editar asignación de cuidador" : "Asignar cuidador";

        // Load support data
        const [relationshipTypes, patients, staff] = await Promise.all([
            Api.admin.listCaregiverRelationshipTypes(state.token, state.selectedOrgId),
            Api.admin.listPatients(state.token, state.selectedOrgId),
            Api.admin.listStaff(state.token, state.selectedOrgId),
        ]);

        // If editing, get current assignment
        let currentAssignment = null;
        if (isEdit) {
            const assignments = await Api.admin.listCaregiverAssignments(state.token, state.selectedOrgId);
            currentAssignment = assignments.find(a => a.patientId === patientId && a.caregiverId === caregiverId);
        }

        const patientOptions = patients
            .map(p => `<option value="${escapeHtml(p.id)}" ${p.id === patientId ? 'selected' : ''}>${escapeHtml(p.name)} (${escapeHtml(p.email || 'Sin correo')})</option>`)
            .join('');

        const caregiverOptions = staff
            .map(s => `<option value="${escapeHtml(s.userId)}" ${s.userId === caregiverId ? 'selected' : ''}>${escapeHtml(s.name)} (${escapeHtml(s.email)})</option>`)
            .join('');

        const relationshipOptions = relationshipTypes
            .map(r => `<option value="${escapeHtml(r.id)}" ${currentAssignment?.relationshipTypeId === r.id ? 'selected' : ''}>${escapeHtml(r.label)}</option>`)
            .join('');

        const modalHtml = `
            <div class="modal-overlay" id="caregiverAssignmentModal">
                <div class="modal-content modal-lg">
                    <div class="modal-header">
                        <h3>👨‍⚕️ ${modalTitle}</h3>
                        <button class="modal-close" type="button" onclick="document.getElementById('caregiverAssignmentModal').remove()">&times;</button>
                    </div>
                    <form id="caregiverAssignmentForm" class="modal-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="assignPatientId">Paciente *</label>
                                <select id="assignPatientId" name="patient_id" required ${isEdit ? 'disabled' : ''}>
                                    <option value="">-- Selecciona un paciente --</option>
                                    ${patientOptions}
                                </select>
                                ${isEdit ? `<input type="hidden" name="patient_id" value="${escapeHtml(patientId)}">` : ''}
                            </div>
                            <div class="form-group">
                                <label for="assignCaregiverId">Cuidador *</label>
                                <select id="assignCaregiverId" name="caregiver_id" required ${isEdit ? 'disabled' : ''}>
                                    <option value="">-- Selecciona un usuario --</option>
                                    ${caregiverOptions}
                                </select>
                                ${isEdit ? `<input type="hidden" name="caregiver_id" value="${escapeHtml(caregiverId)}">` : ''}
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="assignRelationshipType">Tipo de relación</label>
                                <select id="assignRelationshipType" name="relationship_type_id">
                                    <option value="">-- Sin especificar --</option>
                                    ${relationshipOptions}
                                </select>
                            </div>
                            <div class="form-group form-group-checkbox">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="assignIsPrimary" name="is_primary" ${currentAssignment?.isPrimary ? 'checked' : ''}>
                                    <span>Es cuidador principal</span>
                                </label>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="assignStartedAt">Fecha de inicio</label>
                                <input type="date" id="assignStartedAt" name="started_at" value="${currentAssignment?.startedAt ? currentAssignment.startedAt.split('T')[0] : ''}">
                            </div>
                            <div class="form-group">
                                <label for="assignEndedAt">Fecha de fin (opcional)</label>
                                <input type="date" id="assignEndedAt" name="ended_at" value="${currentAssignment?.endedAt ? currentAssignment.endedAt.split('T')[0] : ''}">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="assignNote">Nota (opcional)</label>
                            <textarea id="assignNote" name="note" rows="3" maxlength="500">${escapeHtml(currentAssignment?.note || '')}</textarea>
                        </div>
                        <div class="form-error hidden" id="caregiverAssignmentError"></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-ghost" onclick="document.getElementById('caregiverAssignmentModal').remove()">Cancelar</button>
                            <button type="submit" class="btn btn-primary">${isEdit ? 'Actualizar' : 'Asignar'}</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const form = document.getElementById('caregiverAssignmentForm');
        const errorEl = document.getElementById('caregiverAssignmentError');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorEl.classList.add('hidden');

            const formData = new FormData(form);
            const payload = {
                patient_id: formData.get('patient_id'),
                caregiver_id: formData.get('caregiver_id'),
                relationship_type_id: formData.get('relationship_type_id') || null,
                is_primary: formData.has('is_primary'),
                started_at: formData.get('started_at') || null,
                ended_at: formData.get('ended_at') || null,
                note: formData.get('note') || null,
            };

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = isEdit ? 'Actualizando...' : 'Asignando...';

            try {
                if (isEdit) {
                    await Api.admin.updateCaregiverAssignment(state.token, state.selectedOrgId, patientId, caregiverId, payload);
                    showToast('Asignación actualizada correctamente', 'success');
                } else {
                    await Api.admin.createCaregiverAssignment(state.token, state.selectedOrgId, payload);
                    showToast('Cuidador asignado correctamente', 'success');
                }
                document.getElementById('caregiverAssignmentModal')?.remove();
                state.tabCache.delete('caregivers');
                await activateTab('caregivers');
            } catch (error) {
                errorEl.textContent = error.message || 'No se pudo completar la asignación';
                errorEl.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.textContent = isEdit ? 'Actualizar' : 'Asignar';
            }
        });
    };

    const bindEvents = () => {
        if (!modalEventsBound) {
            el.modal.close?.addEventListener("click", () => closeModal());
            el.modal.overlay?.addEventListener("click", (event) => {
                if (event.target === el.modal.overlay) {
                    closeModal();
                }
            });
            el.modal.footer?.addEventListener("click", (event) => {
                if (event.target.closest("[data-modal-close]")) {
                    closeModal();
                }
            });
            document.addEventListener("keydown", (event) => {
                if (event.key === "Escape" && !el.modal.overlay?.classList.contains("hidden")) {
                    closeModal();
                }
            });
            modalEventsBound = true;
        }

        if (el.buttons.createGroundTruth) {
            el.buttons.createGroundTruth.disabled = true;
        }
        if (el.buttons.refreshGroundTruth) {
            el.buttons.refreshGroundTruth.disabled = true;
        }
        if (el.groundTruthPatientFilter) {
            el.groundTruthPatientFilter.disabled = true;
        }

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

        el.buttons.assignCaregiver?.addEventListener("click", () => {
            showCaregiverAssignmentModal();
        });

        el.buttons.createPatient?.addEventListener("click", () => {
            showPatientModal();
        });

        el.buttons.createAlert?.addEventListener("click", () => {
            showAlertModal();
        });

        el.buttons.createDevice?.addEventListener("click", () => {
            showDeviceModal();
        });

        el.buttons.createGroundTruth?.addEventListener("click", () => {
            showGroundTruthModal();
        });

        el.buttons.refreshGroundTruth?.addEventListener("click", () => {
            const patientId = state.groundTruthSelectedPatientId || el.groundTruthPatientFilter?.value || "";
            state.tabCache.delete("ground-truth");
            loadGroundTruthLabels(patientId, { showLoading: true });
        });

        el.groundTruthPatientFilter?.addEventListener("change", async (event) => {
            const patientId = event.target.value || null;
            state.groundTruthSelectedPatientId = patientId || null;
            state.tabCache.delete("ground-truth");
            await loadGroundTruthLabels(patientId, { showLoading: true });
        });

        el.buttons.refreshPushDevices?.addEventListener("click", () => {
            activateTab("push-devices");
        });

        // Search and filter event listeners
        el.patientsSearchInput?.addEventListener("input", (e) => {
            state.patientsSearchQuery = e.target.value;
            state.pagination.patients.page = 1;
            const cachedData = state.tabCache.get('patients');
            if (cachedData) renderPatients(cachedData);
        });

        el.staffSearchInput?.addEventListener("input", (e) => {
            state.staffSearchQuery = e.target.value;
            state.pagination.staff.page = 1;
            const cachedData = state.tabCache.get('staff');
            if (cachedData) renderStaff(cachedData);
        });

        el.alertsStatusFilter?.addEventListener("change", (e) => {
            state.alertsFilterStatus = e.target.value || null;
            state.pagination.alerts.page = 1;
            const cachedData = state.tabCache.get('alerts');
            if (cachedData) renderAlerts(cachedData);
        });

        el.alertsLevelFilter?.addEventListener("change", (e) => {
            state.alertsFilterLevel = e.target.value || null;
            state.pagination.alerts.page = 1;
            const cachedData = state.tabCache.get('alerts');
            if (cachedData) renderAlerts(cachedData);
        });

        el.devicesStatusFilter?.addEventListener("change", (e) => {
            state.devicesFilterStatus = e.target.value || null;
            state.pagination.devices.page = 1;
            const cachedData = state.tabCache.get('devices');
            if (cachedData) renderDevices(cachedData);
        });

        el.pushDevicesStatusFilter?.addEventListener("change", (e) => {
            state.pushDevicesFilterStatus = e.target.value || null;
            state.pagination.pushDevices.page = 1;
            const cachedData = state.tabCache.get('push-devices');
            if (cachedData) renderPushDevices(cachedData);
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
        viewPatientProfile: async (patientId) => {
            await viewPatientProfile(patientId);
        },
        viewStaffProfile: async (userId) => {
            await viewStaffProfile(userId);
        },
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
                state.availablePatients = [];
                state.tabCache.delete('ground-truth');
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
            await showAlertModal(alertId);
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
        editCaregiverAssignment: async (patientId, caregiverId) => {
            await showCaregiverAssignmentModal(patientId, caregiverId);
        },
        deleteCaregiverAssignment: async (patientId, caregiverId) => {
            if (!confirm("¿Está seguro de eliminar esta asignación de cuidador?")) return;
            try {
                await Api.admin.deleteCaregiverAssignment(state.token, state.selectedOrgId, patientId, caregiverId);
                showToast('Asignación eliminada correctamente', 'success');
                state.tabCache.delete('caregivers');
                await activateTab("caregivers");
            } catch (error) {
                handleApiError(error);
            }
        },
        createGroundTruth: async () => {
            await showGroundTruthModal();
        },
        editGroundTruth: async (patientId, labelId) => {
            await showGroundTruthModal(patientId, labelId);
        },
        deleteGroundTruth: async (patientId, labelId) => {
            if (!confirm("¿Eliminar esta etiqueta ground truth?")) return;
            try {
                await Api.admin.deleteGroundTruthLabel(state.token, state.selectedOrgId, patientId, labelId);
                showToast('Etiqueta eliminada correctamente', 'success');
                state.tabCache.delete('ground-truth');
                const nextPatientId = patientId || state.groundTruthSelectedPatientId;
                await loadGroundTruthLabels(nextPatientId, { showLoading: true });
            } catch (error) {
                handleApiError(error);
            }
        },
        editDevice: async (deviceId) => {
            await showDeviceModal(deviceId);
        },
        deleteDevice: async (deviceId) => {
            if (!confirm("¿Está seguro de eliminar este dispositivo?")) return;
            try {
                await Api.admin.deleteDevice(state.token, state.selectedOrgId, deviceId);
                showToast('Dispositivo eliminado correctamente', 'success');
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
                showToast(`Dispositivo push ${activate ? "activado" : "desactivado"}`, "success");
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
                showToast('Push device eliminado correctamente', 'success');
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
