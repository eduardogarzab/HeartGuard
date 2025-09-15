/**
 * HeartGuard - Superadministrador Dashboard
 * JavaScript para funcionalidad interactiva
 */

class HeartGuardApp {
    constructor() {
        this.baseURL = '/admin';
        this.token = localStorage.getItem('heartguard_token');
        this.currentUser = null;
        this.dashboardData = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
        this.hideLoadingScreen();
    }

    setupEventListeners() {
        // Login form
        document.getElementById('loginForm')?.addEventListener('submit', (e) => this.handleLogin(e));
        
        // Sidebar toggle
        document.getElementById('sidebarToggle')?.addEventListener('click', () => this.toggleSidebar());
        
        // Menu navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => this.handleMenuClick(e));
        });
        
        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.handleLogout());
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });
        
        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });
        
        // Create user form
        document.getElementById('createUserForm')?.addEventListener('submit', (e) => this.handleCreateUser(e));
        
        // Auto-refresh dashboard every 30 seconds
        setInterval(() => this.refreshDashboard(), 30000);
    }

    checkAuthStatus() {
        if (this.token) {
            this.showDashboard();
            this.loadDashboard();
        } else {
            this.showLogin();
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');
        
        try {
            errorDiv.style.display = 'none';
            
            const response = await fetch(`${this.baseURL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.token = data.token;
                this.currentUser = data.usuario;
                localStorage.setItem('heartguard_token', this.token);
                localStorage.setItem('heartguard_user', JSON.stringify(this.currentUser));
                
                this.showDashboard();
                this.loadDashboard();
                this.showToast('¡Bienvenido al panel de HeartGuard!', 'success');
            } else {
                throw new Error(data.error || 'Error de autenticación');
            }
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    handleLogout() {
        if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
            fetch(`${this.baseURL}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            }).catch(() => {}); // Ignore errors on logout
            
            localStorage.removeItem('heartguard_token');
            localStorage.removeItem('heartguard_user');
            this.token = null;
            this.currentUser = null;
            this.showLogin();
            this.showToast('Sesión cerrada exitosamente', 'success');
        }
    }

    showLogin() {
        document.getElementById('loginScreen').style.display = 'flex';
        document.getElementById('dashboard').style.display = 'none';
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
        document.getElementById('loginError').style.display = 'none';
    }

    showDashboard() {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('dashboard').style.display = 'flex';
        
        // Restaurar estado del sidebar
        this.restoreSidebarState();
    }

    restoreSidebarState() {
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }
    }

    hideLoadingScreen() {
        setTimeout(() => {
            document.getElementById('loadingScreen').classList.add('hidden');
        }, 1000);
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            
            // Guardar estado en localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed.toString());
            
            console.log('Sidebar toggled:', isCollapsed ? 'collapsed' : 'expanded');
        }
    }

    handleMenuClick(e) {
        e.preventDefault();
        
        // Remove active class from all menu items
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to clicked item
        e.currentTarget.classList.add('active');
        
        // Show corresponding section
        const section = e.currentTarget.dataset.section;
        this.showSection(section);
        
        // Update page title
        this.updatePageTitle(section);
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show selected section
        const targetSection = document.getElementById(`${sectionName}Section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Load section data
        this.loadSectionData(sectionName);
    }

    updatePageTitle(section) {
        const titles = {
            dashboard: 'Dashboard',
            usuarios: 'Gestión de Usuarios',
            familias: 'Gestión de Familias',
            alertas: 'Gestión de Alertas',
            ubicaciones: 'Ubicaciones de Usuarios',
            metricas: 'Métricas Fisiológicas',
            catalogos: 'Catálogos del Sistema',
            logs: 'Logs del Sistema',
            microservicios: 'Estado de Microservicios'
        };
        
        const subtitles = {
            dashboard: 'Panel de control del sistema HeartGuard',
            usuarios: 'Administra usuarios del sistema',
            familias: 'Gestiona familias y sus miembros',
            alertas: 'Monitorea y gestiona alertas médicas',
            ubicaciones: 'Consulta ubicaciones históricas',
            metricas: 'Accede a métricas fisiológicas',
            catalogos: 'Administra catálogos globales',
            logs: 'Revisa actividad del sistema',
            microservicios: 'Monitorea estado de servicios'
        };
        
        document.getElementById('pageTitle').textContent = titles[section] || 'Dashboard';
        document.getElementById('pageSubtitle').textContent = subtitles[section] || 'Panel de control del sistema HeartGuard';
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'usuarios':
                await this.loadUsuarios();
                break;
            case 'familias':
                await this.loadFamilias();
                break;
            case 'alertas':
                await this.loadAlertas();
                break;
            case 'catalogos':
                await this.loadCatalogos();
                break;
            case 'logs':
                await this.loadLogs();
                break;
            case 'microservicios':
                await this.loadMicroservicios();
                break;
            case 'ubicaciones':
                await this.loadUbicaciones();
                break;
        }
    }

    async loadDashboard() {
        try {
            console.log('📊 Loading dashboard...');
            const response = await this.apiCall('/dashboard');
            console.log('📊 Dashboard response:', response);
            if (response.success) {
                this.dashboardData = response.data;
                this.updateDashboardStats(response.data);
                this.updateBadges(response.data);
                console.log('✅ Dashboard loaded successfully');
            }
        } catch (error) {
            console.error('❌ Error loading dashboard:', error);
            this.showToast('Error cargando dashboard', 'error');
        }
    }

    updateDashboardStats(data) {
        console.log('📊 Updating dashboard stats with data:', data);
        
        // Verificar que los elementos existen antes de actualizarlos
        const elements = {
            'totalUsuarios': data.total_usuarios || 0,
            'totalFamilias': data.total_familias || 0,
            'alertasPendientes': data.alertas_pendientes || 0,
            'alertasCriticas': data.alertas_criticas || 0,
            'ubicacionesHoy': data.ubicaciones_hoy || 0,
            'microserviciosActivos': data.microservicios_activos || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                console.log(`✅ Updated ${id} to: ${value}`);
            } else {
                console.warn(`⚠️ Element with id '${id}' not found`);
            }
        });
    }

    updateBadges(data) {
        console.log('🔔 Updating badges with data:', data);
        const alertasBadge = document.getElementById('alertasBadge');
        const notificationsBadge = document.getElementById('notificationsBadge');
        
        if (alertasBadge) {
            alertasBadge.textContent = data.alertas_pendientes || 0;
            console.log('✅ Alertas badge updated to:', data.alertas_pendientes || 0);
        } else {
            console.error('❌ Element alertasBadge not found');
        }
        
        if (notificationsBadge) {
            notificationsBadge.textContent = data.alertas_criticas || 0;
            console.log('✅ Notifications badge updated to:', data.alertas_criticas || 0);
        } else {
            console.error('❌ Element notificationsBadge not found');
        }
    }

    async loadUsuarios() {
        try {
            const response = await this.apiCall('/usuarios');
            if (response.success) {
                this.renderUsuariosTable(response.data);
            }
        } catch (error) {
            console.error('Error loading usuarios:', error);
            this.showToast('Error cargando usuarios', 'error');
        }
    }

    searchUsuarios() {
        const searchTerm = document.getElementById('usuarioSearch').value.toLowerCase();
        const rows = document.querySelectorAll('#usuariosTable tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchFamilias() {
        const searchTerm = document.getElementById('familiaSearch').value.toLowerCase();
        const rows = document.querySelectorAll('#familiasTable tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchAlertas() {
        const searchTerm = document.getElementById('alertaSearch').value.toLowerCase();
        const rows = document.querySelectorAll('#alertasTable tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchUbicaciones() {
        const searchTerm = document.getElementById('ubicacionSearch').value.toLowerCase();
        const rows = document.querySelectorAll('#ubicacionesTable tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    renderUsuariosTable(usuarios) {
        const tbody = document.getElementById('usuariosTable');
        tbody.innerHTML = '';
        
        if (!usuarios || usuarios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay usuarios disponibles</td></tr>';
            return;
        }
        
        usuarios.forEach(usuario => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${usuario.id}</td>
                <td>${usuario.nombre}</td>
                <td>${usuario.email}</td>
                <td><span class="badge ${usuario.rol === 'superadmin' ? 'badge-primary' : 'badge-secondary'}">${usuario.rol}</span></td>
                <td>${usuario.familia_nombre || '-'}</td>
                <td><span class="badge ${usuario.estado ? 'badge-success' : 'badge-error'}">${usuario.estado ? 'Activo' : 'Inactivo'}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="showEditUserModal(${usuario.id})" title="Editar usuario">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-error" onclick="app.deleteUsuario(${usuario.id})" title="Eliminar usuario">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadFamilias() {
        try {
            const response = await this.apiCall('/familias');
            if (response.success) {
                this.renderFamiliasTable(response.data);
            }
        } catch (error) {
            console.error('Error loading familias:', error);
            this.showToast('Error cargando familias', 'error');
        }
    }

    renderFamiliasTable(familias) {
        const tbody = document.getElementById('familiasTable');
        tbody.innerHTML = '';
        
        familias.forEach(familia => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${familia.id}</td>
                <td>${familia.nombre_familia}</td>
                <td>${familia.total_miembros}</td>
                <td>${new Date(familia.fecha_creacion).toLocaleDateString()}</td>
                <td><span class="badge ${familia.estado ? 'badge-success' : 'badge-error'}">${familia.estado ? 'Activa' : 'Inactiva'}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="showEditFamilyModal(${familia.id})" title="Editar familia">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-error" onclick="app.deleteFamilia(${familia.id})" title="Eliminar familia">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadAlertas() {
        try {
            const response = await this.apiCall('/alertas');
            if (response.success) {
                this.renderAlertasTable(response.data);
            }
        } catch (error) {
            console.error('Error loading alertas:', error);
            this.showToast('Error cargando alertas', 'error');
        }
    }

    renderAlertasTable(alertas) {
        const tbody = document.getElementById('alertasTable');
        tbody.innerHTML = '';
        
        alertas.forEach(alerta => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${alerta.id}</td>
                <td>${alerta.usuario_nombre}</td>
                <td>${alerta.tipo}</td>
                <td>${alerta.descripcion}</td>
                <td><span class="badge ${alerta.nivel === 'critico' ? 'badge-error' : 'badge-warning'}">${alerta.nivel}</span></td>
                <td>${new Date(alerta.fecha).toLocaleString()}</td>
                <td><span class="badge ${alerta.atendida ? 'badge-success' : 'badge-warning'}">${alerta.atendida ? 'Atendida' : 'Pendiente'}</span></td>
                <td>
                    ${!alerta.atendida ? `
                        <button class="btn btn-sm btn-success" onclick="app.atenderAlerta(${alerta.id})">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-error" onclick="app.deleteAlerta(${alerta.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadCatalogos() {
        try {
            const response = await this.apiCall('/catalogos');
            if (response.success) {
                this.renderCatalogosTable(response.data);
            }
        } catch (error) {
            console.error('Error loading catalogos:', error);
            this.showToast('Error cargando catálogos', 'error');
        }
    }

    renderCatalogosTable(catalogos) {
        const tbody = document.getElementById('catalogosTable');
        tbody.innerHTML = '';
        
        catalogos.forEach(catalogo => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${catalogo.id}</td>
                <td>${catalogo.tipo}</td>
                <td>${catalogo.clave}</td>
                <td>${catalogo.valor}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="app.editCatalogo(${catalogo.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-error" onclick="app.deleteCatalogo(${catalogo.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadLogs() {
        try {
            const response = await this.apiCall('/logs');
            if (response.success) {
                this.renderLogsTable(response.data);
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            this.showToast('Error cargando logs', 'error');
        }
    }

    renderLogsTable(logs) {
        const tbody = document.getElementById('logsTable');
        tbody.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No hay logs disponibles</td></tr>';
            return;
        }
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.id}</td>
                <td>${log.usuario_nombre || 'Sistema'}</td>
                <td>${log.accion}</td>
                <td>${log.detalle}</td>
                <td>${new Date(log.fecha).toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadMicroservicios() {
        try {
            const response = await this.apiCall('/microservicios');
            if (response.success) {
                this.renderMicroserviciosGrid(response.data);
            }
        } catch (error) {
            console.error('Error loading microservicios:', error);
            this.showToast('Error cargando microservicios', 'error');
        }
    }

    renderMicroserviciosGrid(microservicios) {
        const grid = document.getElementById('microserviciosGrid');
        grid.innerHTML = '';
        
        if (!microservicios || microservicios.length === 0) {
            grid.innerHTML = '<div class="text-center text-muted">No hay microservicios configurados</div>';
            return;
        }
        
        microservicios.forEach(ms => {
            const card = document.createElement('div');
            card.className = `microservice-card ${ms.estado}`;
            card.innerHTML = `
                <div class="microservice-header">
                    <h3>${ms.nombre}</h3>
                    <span class="badge ${ms.estado === 'activo' ? 'badge-success' : 'badge-error'}">${ms.estado}</span>
                </div>
                <p class="microservice-url">${ms.url}</p>
                ${ms.version ? `<p class="microservice-version">Versión: ${ms.version}</p>` : ''}
                ${ms.ultima_verificacion ? `<p class="microservice-time">Última verificación: ${new Date(ms.ultima_verificacion).toLocaleString()}</p>` : ''}
                <div class="microservice-actions">
                    <button class="btn btn-sm btn-secondary" onclick="app.updateMicroservicioEstado(${ms.id}, 'activo')">
                        <i class="fas fa-play"></i> Activar
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="app.updateMicroservicioEstado(${ms.id}, 'inactivo')">
                        <i class="fas fa-pause"></i> Desactivar
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Modal functions
    showCreateUserModal() {
        this.openModal('createUserModal');
        this.loadFamiliasForSelect();
    }

    showCreateFamilyModal() {
        // Implement create family modal
        this.showToast('Función en desarrollo', 'warning');
    }

    showCreateAlertModal() {
        // Implement create alert modal
        this.showToast('Función en desarrollo', 'warning');
    }

    showCreateCatalogModal() {
        // Implement create catalog modal
        this.showToast('Función en desarrollo', 'warning');
    }

    async loadFamiliasForSelect() {
        try {
            const response = await this.apiCall('/familias');
            if (response.success) {
                const select = document.getElementById('userFamily');
                select.innerHTML = '<option value="">Sin familia</option>';
                response.data.forEach(familia => {
                    const option = document.createElement('option');
                    option.value = familia.id;
                    option.textContent = familia.nombre_familia;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading familias for select:', error);
        }
    }

    async handleCreateUser(e) {
        e.preventDefault();
        
        const formData = {
            nombre: document.getElementById('userName').value,
            email: document.getElementById('userEmail').value,
            password: document.getElementById('userPassword').value,
            rol: document.getElementById('userRole').value,
            familia_id: document.getElementById('userFamily').value || null
        };
        
        try {
            const response = await this.apiCall('/usuarios', 'POST', formData);
            if (response.success) {
                this.showToast('Usuario creado exitosamente', 'success');
                this.closeModal('createUserModal');
                this.loadUsuarios();
            }
        } catch (error) {
            this.showToast('Error creando usuario: ' + error.message, 'error');
        }
    }

    // CRUD Operations
    async editUsuario(id) {
        this.showToast('Función de edición en desarrollo', 'warning');
    }

    async deleteUsuario(id) {
        if (confirm('¿Estás seguro de eliminar este usuario?')) {
            try {
                await this.apiCall(`/usuarios/${id}`, 'DELETE');
                this.showToast('Usuario eliminado exitosamente', 'success');
                this.loadUsuarios();
            } catch (error) {
                this.showToast('Error eliminando usuario', 'error');
            }
        }
    }

    async editFamilia(id) {
        this.showToast('Función de edición en desarrollo', 'warning');
    }

    async deleteFamilia(id) {
        if (confirm('¿Estás seguro de eliminar esta familia?')) {
            try {
                await this.apiCall(`/familias/${id}`, 'DELETE');
                this.showToast('Familia eliminada exitosamente', 'success');
                this.loadFamilias();
            } catch (error) {
                this.showToast('Error eliminando familia', 'error');
            }
        }
    }

    async atenderAlerta(id) {
        try {
            await this.apiCall(`/alertas/${id}/atender`, 'PUT', { atendido_por: this.currentUser?.id || 1 });
            this.showToast('Alerta atendida exitosamente', 'success');
            this.loadAlertas();
            this.refreshDashboard();
        } catch (error) {
            this.showToast('Error atendiendo alerta', 'error');
        }
    }

    async deleteAlerta(id) {
        if (confirm('¿Estás seguro de eliminar esta alerta?')) {
            try {
                await this.apiCall(`/alertas/${id}`, 'DELETE');
                this.showToast('Alerta eliminada exitosamente', 'success');
                this.loadAlertas();
                this.refreshDashboard();
            } catch (error) {
                this.showToast('Error eliminando alerta', 'error');
            }
        }
    }

    async editCatalogo(id) {
        this.showToast('Función de edición en desarrollo', 'warning');
    }

    async deleteCatalogo(id) {
        if (confirm('¿Estás seguro de eliminar este catálogo?')) {
            try {
                await this.apiCall(`/catalogos/${id}`, 'DELETE');
                this.showToast('Catálogo eliminado exitosamente', 'success');
                this.loadCatalogos();
            } catch (error) {
                this.showToast('Error eliminando catálogo', 'error');
            }
        }
    }

    async updateMicroservicioEstado(id, estado) {
        try {
            await this.apiCall(`/microservicios/${id}/estado`, 'PUT', { estado });
            this.showToast(`Microservicio ${estado === 'activo' ? 'activado' : 'desactivado'} exitosamente`, 'success');
            this.loadMicroservicios();
        } catch (error) {
            this.showToast('Error actualizando microservicio', 'error');
        }
    }

    async refreshMicroservicios() {
        await this.loadMicroservicios();
        this.showToast('Microservicios actualizados', 'success');
    }

    async loadUbicaciones() {
        try {
            const response = await this.apiCall('/ubicaciones');
            if (response.success) {
                this.renderUbicacionesTable(response.data);
            }
        } catch (error) {
            console.error('Error loading ubicaciones:', error);
            this.showToast('Error cargando ubicaciones', 'error');
        }
    }

    async refreshUbicaciones() {
        await this.loadUbicaciones();
        this.showToast('Ubicaciones actualizadas', 'success');
    }

    renderUbicacionesTable(ubicaciones) {
        const tbody = document.getElementById('ubicacionesTable');
        tbody.innerHTML = '';
        
        if (!ubicaciones || ubicaciones.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No hay ubicaciones disponibles</td></tr>';
            return;
        }
        
        ubicaciones.forEach(ubicacion => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ubicacion.id}</td>
                <td>${ubicacion.usuario_nombre}</td>
                <td>${ubicacion.latitud}</td>
                <td>${ubicacion.longitud}</td>
                <td>${ubicacion.precision_metros ? ubicacion.precision_metros + 'm' : '-'}</td>
                <td><span class="badge badge-secondary">${ubicacion.fuente || 'gps'}</span></td>
                <td>${ubicacion.ubicacion_timestamp ? new Date(ubicacion.ubicacion_timestamp).toLocaleString() : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="app.viewUbicacionOnMap(${ubicacion.latitud}, ${ubicacion.longitud})">
                        <i class="fas fa-map"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    viewUbicacionOnMap(lat, lng) {
        // Abrir Google Maps con las coordenadas
        const url = `https://www.google.com/maps?q=${lat},${lng}`;
        window.open(url, '_blank');
    }

    async refreshDashboard() {
        await this.loadDashboard();
    }

    // Utility functions
    async apiCall(endpoint, method = 'GET', data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Error en la petición');
        }
        
        return result;
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        if (typeof modalId === 'string') {
            document.getElementById(modalId).classList.remove('active');
        } else {
            modalId.classList.remove('active');
        }
        document.body.style.overflow = '';
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function showCreateAlertModal() {
    app.showCreateAlertModal();
}

function showCreateCatalogModal() {
    app.showCreateCatalogModal();
}


function refreshMicroservicios() {
    app.refreshMicroservicios();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new HeartGuardApp();
});

// Add some CSS for badges
const badgeStyles = `
.badge-primary { background: var(--primary-color); color: white; }
.badge-secondary { background: var(--secondary-color); color: white; }
.badge-success { background: var(--success-color); color: white; }
.badge-warning { background: var(--warning-color); color: white; }
.badge-error { background: var(--error-color); color: white; }
.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
.microservice-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.microservice-url { color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem; }
.microservice-version { color: var(--text-muted); font-size: 0.75rem; margin-bottom: 0.5rem; }
.microservice-time { color: var(--text-muted); font-size: 0.75rem; margin-bottom: 1rem; }
.microservice-actions { display: flex; gap: 0.5rem; }
.toast-close { background: none; border: none; color: inherit; cursor: pointer; margin-left: auto; }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = badgeStyles;
document.head.appendChild(styleSheet);

// =========================================================
// FUNCIONES GLOBALES PARA MODALES
// =========================================================

function showCreateUserModal() {
    console.log('🔥 showCreateUserModal called!');
    
    try {
        console.log('🔍 Buscando elementos...');
        
        const modal = document.getElementById('createUserModal');
        const title = document.getElementById('userModalTitle');
        const submitText = document.getElementById('userSubmitText');
        
        console.log('Modal found:', modal);
        console.log('Title found:', title);
        console.log('SubmitText found:', submitText);
        
        if (modal) {
            modal.classList.add('active');
            console.log('✅ Modal class "active" added');
        } else {
            console.error('❌ Modal not found!');
        }
        
        // Mostrar campos de contraseña y restaurar required para creación
        const passwordRow = document.getElementById('passwordRow');
        if (passwordRow) {
            passwordRow.style.display = 'grid';
            
            // Restaurar required en los campos de contraseña
            const passwordField = document.getElementById('userPassword');
            const passwordConfirmField = document.getElementById('userPasswordConfirm');
            
            if (passwordField) {
                passwordField.setAttribute('required', 'required');
            }
            if (passwordConfirmField) {
                passwordConfirmField.setAttribute('required', 'required');
            }
        }
        
        // Cargar familias para el dropdown
        if (window.app) {
            loadFamiliesForSelect();
        } else {
            console.error('❌ App not initialized');
        }
        
        if (title) {
            title.textContent = 'Crear Nuevo Usuario';
            console.log('✅ Title updated');
        }
        
        if (submitText) {
            submitText.textContent = 'Crear Usuario';
            console.log('✅ Submit text updated');
        }
        
        console.log('✅ Modal opened successfully');
    } catch (error) {
        console.error('❌ Error opening modal:', error);
        alert('Error: ' + error.message);
    }
}

async function showEditUserModal(userId) {
    console.log('Opening edit user modal for ID:', userId);
    try {
        document.getElementById('userModalTitle').textContent = 'Editar Usuario';
        document.getElementById('userSubmitText').textContent = 'Actualizar Usuario';
        document.getElementById('userId').value = userId;
        
        // Ocultar campos de contraseña para edición y remover required
        const passwordRow = document.getElementById('passwordRow');
        if (passwordRow) {
            passwordRow.style.display = 'none';
            
            // Remover required de los campos de contraseña
            const passwordField = document.getElementById('userPassword');
            const passwordConfirmField = document.getElementById('userPasswordConfirm');
            
            if (passwordField) {
                passwordField.removeAttribute('required');
            }
            if (passwordConfirmField) {
                passwordConfirmField.removeAttribute('required');
            }
        }
        
        // Cargar familias para el dropdown
        if (window.app) {
            await loadFamiliesForSelect();
        }
        
        // Cargar datos del usuario
        if (window.app) {
            await loadUserData(userId);
        }
        
        document.getElementById('createUserModal').classList.add('active');
        console.log('Edit modal opened successfully');
    } catch (error) {
        console.error('Error opening edit modal:', error);
    }
}

function showCreateFamilyModal() {
    console.log('Opening create family modal');
    try {
        document.getElementById('familyModalTitle').textContent = 'Crear Nueva Familia';
        document.getElementById('familySubmitText').textContent = 'Crear Familia';
        document.getElementById('createFamilyModal').classList.add('active');
        console.log('Family modal opened successfully');
    } catch (error) {
        console.error('Error opening family modal:', error);
    }
}

async function showEditFamilyModal(familyId) {
    console.log('Opening edit family modal for ID:', familyId);
    try {
        document.getElementById('familyModalTitle').textContent = 'Editar Familia';
        document.getElementById('familySubmitText').textContent = 'Actualizar Familia';
        document.getElementById('familyId').value = familyId;
        
        // Cargar datos de la familia
        if (window.app) {
            await loadFamilyData(familyId);
        }
        
        document.getElementById('createFamilyModal').classList.add('active');
        console.log('Edit family modal opened successfully');
    } catch (error) {
        console.error('Error opening edit family modal:', error);
    }
}

function closeModal(modalId) {
    console.log('Closing modal:', modalId);
    try {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            console.log('Modal class "active" removed');
        }
    } catch (error) {
        console.error('Error closing modal:', error);
    }
}

function resetUserForm() {
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';
    
    // Mostrar campos de contraseña y restaurar required
    const passwordRow = document.getElementById('passwordRow');
    if (passwordRow) {
        passwordRow.style.display = 'grid';
        
        const passwordField = document.getElementById('userPassword');
        const passwordConfirmField = document.getElementById('userPasswordConfirm');
        
        if (passwordField) {
            passwordField.setAttribute('required', 'required');
        }
        if (passwordConfirmField) {
            passwordConfirmField.setAttribute('required', 'required');
        }
    }
}

function resetFamilyForm() {
    document.getElementById('familyForm').reset();
    document.getElementById('familyId').value = '';
}

async function loadUserData(userId) {
    console.log('🔄 Loading user data for ID:', userId);
    try {
        const response = await window.app.apiCall(`/usuarios/${userId}`);
        console.log('📊 User response:', response);
        
        if (response.success) {
            const user = response.data;
            console.log('👤 User data:', user);
            
            document.getElementById('userName').value = user.nombre || '';
            document.getElementById('userEmail').value = user.email || '';
            document.getElementById('userRole').value = user.rol_nombre || '';
            document.getElementById('userStatus').value = user.estado ? 'true' : 'false';
            
            // Cargar familias y luego asignar la familia del usuario
            await loadFamiliesForSelect();
            
            // Asignar la familia correcta por ID
            if (user.familia_id) {
                document.getElementById('userFamily').value = user.familia_id;
                console.log('✅ Family assigned:', user.familia_id);
            } else {
                document.getElementById('userFamily').value = '';
                console.log('ℹ️ No family assigned');
            }
            
            console.log('✅ User data loaded successfully');
        } else {
            console.error('❌ Failed to load user data:', response);
        }
    } catch (error) {
        console.error('❌ Error loading user data:', error);
        window.app.showToast('Error cargando datos del usuario', 'error');
    }
}

async function loadFamilyData(familyId) {
    console.log('🔄 Loading family data for ID:', familyId);
    try {
        const response = await window.app.apiCall(`/familias/${familyId}`);
        console.log('📊 Family response:', response);
        
        if (response.success) {
            const family = response.data;
            console.log('🏠 Family data:', family);
            
            document.getElementById('familyName').value = family.nombre_familia || '';
            document.getElementById('familyCode').value = family.codigo_familia || '';
            document.getElementById('familyDescription').value = family.descripcion || '';
            document.getElementById('familyStatus').value = family.estado ? 'true' : 'false';
            
            console.log('✅ Family data loaded successfully');
        } else {
            console.error('❌ Failed to load family data:', response);
        }
    } catch (error) {
        console.error('❌ Error loading family data:', error);
        window.app.showToast('Error cargando datos de la familia', 'error');
    }
}

async function loadFamiliesForSelect() {
    console.log('🔄 Loading families for select...');
    try {
        const response = await window.app.apiCall('/familias');
        console.log('📊 Families response:', response);
        
        if (response.success) {
            const select = document.getElementById('userFamily');
            console.log('🎯 Family select element:', select);
            
            if (select) {
                // Mantener la opción "Sin familia"
                select.innerHTML = '<option value="">Sin familia asignada</option>';
                
                response.data.forEach(family => {
                    const option = document.createElement('option');
                    option.value = family.id;
                    option.textContent = family.nombre_familia;
                    select.appendChild(option);
                    console.log('✅ Added family option:', family.nombre_familia);
                });
                
                console.log('✅ Families loaded successfully');
            } else {
                console.error('❌ Family select element not found!');
            }
        } else {
            console.error('❌ Failed to load families:', response);
        }
    } catch (error) {
        console.error('❌ Error loading families:', error);
    }
}

// =========================================================
// EVENT LISTENERS PARA FORMULARIOS
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    // Formulario de usuario
    document.getElementById('userForm').addEventListener('submit', async function(e) {
        console.log('📝 Form submit event triggered!');
        e.preventDefault();
        await handleUserSubmit();
    });
    
    // Formulario de familia
    document.getElementById('familyForm').addEventListener('submit', async function(e) {
        console.log('📝 Family form submit event triggered!');
        e.preventDefault();
        await handleFamilySubmit();
    });
});

async function handleUserSubmit() {
    console.log('🔥 handleUserSubmit called!');
    
    const userId = document.getElementById('userId').value;
    const isEdit = userId !== '';
    
    console.log('👤 User ID:', userId);
    console.log('📝 Is Edit:', isEdit);
    
    const familiaValue = document.getElementById('userFamily').value;
    const familiaId = familiaValue ? parseInt(familiaValue) : null;
    
    console.log('🏠 Familia Value:', familiaValue);
    console.log('🏠 Familia ID:', familiaId);
    
    const userData = {
        nombre: document.getElementById('userName').value,
        email: document.getElementById('userEmail').value,
        rol: document.getElementById('userRole').value,
        estado: document.getElementById('userStatus').value === 'true',
        familia_id: familiaId,
        relacion: familiaId ? 'miembro' : '' // Valor por defecto para la relación
    };
    
    // Solo incluir contraseña si es creación o si se proporcionó
    const password = document.getElementById('userPassword').value;
    const passwordConfirm = document.getElementById('userPasswordConfirm').value;
    
    if (!isEdit && password) {
        if (password !== passwordConfirm) {
            window.app.showToast('Las contraseñas no coinciden', 'error');
            return;
        }
        userData.password = password;
    }
    
    try {
        console.log('📤 Sending user data:', userData);
        
        let response;
        if (isEdit) {
            console.log('🔄 Making PUT request to update user');
            response = await window.app.apiCall(`/usuarios/${userId}`, 'PUT', userData);
        } else {
            console.log('🔄 Making POST request to create user');
            response = await window.app.apiCall('/usuarios', 'POST', userData);
        }
        
        console.log('📥 Response received:', response);
        
        if (response.success) {
            console.log('✅ User saved successfully');
            window.app.showToast(
                isEdit ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente', 
                'success'
            );
            closeModal('createUserModal');
            window.app.loadUsuarios();
        } else {
            console.error('❌ Failed to save user:', response);
            window.app.showToast('Error guardando usuario', 'error');
        }
    } catch (error) {
        console.error('❌ Error saving user:', error);
        window.app.showToast('Error guardando usuario', 'error');
    }
    
    console.log('🏁 handleUserSubmit finished');
}

async function handleFamilySubmit() {
    console.log('🔥 handleFamilySubmit called!');
    
    const familyId = document.getElementById('familyId').value;
    const isEdit = familyId !== '';
    
    console.log('🏠 Family ID:', familyId);
    console.log('📝 Is Edit:', isEdit);
    
    const familyData = {
        nombre_familia: document.getElementById('familyName').value,
        codigo_familia: document.getElementById('familyCode').value,
        descripcion: document.getElementById('familyDescription').value,
        estado: document.getElementById('familyStatus').value === 'true'
    };
    
    console.log('📤 Sending family data:', familyData);
    
    try {
        let response;
        if (isEdit) {
            console.log('🔄 Making PUT request to update family');
            response = await window.app.apiCall(`/familias/${familyId}`, 'PUT', familyData);
        } else {
            console.log('🔄 Making POST request to create family');
            response = await window.app.apiCall('/familias', 'POST', familyData);
        }
        
        console.log('📥 Response received:', response);
        
        if (response.success) {
            console.log('✅ Family saved successfully');
            window.app.showToast(
                isEdit ? 'Familia actualizada exitosamente' : 'Familia creada exitosamente', 
                'success'
            );
            closeModal('createFamilyModal');
            window.app.loadFamilias();
        } else {
            console.error('❌ Failed to save family:', response);
            window.app.showToast('Error guardando familia', 'error');
        }
    } catch (error) {
        console.error('❌ Error saving family:', error);
        window.app.showToast('Error guardando familia', 'error');
    }
    
    console.log('🏁 handleFamilySubmit finished');
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.app = new HeartGuardApp();
    // Cargar dashboard por defecto
    window.app.loadDashboard();
});
