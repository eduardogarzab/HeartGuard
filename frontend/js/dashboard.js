import { apiClient } from './api.js';
import { requireAuth, getCurrentUser, getOrgId } from './auth.js';
import { initSidebarToggle, showLoader, hideLoader, formatDateTime, xmlCollectionToArray, xmlNodeText, t } from './utils.js';

let metricsElements;
let auditList;
let criticalIndicator;

async function loadMetrics() {
  const orgId = getOrgId();
  if (!orgId) return;

  Object.values(metricsElements).forEach((el) => {
    if (el) {
      showLoader(el);
    }
  });

  try {
    const metricsXml = await apiClient.request(`/metrics?org_id=${encodeURIComponent(orgId)}`);
    if (!metricsXml) return;
    const totals = metricsXml.querySelector('Metrics');
    if (totals) {
      updateMetric('users', xmlNodeText(totals, 'total_users'));
      updateMetric('patients', xmlNodeText(totals, 'total_patients'));
      updateMetric('alerts', xmlNodeText(totals, 'open_alerts'));
    }
    await loadAuditEvents(orgId);
  } catch (error) {
    console.error(error);
    showError(Object.values(metricsElements), error);
  }
}

async function loadAuditEvents(orgId) {
  if (!auditList) return;
  showLoader(auditList);
  try {
    const auditXml = await apiClient.request(`/audit?org_id=${encodeURIComponent(orgId)}`);
    hideLoader(auditList);
    if (!auditXml) {
      auditList.innerHTML = `<li>${t('noResults')}</li>`;
      return;
    }

    const events = xmlCollectionToArray(auditXml, 'Event').filter((eventNode) => xmlNodeText(eventNode, 'org_id') === orgId);
    if (events.length === 0) {
      auditList.innerHTML = `<li>${t('noResults')}</li>`;
      return;
    }

    auditList.innerHTML = '';
    events.slice(0, 10).forEach((eventNode) => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${xmlNodeText(eventNode, 'type')}</strong> · ${formatDateTime(xmlNodeText(eventNode, 'created_at'))}`;
      auditList.appendChild(li);
    });
  } catch (error) {
    console.error(error);
    auditList.innerHTML = `<li>${error.message}</li>`;
  }
}

function updateMetric(key, value) {
  const el = metricsElements[key];
  if (!el) return;
  hideLoader(el);
  el.textContent = value || '0';
  if (key === 'alerts' && criticalIndicator) {
    criticalIndicator.textContent = value || '0';
  }
}

function showError(elements, error) {
  elements.forEach((el) => {
    if (!el) return;
    el.innerHTML = `<span class="alert alert--danger">${error.message}</span>`;
  });
}

function populateUserContext() {
  const user = getCurrentUser();
  const orgName = document.querySelector('[data-org-name]');
  if (orgName && user?.organization_name) {
    orgName.textContent = user.organization_name;
  }
}

function initDashboard() {
  requireAuth();
  initSidebarToggle();
  populateUserContext();

  metricsElements = {
    users: document.getElementById('metric-users'),
    patients: document.getElementById('metric-patients'),
    alerts: document.getElementById('metric-alerts')
  };
  auditList = document.getElementById('audit-events');
  criticalIndicator = document.querySelector('[data-critical-indicator]');

  loadMetrics();
}

document.addEventListener('DOMContentLoaded', initDashboard);
