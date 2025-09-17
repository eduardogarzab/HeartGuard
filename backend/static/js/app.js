/**
 * HeartGuard - Superadministrador Dashboard
 * Versión Final Refactorizada y Corregida
 */
console.log('📄 app.js file loaded! - Version: 2025-09-17-21:45');
class HeartGuardApp {
    constructor() {
        this.baseURL = '/admin';
        this.token = localStorage.getItem('heartguard_token');
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
        document.getElementById('sidebarToggle')?.addEventListener('click', () => this.toggleSidebar());
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
                dashboard: '/dashboard', usuarios: '/usuarios', familias: '/familias', alertas: '/alertas', ubicaciones: '/ubicaciones', catalogos: '/catalogos', logs: '/logs', microservicios: '/microservicios'
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
        Object.entries({
            'totalUsuarios': data.total_usuarios, 'totalFamilias': data.total_familias,
            'alertasPendientes': data.alertas_pendientes, 'alertasCriticas': data.alertas_criticas,
        }).forEach(([id, value]) => {
            const el = document.getElementById(id);
            console.log(`🔍 Element ${id}:`, el, 'Value:', value);
            if(el) el.textContent = value ?? 0;
        });
        
        // Update sidebar badges
        this.updateSidebarBadges(data);
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
            const cols = { usuarios: 7, familias: 6, alertas: 8, ubicaciones: 8, catalogos: 5, logs: 5 };
            tbody.innerHTML = `<tr><td colspan="${cols[type]}" class="text-center">No hay datos disponibles</td></tr>`;
            return;
        }

