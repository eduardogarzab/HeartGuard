/**
 * HeartGuard - Superadministrador Dashboard
 * Versión Final Refactorizada y Corregida
 */
console.log('📄 app.js file loaded! - Version: 2025-09-17-21:45');
class HeartGuardApp {
    constructor() {
        this.baseURL = '/admin';
        this.token = localStorage.getItem('heartguard_token');
        const segments = document.getElementById('microservicesSegments');
        this.microservicesTotal = segments ? Number(segments.dataset.total || 4) : 4;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        // --- Formularios ---
        document.getElementById('loginForm')?.addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('familyForm')?.addEventListener('submit', (e) => this.handleFamilySubmit(e));
        document.getElementById('userForm')?.addEventListener('submit', (e) => this.handleUserSubmit(e));
        document.getElementById('editUserForm')?.addEventListener('submit', (e) => this.handleUserSubmit(e, true));

        // --- Navegación y UI ---
        document.querySelectorAll('.menu-item').forEach(item => item.addEventListener('click', (e) => this.handleMenuClick(e)));
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.handleLogout());

        // --- Botones de acción principales ---
        document.querySelector('#usuariosSection .btn-primary')?.addEventListener('click', () => this.openModal('createUserModal'));
        document.querySelector('#familiasSection .btn-primary')?.addEventListener('click', () => this.openModal('createFamilyModal'));

        // --- Búsqueda ---
        document.getElementById('usuarioSearch')?.addEventListener('keyup', (e) => this.searchTable(e.target.value, 'usuariosTable'));
        document.getElementById('familiaSearch')?.addEventListener('keyup', (e) => this.searchTable(e.target.value, 'familiasTable'));

