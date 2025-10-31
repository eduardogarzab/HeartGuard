const UI_STRINGS = {
  es: {
    dashboard: 'Panel de control',
    organization: 'Organización',
    users: 'Usuarios',
    patients: 'Pacientes',
    devices: 'Dispositivos',
    alerts: 'Alertas',
    invitations: 'Invitaciones',
    profile: 'Perfil',
    logout: 'Cerrar sesión',
    loading: 'Cargando…',
    noResults: 'No se encontraron resultados',
    confirm: 'Confirmar',
    cancel: 'Cancelar',
    confirmCancelInvitation: '¿Deseas cancelar esta invitación? Esta acción no se puede deshacer.',
    confirmResolveAlert: '¿Marcar esta alerta como resuelta?',
    confirmAcknowledgeAlert: '¿Marcar esta alerta como reconocida?',
    confirmDelete: '¿Confirmas que deseas continuar con la acción?',
    severityCritical: 'Crítica',
    severityHigh: 'Alta',
    severityMedium: 'Media',
    severityLow: 'Baja',
    severityInfo: 'Informativa',
    statusOpen: 'Abierta',
    statusAcknowledged: 'Reconocida',
    statusResolved: 'Resuelta',
    inviteNew: 'Nueva invitación',
    searchPlaceholder: 'Buscar…',
    riskLevel: 'Nivel de riesgo',
    totalUsers: 'Usuarios totales',
    totalPatients: 'Pacientes totales',
    openAlerts: 'Alertas abiertas',
    auditEvents: 'Eventos recientes',
    loginTitle: 'Iniciar sesión',
    email: 'Correo electrónico',
    password: 'Contraseña',
    submit: 'Enviar',
    rememberOrg: 'Organización',
    filters: 'Filtros',
    refresh: 'Actualizar',
    modalClose: 'Cerrar modal'
  }
};

let currentLang = localStorage.getItem('lang') || 'es';

export function t(key) {
  const langPack = UI_STRINGS[currentLang] || UI_STRINGS.es;
  return langPack[key] || key;
}

export function setLang(lang) {
  if (UI_STRINGS[lang]) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
  }
}

export function parseXml(xmlString) {
  const parser = new DOMParser();
  return parser.parseFromString(xmlString, 'application/xml');
}

export function xmlNodeText(node, selector) {
  const el = node.querySelector(selector);
  return el ? el.textContent.trim() : '';
}

export function xmlCollectionToArray(document, itemSelector) {
  return Array.from(document.querySelectorAll(itemSelector));
}

export function formatDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatDateTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function capitalize(value) {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function buildSeverityBadge(severity) {
  const normalized = (severity || '').toLowerCase();
  const badge = document.createElement('span');
  badge.classList.add('badge');
  if (normalized === 'critical' || normalized === 'high') {
    badge.classList.add('badge-danger');
  } else if (normalized === 'medium' || normalized === 'warning') {
    badge.classList.add('badge-warning');
  } else if (normalized === 'low' || normalized === 'info') {
    badge.classList.add('badge-info');
  } else {
    badge.classList.add('badge-success');
  }
  badge.textContent = capitalize(normalized);
  return badge;
}

export function buildStatusBadge(status) {
  const normalized = (status || '').toLowerCase();
  const badge = document.createElement('span');
  badge.classList.add('badge');
  if (normalized === 'resolved') {
    badge.classList.add('badge-success');
  } else if (normalized === 'open') {
    badge.classList.add('badge-danger');
  } else {
    badge.classList.add('badge-warning');
  }
  badge.textContent = capitalize(normalized);
  return badge;
}

export function showLoader(container) {
  container.innerHTML = '';
  const loader = document.createElement('div');
  loader.className = 'loader';
  loader.setAttribute('role', 'status');
  loader.innerHTML = `<span class="loader__spinner" aria-hidden="true"></span><span>${t('loading')}</span>`;
  container.appendChild(loader);
}

export function hideLoader(container) {
  container.innerHTML = '';
}

export function paginate(array, page = 1, pageSize = 10) {
  const start = (page - 1) * pageSize;
  return array.slice(start, start + pageSize);
}

export function trapFocus(modal) {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea',
    'input',
    'select',
    '[tabindex]:not([tabindex="-1"])'
  ];
  const focusableElements = Array.from(modal.querySelectorAll(focusableSelectors.join(',')));
  if (focusableElements.length === 0) return;
  const first = focusableElements[0];
  const last = focusableElements[focusableElements.length - 1];

  modal.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab') return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  first.focus();
}

export function initSidebarToggle() {
  const sidebar = document.querySelector('.sidebar');
  const toggle = document.querySelector('.sidebar__toggle');
  if (!sidebar || !toggle) return;

  toggle.addEventListener('click', () => {
    const isOpen = sidebar.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
}

export function validateEmail(email) {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}

export function ensurePositiveInteger(value) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0;
}
