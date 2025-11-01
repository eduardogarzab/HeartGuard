import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser } from './auth.js';
import {
  initSidebarToggle,
  showLoader,
  xmlCollectionToArray,
  xmlNodeText,
  formatDateTime,
  buildSeverityBadge,
  buildStatusBadge,
  t
} from './utils.js';

let alerts = [];
let tableBody;
let severityFilter;
let statusFilter;
let feedback;

function renderAlerts() {
  if (!tableBody) return;
  tableBody.innerHTML = '';
  const severity = severityFilter?.value || 'all';
  const status = statusFilter?.value || 'all';

  const filtered = alerts.filter((alert) => {
    const severityMatch = severity === 'all' || alert.severity === severity;
    const statusMatch = status === 'all' || alert.status === status;
    return severityMatch && statusMatch;
  });

  if (filtered.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 7;
    cell.className = 'table-empty';
    cell.textContent = t('noResults');
    row.appendChild(cell);
    tableBody.appendChild(row);
    return;
  }

  filtered.forEach((alert) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${alert.patient_name}</td>
      <td>${formatDateTime(alert.created_at)}</td>
      <td data-severity></td>
      <td data-status></td>
      <td>${alert.description}</td>
      <td>${alert.assignee || '—'}</td>
      <td class="actions">
        <button class="button button--ghost" data-ack="${alert.id}">Reconocer</button>
        <button class="button button--secondary" data-assign="${alert.id}">Asignar</button>
        <button class="button" data-resolve="${alert.id}">Resolver</button>
      </td>
    `;

    const severityCell = row.querySelector('[data-severity]');
    const statusCell = row.querySelector('[data-status]');
    if (severityCell) {
      const badge = buildSeverityBadge(alert.severity);
      if (alert.severity === 'critical') {
        badge.classList.add('badge-danger');
      }
      severityCell.appendChild(badge);
    }
    if (statusCell) {
      statusCell.appendChild(buildStatusBadge(alert.status));
    }

    tableBody.appendChild(row);
  });

  tableBody.querySelectorAll('[data-ack]').forEach((button) => {
    button.addEventListener('click', async () => {
      if (confirm(t('confirmAcknowledgeAlert'))) {
        await acknowledgeAlert(button.getAttribute('data-ack'));
      }
    });
  });

  tableBody.querySelectorAll('[data-resolve]').forEach((button) => {
    button.addEventListener('click', async () => {
      if (confirm(t('confirmResolveAlert'))) {
        await resolveAlert(button.getAttribute('data-resolve'));
      }
    });
  });

  tableBody.querySelectorAll('[data-assign]').forEach((button) => {
    button.addEventListener('click', async () => {
      const member = prompt('Ingrese el correo del miembro a asignar');
      if (member) {
        await assignAlert(button.getAttribute('data-assign'), member.trim());
      }
    });
  });
}

async function acknowledgeAlert(alertId) {
  try {
    await apiClient.request(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: `<AcknowledgeAlertRequest><id>${alertId}</id></AcknowledgeAlertRequest>`
    });
    setFeedback('Alerta marcada como reconocida.', 'success');
    await loadAlerts();
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

async function resolveAlert(alertId) {
  try {
    await apiClient.request(`/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: `<ResolveAlertRequest><id>${alertId}</id></ResolveAlertRequest>`
    });
    setFeedback('Alerta marcada como resuelta.', 'success');
    await loadAlerts();
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

async function assignAlert(alertId, assignee) {
  if (!assignee || assignee.length < 3) {
    setFeedback('Ingresa un asignatario válido.', 'danger');
    return;
  }
  try {
    await apiClient.request(`/alerts/${alertId}/assign`, {
      method: 'POST',
      body: `<AssignAlertRequest><id>${alertId}</id><assignee>${assignee}</assignee></AssignAlertRequest>`
    });
    setFeedback('Alerta asignada correctamente.', 'success');
    await loadAlerts();
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

function setFeedback(message, variant = 'info') {
  if (!feedback) return;
  feedback.hidden = false;
  feedback.textContent = message;
  feedback.className = `alert alert--${variant}`;
}

async function loadAlerts() {
  const orgId = getOrgId();
  if (!orgId) return;
  showLoader(tableBody);
  try {
    const xml = await apiClient.request('/alerts');
    if (!xml) {
      tableBody.innerHTML = '';
      return;
    }
    alerts = xmlCollectionToArray(xml, 'Alert')
      .filter((node) => xmlNodeText(node, 'org_id') === orgId)
      .map((node) => ({
        id: xmlNodeText(node, 'id'),
        patient_name: xmlNodeText(node, 'patient_name'),
        description: xmlNodeText(node, 'description'),
        severity: xmlNodeText(node, 'severity').toLowerCase(),
        status: xmlNodeText(node, 'status').toLowerCase(),
        assignee: xmlNodeText(node, 'assignee'),
        created_at: xmlNodeText(node, 'created_at')
      }));
    renderAlerts();
  } catch (error) {
    console.error(error);
    tableBody.innerHTML = `<tr><td colspan="7" class="table-empty">${error.message}</td></tr>`;
  }
}

function populateUserContext() {
  const user = getCurrentUser();
  const orgName = document.querySelector('[data-org-name]');
  if (orgName && user?.organization_name) {
    orgName.textContent = user.organization_name;
  }
}

function init() {
  requireAuth();
  initSidebarToggle();
  populateUserContext();
  tableBody = document.querySelector('#alerts-table tbody');
  severityFilter = document.getElementById('filter-severity');
  statusFilter = document.getElementById('filter-status');
  feedback = document.getElementById('alerts-feedback');

  if (severityFilter) {
    severityFilter.addEventListener('change', renderAlerts);
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', renderAlerts);
  }

  loadAlerts();
}

document.addEventListener('DOMContentLoaded', init);