        // --- Modales ---
        document.querySelectorAll('.modal-close, .modal .btn-secondary').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) this.closeModal(modal.id);
            });
        });

        // --- Lógica para menú móvil ---
        document.getElementById('mobileMenuToggle')?.addEventListener('click', () => this.toggleMobileMenu());
        document.getElementById('overlay')?.addEventListener('click', () => this.toggleMobileMenu(false));
    }

    checkAuthStatus() {
        if (this.token) {
            this.showDashboard();
            this.loadSectionData('dashboard');
        } else {
            this.showLogin();
        }
        document.getElementById('loadingScreen').classList.add('hidden');
    }

    // --- Autenticación y Navegación ---

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');

        try {
            errorDiv.style.display = 'none';
            const response = await fetch(`${this.baseURL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.error || 'Credenciales incorrectas');

            this.token = data.token;
            localStorage.setItem('heartguard_token', this.token);
            this.showDashboard();
            this.loadSectionData('dashboard');
            this.showToast('¡Bienvenido de vuelta!', 'success');
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    handleLogout() {
        localStorage.removeItem('heartguard_token');
        this.token = null;
        window.location.reload(); // Recarga la página para ir al login
    }

    showLogin() {
        document.getElementById('loginScreen').style.display = 'flex';
        document.getElementById('dashboard').style.display = 'none';
    }

    showDashboard() {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('dashboard').style.display = 'flex';
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            document.querySelector('.sidebar').classList.add('collapsed');
        }
    }

    handleMenuClick(e) {
        e.preventDefault();
        const menuItem = e.currentTarget;
        document.querySelector('.menu-item.active')?.classList.remove('active');
        menuItem.classList.add('active');
        this.showSection(menuItem.dataset.section);
        
        // Cerrar sidebar en móvil después de la selección
        if (document.body.clientWidth <= 768) {
            this.toggleMobileMenu(false);
        }
    }
    
    showSection(sectionName) {
        document.querySelector('.section.active')?.classList.remove('active');
        document.getElementById(`${sectionName}Section`)?.classList.add('active');
        this.loadSectionData(sectionName);
    }

    // --- Carga y Renderizado de Datos ---
    
    async loadSectionData(sectionName) {
        try {
            const endpointMap = {
                dashboard: '/dashboard', usuarios: '/usuarios', familias: '/familias', alertas: '/alertas', catalogos: '/catalogos', logs: '/logs', microservicios: '/microservicios'
            };
            if (!endpointMap[sectionName]) return;

            const response = await this.apiCall(endpointMap[sectionName]);
            if (!response.success) throw new Error(response.error);

            if (sectionName === 'dashboard') {
                this.renderDashboard(response.data);
            } else if (sectionName === 'microservicios') {
                this.renderMicroservicios(response.data);
            } else {
                this.renderTable(response.data, sectionName);
            }
        } catch (error) {
            this.showToast(`Error al cargar ${sectionName}: ${error.message}`, 'error');
        }
    }
    
    renderDashboard(data) {
        console.log('📊 Dashboard data received:', data);

        const totalUsuarios = Number(data.total_usuarios ?? 0);
        const totalFamilias = Number(data.total_familias ?? 0);
        const alertasTotales = Number(data.alertas_pendientes ?? 0);
        const alertasCriticas = Number(data.alertas_criticas ?? 0);
        const microserviciosActivos = Number(data.microservicios_activos ?? 0);

        const maxBarValue = Math.max(totalUsuarios, totalFamilias, 1);

        this.updateAlertChart(alertasTotales, alertasCriticas);
        this.updateBarChart('usuarios', totalUsuarios, maxBarValue);
        this.updateBarChart('familias', totalFamilias, maxBarValue);
        this.updateMicroservicesChart(microserviciosActivos);

        this.updateSidebarBadges(data);
    }

    updateAlertChart(total, criticos) {
        const circle = document.getElementById('alertCircle');
        const ring = document.getElementById('alertCircleRing');
        const totalLabel = document.getElementById('alertTotalValue');
        const tooltip = document.getElementById('alertTooltip');
        const criticalLabel = document.getElementById('alertCriticalLabel');

        if (!circle || !ring || !totalLabel) return;

        const safeTotal = Number.isFinite(total) ? total : 0;
        const safeCriticos = Number.isFinite(criticos) ? criticos : 0;
        const totalFormatted = safeTotal.toLocaleString('es-MX');
        const critFormatted = safeCriticos.toLocaleString('es-MX');
        const ratio = safeTotal > 0 ? Math.min(safeCriticos / safeTotal, 1) : 0;
        const degrees = ratio * 360;

        totalLabel.textContent = totalFormatted;
        ring.style.background = safeTotal === 0
            ? 'conic-gradient(var(--border-color) 0deg, var(--border-color) 360deg)'
            : `conic-gradient(var(--critical-color) 0deg ${degrees}deg, var(--primary-color) ${degrees}deg 360deg)`;
        circle.classList.toggle('is-empty', safeTotal === 0);

        if (tooltip) {
            tooltip.textContent = safeTotal === 0
                ? 'Sin alertas críticas'
                : `${critFormatted} críticas (${Math.round(ratio * 100)}%)`;
        }

        if (criticalLabel) {
            criticalLabel.textContent = `${critFormatted} críticas`;
        }
    }

    updateBarChart(key, value, maxValue) {
        const bar = document.getElementById(`${key}Bar`);
        const label = document.getElementById(`${key}Value`);
        if (!bar || !label) return;

        const safeValue = Number.isFinite(value) ? value : 0;
        const safeMax = Number.isFinite(maxValue) && maxValue > 0 ? maxValue : Math.max(safeValue, 1);
        const percent = safeValue === 0 ? 0 : Math.min(100, Math.max(15, (safeValue / safeMax) * 100));

        bar.style.height = `${percent}%`;
        bar.style.width = '100%';
        bar.classList.toggle('is-empty', safeValue === 0);
        label.textContent = safeValue.toLocaleString('es-MX');
    }

    updateMicroservicesChart(activos) {
        const container = document.getElementById('microservicesSegments');
        const summary = document.getElementById('microserviciosSummary');
        if (!container || !summary) return;

        const total = Number(container.dataset.total || this.microservicesTotal || 4);
        const normalizedTotal = total > 0 ? total : 4;
        const normalizedActivos = Math.max(0, Math.min(Number.isFinite(activos) ? activos : 0, normalizedTotal));

        container.dataset.total = normalizedTotal;

        if (container.childElementCount !== normalizedTotal) {
            container.innerHTML = '';
            for (let i = 0; i < normalizedTotal; i += 1) {
                const segment = document.createElement('div');
                segment.className = 'segment';
                container.appendChild(segment);
            }
        }

        Array.from(container.children).forEach((segment, index) => {
            segment.classList.toggle('active', index < normalizedActivos);
            segment.classList.toggle('inactive', index >= normalizedActivos);
        });

        summary.textContent = `${normalizedActivos}/${normalizedTotal} activos`;
        this.microservicesTotal = normalizedTotal;
    }
    
    updateSidebarBadges(data) {
        // Update alertas badge in sidebar
        const alertasBadge = document.getElementById('alertasBadge');
        if (alertasBadge) {
            alertasBadge.textContent = data.alertas_pendientes ?? 0;
            console.log('🔔 Updated alertasBadge:', data.alertas_pendientes);
        }
        
        // Update notifications badge if exists
        const notificationsBadge = document.getElementById('notificationsBadge');
        if (notificationsBadge) {
            notificationsBadge.textContent = data.alertas_pendientes ?? 0;
            console.log('🔔 Updated notificationsBadge:', data.alertas_pendientes);
        }
    }

    renderTable(data, type) {
        const tbody = document.getElementById(`${type}Table`);
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!data || data.length === 0) {
            const cols = { usuarios: 6, familias: 5, alertas: 6, catalogos: 5, logs: 5 };
            tbody.innerHTML = `<tr><td colspan="${cols[type]}" class="text-center">No hay datos disponibles</td></tr>`;
            return;
        }

        const rowRenderers = {
            usuarios: user => `<td>${user.id}</td><td>${user.nombre}</td><td>${user.email}</td><td>${user.rol}</td><td>${user.familia_nombre || '-'}</td><td class="table-actions"><button class="action-button" onclick="app.openModal('createUserModal', ${user.id})"><i class="fas fa-pen"></i>Editar</button><button class="action-button danger" onclick="app.deleteItem('usuarios', ${user.id})"><i class="fas fa-trash"></i>Eliminar</button></td>`,
            familias: family => `<td>${family.id}</td><td>${family.nombre_familia}</td><td>${family.total_miembros}</td><td>${new Date(family.fecha_creacion).toLocaleDateString()}</td><td class="table-actions"><button class="action-button" onclick="app.openModal('createFamilyModal', ${family.id})"><i class="fas fa-pen"></i>Editar</button><button class="action-button danger" onclick="app.deleteItem('familias', ${family.id})"><i class="fas fa-trash"></i>Eliminar</button></td>`,
            alertas: alerta => `<td>${alerta.id}</td><td>${alerta.usuario_nombre || '-'}</td><td>${alerta.tipo || '-'}</td><td>${alerta.descripcion || '-'}</td><td>${alerta.nivel || 'Media'}</td><td>${new Date(alerta.fecha).toLocaleDateString()}</td>`,
            catalogos: catalogo => `<td>${catalogo.id}</td><td>${catalogo.tipo || '-'}</td><td>${catalogo.clave || '-'}</td><td>${catalogo.valor || '-'}</td><td class="table-actions"><button class="action-button" onclick="app.openModal('createCatalogModal', ${catalogo.id})"><i class="fas fa-pen"></i>Editar</button><button class="action-button danger" onclick="app.deleteItem('catalogos', ${catalogo.id})"><i class="fas fa-trash"></i>Eliminar</button></td>`,
            logs: log => `<td>${log.id}</td><td>${log.usuario_nombre || 'Sistema'}</td><td>${log.accion || '-'}</td><td>${log.detalle || '-'}</td><td>${new Date(log.fecha).toLocaleString()}</td>`,
        };
        
        data.forEach(item => {
            const row = tbody.insertRow();
            row.innerHTML = rowRenderers[type](item);
        });
    }

    // --- Lógica de Modales ---

    async openModal(modalId, itemId = null) {
        console.log('🔥🔥🔥 openModal called:', { modalId, itemId });
        console.log('🔥🔥🔥 this context:', this);
        
        const modal = document.getElementById(modalId);
        console.log('🔍 Modal element:', modal);
        if (!modal) {
            console.error('❌ Modal not found:', modalId);
            return;
        }
        
        const form = modal.querySelector('form');
        console.log('🔍 Form element:', form);
        if (!form) {
            console.error('❌ Form not found in modal:', modalId);
            return;
        }
        
        form.reset();
        const isEdit = Boolean(itemId);
        console.log('📋 Modal setup:', { modalId, itemId, isEdit });

        if (modalId === 'createFamilyModal') {
            modal.querySelector('#familyModalTitle').textContent = isEdit ? 'Editar Familia' : 'Crear Nueva Familia';
            modal.querySelector('#familySubmitText').textContent = isEdit ? 'Actualizar Familia' : 'Crear Familia';
            modal.querySelector('#familyId').value = isEdit ? itemId : ''; // LA CORRECCIÓN CLAVE
            if (isEdit) await this.loadAndFillForm('familias', itemId, form);
        } else if (modalId.includes('UserModal')) {
            await this.loadFamiliasForSelect('userFamily');
            if(isEdit) {
                 modal.querySelector('#userId').value = itemId;
                 console.log('✏️ Set userId field for edit mode:', modal.querySelector('#userId').value);
                 await this.loadAndFillForm('usuarios', itemId, form);
                 // Hide password fields when editing
                 const passwordRow = modal.querySelector('#passwordRow');
                 if (passwordRow) {
                     passwordRow.style.display = 'none';
                     modal.querySelector('#userPassword').removeAttribute('required');
                     modal.querySelector('#userPasswordConfirm').removeAttribute('required');
                 }
                 // Update title and button text
                 modal.querySelector('#userModalTitle').textContent = 'Editar Usuario';
                 modal.querySelector('#userSubmitText').textContent = 'Actualizar Usuario';
            } else {
                 // Clear userId field explicitly for create mode
                 modal.querySelector('#userId').value = '';
                 console.log('🧹 Cleared userId field for create mode:', modal.querySelector('#userId').value);
                 
                 // Show password fields when creating
                 const passwordRow = modal.querySelector('#passwordRow');
                 if (passwordRow) {
                     passwordRow.style.display = 'grid';
                     modal.querySelector('#userPassword').setAttribute('required', 'required');
                     modal.querySelector('#userPasswordConfirm').setAttribute('required', 'required');
                 }
                 // Update title and button text
                 modal.querySelector('#userModalTitle').textContent = 'Crear Nuevo Usuario';
                 modal.querySelector('#userSubmitText').textContent = 'Crear Usuario';
            }
        } else if (modalId === 'createCatalogModal') {
            this.resetCatalogForm();
            if (itemId) {
                this.loadCatalogData(itemId);
            }
        }
        modal.classList.add('active');
        console.log('✅ Modal opened successfully:', modalId);
        console.log('🔍 Modal classList:', modal.classList);
    }

    closeModal(modalId) {
        document.getElementById(modalId)?.classList.remove('active');
    }

    async loadAndFillForm(type, id, form) {
        try {
            const response = await this.apiCall(`/${type}/${id}`);
            if (!response.success) throw new Error(response.error);
            const data = response.data;
            const fieldMap = {
                familias: { 'familyName': data.nombre_familia, 'familyCode': data.codigo_familia, 'familyDescription': data.descripcion },
                usuarios: { 'userName': data.nombre, 'userEmail': data.email, 'userRole': data.rol_nombre, 'userFamily': data.familia_id }
            };
            Object.entries(fieldMap[type]).forEach(([fieldId, value]) => {
                const el = form.querySelector(`#${fieldId}`);
                if (el) el.value = value ?? '';
            });
        } catch(error) {
            this.showToast(`Error cargando datos para editar: ${error.message}`, 'error');
        }
    }

    async loadFamiliasForSelect(selectId) {
        const select = document.getElementById(selectId);
        if(!select) return;
        select.innerHTML = '<option value="">Sin familia asignada</option>';
        const response = await this.apiCall('/familias');
        if (response.success) {
            response.data.forEach(familia => select.innerHTML += `<option value="${familia.id}">${familia.nombre_familia}</option>`);
        }
    }

    // --- Lógica de Formularios (CRUD) ---

    async handleFamilySubmit(e) {
        e.preventDefault();
        console.log('🔥 handleFamilySubmit called!');
        console.log('📋 Event target:', e.target);
        
        const form = e.target;
        const id = form.querySelector('#familyId').value || null;
        const data = {
            nombre_familia: form.querySelector('#familyName').value,
            codigo_familia: form.querySelector('#familyCode').value,
            descripcion: form.querySelector('#familyDescription').value,
        };
        
        console.log('📤 Family data:', { id, data });
        
        await this.saveItem('familias', id, data);
        this.closeModal('createFamilyModal');
    }
    
    async handleUserSubmit(e, isEdit = false) {
        e.preventDefault();
        console.log('🔥🔥🔥 handleUserSubmit called!', { isEdit });
        console.log('📋 Event target:', e.target);
        
        const form = e.target;
        const userId = form.querySelector('#userId')?.value;
        const isEditMode = isEdit || userId !== '';
        
        console.log('📋 Form data:', {
            userId: userId,
            userName: form.querySelector('#userName')?.value,
            userEmail: form.querySelector('#userEmail')?.value,
            isEditMode: isEditMode
        });
        
        const userData = {
            nombre: form.querySelector('#userName')?.value,
            email: form.querySelector('#userEmail')?.value,
            rol: form.querySelector('#userRole')?.value,
            familia_id: parseInt(form.querySelector('#userFamily')?.value || '0'),
            relacion: 'miembro'
        };
        
        // Solo incluir contraseña para crear
        if (!isEditMode) {
            const password = form.querySelector('#userPassword')?.value;
            const passwordConfirm = form.querySelector('#userPasswordConfirm')?.value;
            
            if (!password) {
                this.showToast('La contraseña es requerida', 'error');
                return;
            }
            
            if (password !== passwordConfirm) {
                this.showToast('Las contraseñas no coinciden', 'error');
                return;
            }
            
            userData.password = password;
        }
        
        console.log('📤 Sending user data:', userData);
        
        try {
            const response = await this.apiCall(
                isEditMode ? `/usuarios/${userId}` : '/usuarios',
                isEditMode ? 'PUT' : 'POST',
                userData
            );
            
            console.log('📥 Response received:', response);
            
            if (response.success) {
                this.showToast(`Usuario ${isEditMode ? 'actualizado' : 'creado'} exitosamente`, 'success');
                this.closeModal('createUserModal');
                this.loadSectionData('usuarios');
            } else {
                this.showToast(`Error ${isEditMode ? 'actualizando' : 'creando'} usuario`, 'error');
            }
        } catch (error) {
            console.error('❌ Error saving user:', error);
            this.showToast(`Error ${isEditMode ? 'actualizando' : 'creando'} usuario`, 'error');
        }
    }

    async saveItem(type, id, data) {
        const isEdit = id !== null;
        try {
            const response = await this.apiCall(isEdit ? `/${type}/${id}` : `/${type}`, isEdit ? 'PUT' : 'POST', data);
            if (!response.success) throw new Error(response.error);
            this.showToast(`Registro ${isEdit ? 'actualizado' : 'creado'} con éxito`, 'success');
            this.loadSectionData(type);
        } catch (error) {
            this.showToast(`Error al guardar: ${error.message}`, 'error');
        }
    }

    async deleteItem(type, id) {
        if (confirm(`¿Estás seguro de que quieres eliminar este registro?`)) {
            try {
                const response = await this.apiCall(`/${type}/${id}`, 'DELETE');
                if (!response.success) throw new Error(response.error);
                this.showToast('Registro eliminado con éxito', 'success');
                this.loadSectionData(type);
            } catch (error) {
                this.showToast(`Error al eliminar: ${error.message}`, 'error');
            }
        }
    }


    

    // --- Funciones para Catálogos ---
    
    async handleCatalogSubmit() {
        console.log('📋 Submitting catalog form...');
        const form = document.getElementById('catalogForm');
        const formData = new FormData(form);
        
        const data = {
            tipo: formData.get('tipo'),
            clave: formData.get('clave'),
            valor: formData.get('valor'),
            descripcion: formData.get('descripcion'),
            activo: document.getElementById('catalogActivo').checked
        };
        
        const catalogId = formData.get('id');
        const isEdit = Boolean(catalogId);
        
        try {
            let response;
            if (isEdit) {
                console.log('✏️ Updating catalog:', catalogId);
                response = await this.apiCall(`/catalogos/${catalogId}`, 'PUT', data);
                this.showToast('Catálogo actualizado con éxito', 'success');
            } else {
                console.log('📝 Creating new catalog...');
                response = await this.apiCall('/catalogos', 'POST', data);
                this.showToast('Catálogo creado con éxito', 'success');
            }
            
            if (!response.success) throw new Error(response.error);
            
            this.closeModal('createCatalogModal');
            this.loadSectionData('catalogos');
            
        } catch (error) {
            console.error('❌ Error saving catalog:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        }
    }
    
    async loadCatalogData(id) {
        console.log('📋 Loading catalog data for ID:', id);
        try {
            const response = await this.apiCall(`/catalogos/${id}`);
            if (!response.success) throw new Error(response.error);
            
            const catalog = response.data;
            document.getElementById('catalogId').value = catalog.id;
            document.getElementById('catalogType').value = catalog.tipo;
            document.getElementById('catalogClave').value = catalog.clave;
            document.getElementById('catalogValor').value = catalog.valor;
            document.getElementById('catalogDescripcion').value = catalog.descripcion || '';
            document.getElementById('catalogActivo').checked = catalog.activo;
            
            document.getElementById('catalogModalTitle').textContent = 'Editar Catálogo';
            document.getElementById('catalogSubmitBtn').textContent = 'Actualizar Catálogo';
            
        } catch (error) {
            console.error('❌ Error loading catalog data:', error);
            this.showToast(`Error al cargar datos: ${error.message}`, 'error');
        }
    }
    
    resetCatalogForm() {
        console.log('🔄 Resetting catalog form...');
        const form = document.getElementById('catalogForm');
        form.reset();
        document.getElementById('catalogId').value = '';
        document.getElementById('catalogActivo').checked = true;
        document.getElementById('catalogModalTitle').textContent = 'Nuevo Catálogo';
        document.getElementById('catalogSubmitBtn').textContent = 'Crear Catálogo';
    }

    // --- Funciones para Microservicios ---
    
    async renderMicroservicios(data) {
        console.log('🖥️ Rendering enterprise microservices dashboard...', data);
        
        // Actualizar timestamp
        this.updateLastRefreshTime();
        
        // SIEMPRE usar datos dummy coloridos para la demo
        console.log('📊 Usando datos dummy coloridos para la demo');
        const dummyData = [
            { 
                id: 1, 
                nombre: 'HeartGuard API', 
                estado: 'activo',
                responseTime: 45,
                uptime: 99.9,
                requests: 1250
            },
            { 
                id: 2, 
                nombre: 'Authentication Service', 
                estado: 'activo',
                responseTime: 23,
                uptime: 99.8,
                requests: 890
            },
            { 
                id: 3, 
                nombre: 'Metrics Service', 
                estado: 'degraded',
                responseTime: 156,
                uptime: 98.5,
                requests: 450
            },
            { 
                id: 4, 
                nombre: 'Notification Service', 
                estado: 'activo',
                responseTime: 67,
                uptime: 99.7,
                requests: 320
            },
            { 
                id: 5, 
                nombre: 'Database Service', 
                estado: 'activo',
                responseTime: 12,
                uptime: 99.95,
                requests: 2100
            },
            { 
                id: 6, 
                nombre: 'Cache Service', 
                estado: 'outage',
                responseTime: 0,
                uptime: 0,
                requests: 0
            }
        ];
        
        // SIEMPRE usar el fallback para mostrar datos dummy visibles
        console.log('🎯 Usando fallback dashboard para garantizar visibilidad');
        this.renderFallbackDashboard();
    }

    renderFallbackDashboard() {
        console.log('🎯 Rendering fallback dashboard');
        
        this.updateAlertChart(0, 0);
        this.updateBarChart('usuarios', 0, 1);
        this.updateBarChart('familias', 0, 1);
        this.updateMicroservicesChart(0);
        this.updateSidebarBadges({ alertas_pendientes: 0, alertas_criticas: 0 });

        // Actualizar el status del sistema
        const systemStatusDot = document.getElementById('systemStatusDot');
        const systemStatusLabel = document.getElementById('systemStatusDetail');
        if (systemStatusDot) {
            systemStatusDot.className = 'status-dot operational';
        }
        if (systemStatusLabel) {
            systemStatusLabel.textContent = 'Todos los servicios están funcionando correctamente';
        }
        
        // Renderizar servicios dummy
        const container = document.getElementById('servicesGrid');
        if (container) {
            container.innerHTML = `
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <div class="service-icon">
                                <i class="fas fa-server"></i>
                            </div>
                            HeartGuard API
                        </div>
                        <div class="service-status operational">
                            <div class="status-dot operational"></div>
                            Operacional
                        </div>
                    </div>
                    <div class="service-metrics">
                        <div class="metric">
                            <div class="metric-value">45ms</div>
                            <div class="metric-label">Tiempo de respuesta</div>
                            <div class="metric-trend trend-stable">
                                <i class="fas fa-minus"></i>
                                Estable
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">99.9%</div>
                            <div class="metric-label">Disponibilidad</div>
                            <div class="metric-trend trend-up">
                                <i class="fas fa-arrow-up"></i>
                                Mejorando
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <div class="service-icon">
                                <i class="fas fa-shield-alt"></i>
                            </div>
                            Authentication Service
                        </div>
                        <div class="service-status operational">
                            <div class="status-dot operational"></div>
                            Operacional
                        </div>
                    </div>
                    <div class="service-metrics">
                        <div class="metric">
                            <div class="metric-value">23ms</div>
                            <div class="metric-label">Tiempo de respuesta</div>
                            <div class="metric-trend trend-up">
                                <i class="fas fa-arrow-up"></i>
                                Mejorando
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">99.8%</div>
                            <div class="metric-label">Disponibilidad</div>
                            <div class="metric-trend trend-stable">
                                <i class="fas fa-minus"></i>
                                Estable
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <div class="service-icon">
                                <i class="fas fa-chart-line"></i>
                            </div>
                            Metrics Service
                        </div>
                        <div class="service-status operational">
                            <div class="status-dot operational"></div>
                            Operacional
                        </div>
                    </div>
                    <div class="service-metrics">
                        <div class="metric">
                            <div class="metric-value">89ms</div>
                            <div class="metric-label">Tiempo de respuesta</div>
                            <div class="metric-trend trend-up">
                                <i class="fas fa-arrow-up"></i>
                                Mejorando
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">99.2%</div>
                            <div class="metric-label">Disponibilidad</div>
                            <div class="metric-trend trend-up">
                                <i class="fas fa-arrow-up"></i>
                                Mejorando
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <div class="service-icon">
                                <i class="fas fa-bell"></i>
                            </div>
                            Notification Service
                        </div>
                        <div class="service-status operational">
                            <div class="status-dot operational"></div>
                            Operacional
                        </div>
                    </div>
                    <div class="service-metrics">
                        <div class="metric">
                            <div class="metric-value">67ms</div>
                            <div class="metric-label">Tiempo de respuesta</div>
                            <div class="metric-trend trend-stable">
                                <i class="fas fa-minus"></i>
                                Estable
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">99.7%</div>
                            <div class="metric-label">Disponibilidad</div>
                            <div class="metric-trend trend-up">
                                <i class="fas fa-arrow-up"></i>
                                Mejorando
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Renderizar métricas
        const metricsContainer = document.getElementById('metricsGrid');
        if (metricsContainer) {
            metricsContainer.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">2,910</div>
                    <div class="metric-label">Requests/min</div>
                    <div class="metric-description">Total de solicitudes por minuto</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">73ms</div>
                    <div class="metric-label">Tiempo promedio</div>
                    <div class="metric-description">Tiempo de respuesta promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">99.5%</div>
                    <div class="metric-label">Disponibilidad</div>
                    <div class="metric-description">Promedio de disponibilidad</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">4/4</div>
                    <div class="metric-label">Servicios activos</div>
                    <div class="metric-description">Servicios funcionando correctamente</div>
                </div>
            `;
        }
    }

    updateLastRefreshTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        
        const lastUpdateElement = document.getElementById('lastUpdateTime');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = `Última actualización: ${timeString}`;
        }
    }

    renderSystemStatus(services) {
        console.log('🎯 renderSystemStatus called with:', services);
        const systemStatusDot = document.getElementById('systemStatusDot');
        const systemStatusLabel = document.getElementById('systemStatusDetail');
        
        console.log('🎯 systemStatusDot:', systemStatusDot);
        console.log('🎯 systemStatusLabel:', systemStatusLabel);
        
        if (!systemStatusDot || !systemStatusLabel) {
            console.error('❌ Elementos del sistema status no encontrados');
            return;
        }
        
        // Calcular estado general del sistema
        const operationalServices = services.filter(s => s.estado === 'activo').length;
        const degradedServices = services.filter(s => s.estado === 'degraded').length;
        const outageServices = services.filter(s => s.estado === 'inactivo' || s.estado === 'outage').length;
        
        let systemStatus, statusClass, statusMessage;
        
        if (outageServices > 0) {
            systemStatus = 'outage';
            statusClass = 'outage';
            statusMessage = `${outageServices} servicio(s) fuera de línea`;
        } else if (degradedServices > 0) {
            systemStatus = 'degraded';
            statusClass = 'degraded';
            statusMessage = `${degradedServices} servicio(s) con rendimiento degradado`;
        } else {
            systemStatus = 'operational';
            statusClass = 'operational';
            statusMessage = 'Todos los servicios están funcionando correctamente';
        }
        
        systemStatusDot.className = `status-dot ${statusClass}`;
        systemStatusLabel.textContent = statusMessage;
    }

    renderServicesGrid(services) {
        console.log('🎯 renderServicesGrid called with:', services);
        const container = document.getElementById('servicesGrid');
        console.log('🎯 servicesGrid container:', container);
        if (!container) {
            console.error('❌ Container servicesGrid no encontrado');
            return;
        }
        
        container.innerHTML = services.map(service => {
            const statusClass = this.getStatusClass(service.estado);
            const statusText = this.getStatusText(service.estado);
            const icon = this.getServiceIcon(service.nombre);
            
            return `
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <div class="service-icon">
                                <i class="${icon}"></i>
                            </div>
                            ${service.nombre}
                        </div>
                        <div class="service-status ${statusClass}">
                            <div class="status-dot ${statusClass}"></div>
                            ${statusText}
                        </div>
                    </div>
                    <div class="service-metrics">
                        <div class="metric">
                            <div class="metric-value">${service.responseTime || 0}ms</div>
                            <div class="metric-label">Tiempo de respuesta</div>
                            <div class="metric-trend ${this.getTrendClass('response', service.responseTime)}">
                                <i class="fas ${this.getTrendIcon('response', service.responseTime)}"></i>
                                ${this.getTrendText('response', service.responseTime)}
                            </div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${service.uptime || 0}%</div>
                            <div class="metric-label">Disponibilidad</div>
                            <div class="metric-trend ${this.getTrendClass('uptime', service.uptime)}">
                                <i class="fas ${this.getTrendIcon('uptime', service.uptime)}"></i>
                                ${this.getTrendText('uptime', service.uptime)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderPerformanceMetrics(services) {
        console.log('🎯 renderPerformanceMetrics called with:', services);
        const container = document.getElementById('metricsGrid');
        console.log('🎯 metricsGrid container:', container);
        if (!container) {
            console.error('❌ Container metricsGrid no encontrado');
            return;
        }
        
        // Calcular métricas generales
        const totalRequests = services.reduce((sum, s) => sum + (s.requests || 0), 0);
        const avgResponseTime = services.reduce((sum, s) => sum + (s.responseTime || 0), 0) / services.length;
        const avgUptime = services.reduce((sum, s) => sum + (s.uptime || 0), 0) / services.length;
        const operationalCount = services.filter(s => s.estado === 'activo').length;
        
        container.innerHTML = `
            <div class="metric-card">
                <div class="metric-value">${totalRequests.toLocaleString()}</div>
                <div class="metric-label">Requests/min</div>
                <div class="metric-description">Total de solicitudes por minuto</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${Math.round(avgResponseTime)}ms</div>
                <div class="metric-label">Tiempo promedio</div>
                <div class="metric-description">Tiempo de respuesta promedio</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${avgUptime.toFixed(1)}%</div>
                <div class="metric-label">Disponibilidad</div>
                <div class="metric-description">Promedio de disponibilidad</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${operationalCount}/${services.length}</div>
                <div class="metric-label">Servicios activos</div>
                <div class="metric-description">Servicios funcionando correctamente</div>
            </div>
        `;
    }

    getStatusClass(estado) {
        switch(estado) {
            case 'activo': return 'operational';
            case 'degraded': return 'degraded';
            case 'inactivo':
            case 'outage': return 'outage';
            default: return 'operational';
        }
    }

    getStatusText(estado) {
        switch(estado) {
            case 'activo': return 'Operacional';
            case 'degraded': return 'Degradado';
            case 'inactivo':
            case 'outage': return 'Fuera de línea';
            default: return 'Operacional';
        }
    }

    getServiceIcon(serviceName) {
        if (serviceName.toLowerCase().includes('api')) return 'fas fa-server';
        if (serviceName.toLowerCase().includes('auth')) return 'fas fa-shield-alt';
        if (serviceName.toLowerCase().includes('metric')) return 'fas fa-chart-line';
        if (serviceName.toLowerCase().includes('notification')) return 'fas fa-bell';
        return 'fas fa-cog';
    }

    getTrendClass(type, value) {
        // Lógica simple para determinar tendencias
        if (type === 'response') {
            return value < 100 ? 'trend-stable' : 'trend-up';
        }
        if (type === 'uptime') {
            return value > 99 ? 'trend-up' : value > 95 ? 'trend-stable' : 'trend-down';
        }
        return 'trend-stable';
    }

    getTrendIcon(type, value) {
        const trendClass = this.getTrendClass(type, value);
        switch(trendClass) {
            case 'trend-up': return 'fa-arrow-up';
            case 'trend-down': return 'fa-arrow-down';
            default: return 'fa-minus';
        }
    }

    getTrendText(type, value) {
        const trendClass = this.getTrendClass(type, value);
        switch(trendClass) {
            case 'trend-up': return 'Mejorando';
            case 'trend-down': return 'Empeorando';
            default: return 'Estable';
        }
    }
    
    createSimpleChart(container, data) {
        console.log('🎨 Creando gráfica simple...', data);
        
        // Crear HTML básico
        container.innerHTML = `
            <div class="microservices-chart-container">
                <h3>Estado de Microservicios en el Tiempo</h3>
                <div class="chart-wrapper">
                    <canvas id="microserviciosChart" width="800" height="400"></canvas>
                </div>
                <div class="chart-controls">
                    <button class="action-button" onclick="app.refreshMicroservicios()">
                        <i class="fas fa-rotate"></i> Actualizar
                    </button>
                </div>
            </div>
        `;
        
        // Esperar un momento para que el DOM se actualice
        setTimeout(() => {
            this.initSimpleChart(data);
        }, 100);
    }
    
    initSimpleChart(data) {
        console.log('🎨 Inicializando gráfica simple con datos:', data);
        const canvas = document.getElementById('microserviciosChart');
        if (!canvas) {
            console.error('❌ Canvas no encontrado después de crear HTML');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Datos simples para la demo
        const labels = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00'];
        
        // Colores diferentes para cada microservicio
        const colors = [
            '#FF6B6B', // Rojo coral
            '#4ECDC4', // Verde azulado
            '#45B7D1'  // Azul claro
        ];
        
        // Crear datasets con patrón de accidente
        const datasets = data.map((microservicio, index) => {
            const color = colors[index] || '#666666';
            
            // Patrón: 2 arriba, 1 abajo (simulando accidente)
            let chartData;
            if (index === 0) {
                // Microservicio 1: ON, ON, OFF, ON, ON, OFF, ON
                chartData = [1, 1, 0, 1, 1, 0, 1];
            } else if (index === 1) {
                // Microservicio 2: ON, ON, ON, OFF, ON, ON, ON
                chartData = [1, 1, 1, 0, 1, 1, 1];
            } else {
                // Microservicio 3: ON, OFF, ON, ON, OFF, ON, ON
                chartData = [1, 0, 1, 1, 0, 1, 1];
            }
            
            console.log(`📊 Dataset ${index}:`, {
                nombre: microservicio.nombre,
                color,
                data: chartData
            });
            
            return {
                label: microservicio.nombre,
                data: chartData,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 4,
                fill: false,
                tension: 0,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            };
        });
        
        // Verificar que Chart esté disponible
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js no está cargado');
            return;
        }
        
        // Crear la gráfica
        try {
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: -0.1,
                            max: 1.1,
                            ticks: {
                                stepSize: 1,
                                callback: function(value) {
                                    return value === 1 ? 'ON' : value === 0 ? 'OFF' : '';
                                },
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                display: false
                            }
                        },
                        x: {
                            grid: {
                                display: true,
                                color: '#e0e0e0'
                            },
                            ticks: {
                                font: {
                                    size: 12
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                },
                                padding: 20
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const status = value === 1 ? '🟢 ENCENDIDO' : '🔴 APAGADO';
                                    return context.dataset.label + ': ' + status;
                                }
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Gráfica mejorada creada exitosamente');
            window.microserviciosChart = chart;
        } catch (error) {
            console.error('❌ Error creando gráfica:', error);
        }
    }
    
    
    
    generateSimpleStatusData(isActive) {
        // Generar datos dummy más realistas para la demo
        const data = [];
        const hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00'];
        
        // Crear patrones predefinidos para cada microservicio
        const patterns = {
            'Android API Service': [1, 1, 1, 0, 0, 1, 1], // Se cae en la madrugada
            'Flask Metrics Service': [1, 1, 0, 0, 1, 1, 1], // Problemas en la noche
            'Notification Service': [0, 1, 1, 1, 1, 0, 1]  // Inestable
        };
        
        // Usar el patrón basado en el estado inicial
        let pattern;
        if (isActive) {
            pattern = patterns['Android API Service'];
        } else {
            pattern = Math.random() < 0.5 ? patterns['Flask Metrics Service'] : patterns['Notification Service'];
        }
        
        return pattern;
    }
    
    async checkMicroservicioHealth(id) {
        console.log('🔍 Checking microservicio health:', id);
        try {
            const response = await this.apiCall(`/microservicios/${id}/health`, 'GET');
            if (response.success) {
                this.showToast('Microservicio verificado exitosamente', 'success');
                this.loadSectionData('microservicios');
            } else {
                this.showToast('Error al verificar microservicio', 'error');
            }
        } catch (error) {
            console.error('❌ Error checking microservicio health:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        }
    }
    
    showMicroservicioChart(id, nombre) {
        console.log('📊 Showing microservicio chart:', id, nombre);
        this.showToast(`Gráfica detallada de ${nombre} - Función en desarrollo`, 'info');
    }
    
    updateMicroserviciosChart() {
        console.log('📊 Updating microservicios chart...');
        const timeRange = document.getElementById('timeRangeSelect').value;
        this.showToast(`Actualizando gráfica para ${timeRange}`, 'info');
        // Aquí se actualizaría la gráfica con el nuevo rango de tiempo
    }
    
    refreshMicroserviciosChart() {
        console.log('🔄 Refreshing microservicios chart...');
        this.loadSectionData('microservicios');
        this.showToast('Gráfica actualizada', 'success');
    }
    
    async refreshMicroservicios() {
        console.log('🔄 Refreshing microservicios...');
        await this.loadSectionData('microservicios');
        this.showToast('Microservicios actualizados', 'success');
    }

    // --- Utilidades ---
    searchTable(searchTerm, tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;
        const filter = searchTerm.toUpperCase();
        const rows = table.getElementsByTagName("tr");
        for (let i = 0; i < rows.length; i++) {
            const cells = rows[i].getElementsByTagName("td");
            let found = false;
            for (let j = 0; j < cells.length; j++) {
                if (cells[j]) {
                    if (cells[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
            }
            rows[i].style.display = found ? "" : "none";
        }
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const options = { method, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.token}` } };
        if (data) options.body = JSON.stringify(data);
        const response = await fetch(`${this.baseURL}${endpoint}`, options);
        if (response.status === 401) this.handleLogout();
        return response.json();
    }
    
    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
    
    toggleMobileMenu(forceOpen = null) {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.getElementById('overlay');
        const isOpen = sidebar.classList.contains('is-open');

        if (forceOpen === true || (forceOpen === null && !isOpen)) {
            sidebar.classList.add('is-open');
            overlay.classList.add('active');
        } else {
            sidebar.classList.remove('is-open');
            overlay.classList.remove('active');
        }
    }
}

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded - Initializing HeartGuardApp');
    window.app = new HeartGuardApp();
    console.log('✅ HeartGuardApp initialized:', window.app);
    
    // Verificar que los elementos existan
    const nuevoUsuarioBtn = document.querySelector('button[onclick*="createUserModal"]');
    console.log('🔍 Nuevo Usuario button found:', nuevoUsuarioBtn);
    
    const createUserModal = document.getElementById('createUserModal');
    console.log('🔍 createUserModal found:', createUserModal);
    
    // Agregar event listener adicional para debug
    if (nuevoUsuarioBtn) {
        nuevoUsuarioBtn.addEventListener('click', function(e) {
            console.log('🔥 Button clicked!', e);
            console.log('🔥 app object:', window.app);
            console.log('🔥 app.openModal:', window.app.openModal);
            
            // Probar abrir modal directamente
            try {
                console.log('🔥 Calling app.openModal directly...');
                window.app.openModal('createUserModal');
            } catch (error) {
                console.error('❌ Error calling openModal:', error);
            }
        });
    }
    
    // Función global de prueba
    window.testOpenModal = function() {
        console.log('🧪 Testing openModal...');
        const modal = document.getElementById('createUserModal');
        console.log('🧪 Modal found:', modal);
        if (modal) {
            modal.classList.add('active');
            console.log('🧪 Modal class added');
        }
    };
});