        const rowRenderers = {
            usuarios: user => `<td>${user.id}</td><td>${user.nombre}</td><td>${user.email}</td><td>${user.rol}</td><td>${user.familia_nombre || '-'}</td><td><span class="badge ${user.estado ? 'badge-success' : 'badge-error'}">${user.estado ? 'Activo' : 'Inactivo'}</span></td><td><button class="btn btn-sm" onclick="app.openModal('createUserModal', ${user.id})"><i class="fas fa-edit"></i></button><button class="btn btn-sm btn-error" onclick="app.deleteItem('usuarios', ${user.id})"><i class="fas fa-trash"></i></button></td>`,
            familias: family => `<td>${family.id}</td><td>${family.nombre_familia}</td><td>${family.total_miembros}</td><td>${new Date(family.fecha_creacion).toLocaleDateString()}</td><td><span class="badge ${family.estado ? 'badge-success' : 'badge-error'}">${family.estado ? 'Activa' : 'Inactiva'}</span></td><td><button class="btn btn-sm" onclick="app.openModal('createFamilyModal', ${family.id})"><i class="fas fa-edit"></i></button><button class="btn btn-sm btn-error" onclick="app.deleteItem('familias', ${family.id})"><i class="fas fa-trash"></i></button></td>`,
            alertas: alerta => `<td>${alerta.id}</td><td>${alerta.usuario_nombre || '-'}</td><td>${alerta.tipo || '-'}</td><td>${alerta.descripcion || '-'}</td><td>${alerta.nivel || 'Media'}</td><td>${new Date(alerta.fecha).toLocaleDateString()}</td><td><span class="badge ${alerta.atendida ? 'badge-success' : 'badge-error'}">${alerta.atendida ? 'Atendida' : 'Pendiente'}</span></td><td><button class="btn btn-sm" onclick="app.atenderAlerta(${alerta.id})"><i class="fas fa-check"></i></button><button class="btn btn-sm btn-error" onclick="app.deleteItem('alertas', ${alerta.id})"><i class="fas fa-trash"></i></button></td>`,
            ubicaciones: ubicacion => `<td>${ubicacion.id}</td><td>${ubicacion.usuario_nombre || '-'}</td><td>${ubicacion.latitud || '-'}</td><td>${ubicacion.longitud || '-'}</td><td>${ubicacion.precision_metros || '-'}m</td><td>${ubicacion.fuente || '-'}</td><td>${new Date(ubicacion.ubicacion_timestamp).toLocaleString()}</td><td><button class="btn btn-sm btn-info" onclick="app.viewUbicacionOnMap(${ubicacion.id})" title="Ver en Mapa"><i class="fas fa-map"></i></button></td>`,
            catalogos: catalogo => `<td>${catalogo.id}</td><td>${catalogo.tipo || '-'}</td><td>${catalogo.clave || '-'}</td><td>${catalogo.valor || '-'}</td><td><button class="btn btn-sm" onclick="app.openModal('createCatalogModal', ${catalogo.id})"><i class="fas fa-edit"></i></button><button class="btn btn-sm btn-error" onclick="app.deleteItem('catalogos', ${catalogo.id})"><i class="fas fa-trash"></i></button></td>`,
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
                familias: { 'familyName': data.nombre_familia, 'familyCode': data.codigo_familia, 'familyDescription': data.descripcion, 'familyStatus': String(data.estado) },
                usuarios: { 'userName': data.nombre, 'userEmail': data.email, 'userRole': data.rol_nombre, 'userFamily': data.familia_id, 'userStatus': String(data.estado) }
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
            estado: form.querySelector('#familyStatus').value === 'true',
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
            estado: form.querySelector('#userStatus')?.value === 'true',
            familia_id: parseInt(form.querySelector('#userFamily')?.value) || null,
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

    async atenderAlerta(id) {
        try {
            const data = {
                atendido_por: 1 // ID del superadmin (por ahora hardcodeado)
            };
            const response = await this.apiCall(`/alertas/${id}/atender`, 'PUT', data);
            if (!response.success) throw new Error(response.error);
            this.showToast('Alerta atendida con éxito', 'success');
            this.loadSectionData('alertas');
            // Update dashboard to refresh badges
            this.loadSectionData('dashboard');
        } catch (error) {
            this.showToast(`Error al atender alerta: ${error.message}`, 'error');
        }
    }

    // --- Funciones para Ubicaciones ---
    
    async refreshUbicaciones() {
        console.log('🔄 Refreshing ubicaciones...');
        await this.loadSectionData('ubicaciones');
        this.showToast('Ubicaciones actualizadas', 'success');
    }
    
    // --- Funciones para Ubicaciones Históricas ---
    
    viewUbicacionDetails(id) {
        console.log('👁️ Viendo detalles de ubicación:', id);
        
        // Simular datos de ubicación para la demo
        const ubicacion = {
            id: id,
            usuario_nombre: 'María García',
            latitud: 19.4326,
            longitud: -99.1332,
            precision_metros: 5,
            fuente: 'GPS',
            ubicacion_timestamp: new Date().toISOString(),
            direccion_estimada: 'Centro Histórico, Ciudad de México',
            velocidad: '0 km/h',
            altitud: '2240 m'
        };
        
        // Mostrar modal con detalles
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>Detalles de Ubicación #${ubicacion.id}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Usuario:</label>
                            <span>${ubicacion.usuario_nombre}</span>
                        </div>
                        <div class="info-item">
                            <label>Coordenadas:</label>
                            <span>${ubicacion.latitud}, ${ubicacion.longitud}</span>
                        </div>
                        <div class="info-item">
                            <label>Precisión:</label>
                            <span>${ubicacion.precision_metros} metros</span>
                        </div>
                        <div class="info-item">
                            <label>Fuente:</label>
                            <span>${ubicacion.fuente}</span>
                        </div>
                        <div class="info-item">
                            <label>Dirección estimada:</label>
                            <span>${ubicacion.direccion_estimada}</span>
                        </div>
                        <div class="info-item">
                            <label>Velocidad:</label>
                            <span>${ubicacion.velocidad}</span>
                        </div>
                        <div class="info-item">
                            <label>Altitud:</label>
                            <span>${ubicacion.altitud}</span>
                        </div>
                        <div class="info-item">
                            <label>Timestamp:</label>
                            <span>${new Date(ubicacion.ubicacion_timestamp).toLocaleString()}</span>
                        </div>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Cerrar
                    </button>
                    <button class="btn btn-primary" onclick="app.exportUbicacion(${ubicacion.id})">
                        <i class="fas fa-download"></i>
                        Exportar
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.showToast('Detalles de ubicación cargados', 'info');
    }
    
    exportUbicacion(id) {
        console.log('📥 Exportando ubicación:', id);
        
        // Simular datos de ubicación para exportar
        const ubicacion = {
            id: id,
            usuario_nombre: 'María García',
            latitud: 19.4326,
            longitud: -99.1332,
            precision_metros: 5,
            fuente: 'GPS',
            ubicacion_timestamp: new Date().toISOString(),
            direccion_estimada: 'Centro Histórico, Ciudad de México'
        };
        
        // Crear contenido CSV
        const csvContent = [
            'ID,Usuario,Latitud,Longitud,Precisión,Fuente,Timestamp,Dirección',
            `${ubicacion.id},"${ubicacion.usuario_nombre}",${ubicacion.latitud},${ubicacion.longitud},${ubicacion.precision_metros},"${ubicacion.fuente}","${ubicacion.ubicacion_timestamp}","${ubicacion.direccion_estimada}"`
        ].join('\n');
        
        // Crear y descargar archivo
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `ubicacion_${id}_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showToast('Ubicación exportada exitosamente', 'success');
    }
    
    searchUbicaciones() {
        const searchTerm = document.getElementById('ubicacionSearch').value;
        this.searchTable(searchTerm, 'ubicacionesTable');
    }
    
    viewUbicacionOnMap(id) {
        console.log('🗺️ Mostrando ubicación en mapa:', id);
        
        // Simular datos de ubicación específica
        const ubicacion = {
            id: id,
            usuario_nombre: 'María García',
            latitud: 19.4326,
            longitud: -99.1332,
            precision_metros: 5,
            fuente: 'GPS',
            ubicacion_timestamp: new Date().toISOString(),
            direccion_estimada: 'Centro Histórico, Ciudad de México'
        };
        
        // Crear modal con mapa
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h3>Ubicación de ${ubicacion.usuario_nombre} - #${ubicacion.id}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 1rem;">
                        <p><strong>Dirección estimada:</strong> ${ubicacion.direccion_estimada}</p>
                        <p><strong>Coordenadas:</strong> ${ubicacion.latitud}, ${ubicacion.longitud}</p>
                        <p><strong>Precisión:</strong> ${ubicacion.precision_metros} metros</p>
                        <p><strong>Fecha:</strong> ${new Date(ubicacion.ubicacion_timestamp).toLocaleString()}</p>
                    </div>
                    <div id="mapModal" style="height: 400px; width: 100%; border-radius: 8px; border: 1px solid #e5e7eb;"></div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Cerrar
                    </button>
                    <button class="btn btn-primary" onclick="app.exportUbicacion(${ubicacion.id})">
                        <i class="fas fa-download"></i>
                        Exportar
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Inicializar mapa después de que el modal esté en el DOM
        setTimeout(() => {
            this.initMapModal(ubicacion);
        }, 100);
        
        this.showToast('Mapa cargado', 'info');
    }
    
    initMapModal(ubicacion) {
        console.log('🗺️ Inicializando mapa en modal...');
        
        // Crear mapa centrado en la ubicación específica
        const map = L.map('mapModal').setView([ubicacion.latitud, ubicacion.longitud], 15);
        
        // Agregar capa de tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Agregar marcador en la ubicación específica
        const marker = L.circleMarker([ubicacion.latitud, ubicacion.longitud], {
            radius: 10,
            fillColor: '#dc3545',
            color: '#fff',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        // Popup con información
        marker.bindPopup(`
            <div style="min-width: 200px;">
                <h4 style="margin: 0 0 8px 0; color: #374151;">${ubicacion.usuario_nombre}</h4>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Coordenadas:</strong> ${ubicacion.latitud.toFixed(6)}, ${ubicacion.longitud.toFixed(6)}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Precisión:</strong> ${ubicacion.precision_metros}m</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Dirección:</strong> ${ubicacion.direccion_estimada}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Fecha:</strong> ${new Date(ubicacion.ubicacion_timestamp).toLocaleString()}</p>
            </div>
        `).openPopup();
        
        console.log('✅ Mapa en modal inicializado');
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
        console.log('🖥️ Rendering microservicios...', data);
        const container = document.getElementById('microserviciosGrid');
        if (!container) {
            console.error('❌ Container microserviciosGrid no encontrado');
            return;
        }
        
        container.innerHTML = '';
        
        // Crear datos dummy si no hay datos reales
        if (!data || data.length === 0) {
            console.log('📊 Creando datos dummy para la demo');
            data = [
                { id: 1, nombre: 'Android API Service', estado: 'activo' },
                { id: 2, nombre: 'Flask Metrics Service', estado: 'inactivo' },
                { id: 3, nombre: 'Notification Service', estado: 'activo' }
            ];
        }
        
        // Crear la gráfica directamente
        this.createSimpleChart(container, data);
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
                    <button class="btn btn-sm btn-secondary" onclick="app.refreshMicroservicios()">
                        <i class="fas fa-refresh"></i> Actualizar
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
    
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
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