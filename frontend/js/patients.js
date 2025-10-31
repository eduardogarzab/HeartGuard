import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser } from './auth.js';
import {
  initSidebarToggle,
  showLoader,
  hideLoader,
  xmlCollectionToArray,
  xmlNodeText,
  formatDate,
  formatDateTime,
  trapFocus,
  t
} from './utils.js';

let patients = [];
let currentPage = 1;
const PAGE_SIZE = 10;
let tableBody;
let paginationContainer;
let searchInput;
let riskFilter;
let modal;
let modalContent;

function setupFilters() {
  if (searchInput) {
    searchInput.addEventListener('input', renderPatients);
  }
  if (riskFilter) {
    riskFilter.addEventListener('change', renderPatients);
  }
}

function applyFilters() {
  const searchTerm = searchInput?.value.trim().toLowerCase() || '';
  const risk = riskFilter?.value || 'all';
  return patients.filter((patient) => {
    const matchesSearch = patient.name.toLowerCase().includes(searchTerm);
    const matchesRisk = risk === 'all' || patient.risk_level === risk;
    return matchesSearch && matchesRisk;
  });
}

function renderPatients() {
  if (!tableBody) return;
  const filtered = applyFilters();
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  currentPage = Math.min(currentPage, totalPages);
  const items = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  tableBody.innerHTML = '';

  if (items.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 6;
    cell.className = 'table-empty';
    cell.textContent = t('noResults');
    row.appendChild(cell);
    tableBody.appendChild(row);
    renderPagination(totalPages);
    return;
  }

  items.forEach((patient) => {
    const row = document.createElement('tr');
    row.tabIndex = 0;
    row.setAttribute('role', 'button');
    row.setAttribute('aria-label', `Ver detalles de ${patient.name}`);
    row.addEventListener('click', () => openPatientModal(patient));
    row.addEventListener('keypress', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openPatientModal(patient);
      }
    });

    row.innerHTML = `
      <td>${patient.name}</td>
      <td>${patient.gender}</td>
      <td>${patient.age}</td>
      <td>${patient.risk_level}</td>
      <td>${formatDate(patient.admission_date)}</td>
      <td><button class="button button--ghost" type="button">Detalles</button></td>
    `;

    tableBody.appendChild(row);
  });

  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  if (!paginationContainer) return;
  paginationContainer.innerHTML = '';
  const prev = document.createElement('button');
  prev.textContent = 'Prev';
  prev.disabled = currentPage === 1;
  prev.addEventListener('click', () => {
    currentPage = Math.max(1, currentPage - 1);
    renderPatients();
  });

  const next = document.createElement('button');
  next.textContent = 'Next';
  next.disabled = currentPage === totalPages;
  next.addEventListener('click', () => {
    currentPage = Math.min(totalPages, currentPage + 1);
    renderPatients();
  });

  paginationContainer.appendChild(prev);
  const pageStatus = document.createElement('span');
  pageStatus.textContent = `${currentPage} / ${totalPages}`;
  paginationContainer.appendChild(pageStatus);
  paginationContainer.appendChild(next);
}

function openPatientModal(patient) {
  if (!modal || !modalContent) return;
  modal.setAttribute('aria-hidden', 'false');
  modalContent.innerHTML = `
    <header>
      <h2>${patient.name}</h2>
      <p>${patient.gender} · ${patient.age} años</p>
    </header>
    <section>
      <p><strong>Nivel de riesgo:</strong> ${patient.risk_level}</p>
      <p><strong>Fecha de alta:</strong> ${formatDate(patient.admission_date)}</p>
      <p><strong>Última actualización:</strong> ${formatDateTime(patient.updated_at)}</p>
      <h3>Alertas recientes</h3>
      <ul>
        ${patient.alerts.map((alert) => `<li>${alert.severity} · ${formatDateTime(alert.created_at)} · ${alert.status}</li>`).join('')}
      </ul>
    </section>
    <button class="modal__close" type="button" aria-label="${t('modalClose')}">&times;</button>
  `;

  const closeButton = modalContent.querySelector('.modal__close');
  closeButton.addEventListener('click', closePatientModal);
  trapFocus(modal);
  modal.addEventListener('click', handleModalBackgroundClick);
}

function handleModalBackgroundClick(event) {
  if (event.target === modal) {
    closePatientModal();
  }
}

function closePatientModal() {
  if (!modal) return;
  modal.setAttribute('aria-hidden', 'true');
  modal.removeEventListener('click', handleModalBackgroundClick);
}

async function loadPatients() {
  const orgId = getOrgId();
  if (!orgId) return;
  showLoader(tableBody);
  try {
    const xml = await apiClient.request('/patients');
    if (!xml) {
      tableBody.innerHTML = '';
      return;
    }
    patients = xmlCollectionToArray(xml, 'Patient')
      .filter((node) => xmlNodeText(node, 'org_id') === orgId)
      .map((node) => ({
        id: xmlNodeText(node, 'id'),
        name: xmlNodeText(node, 'name'),
        gender: xmlNodeText(node, 'gender'),
        age: Number(xmlNodeText(node, 'age')),
        risk_level: xmlNodeText(node, 'risk_level'),
        admission_date: xmlNodeText(node, 'admission_date'),
        updated_at: xmlNodeText(node, 'updated_at'),
        alerts: xmlCollectionToArray(node, 'Alert').map((alertNode) => ({
          severity: xmlNodeText(alertNode, 'severity'),
          status: xmlNodeText(alertNode, 'status'),
          created_at: xmlNodeText(alertNode, 'created_at')
        }))
      });
    renderPatients();
  } catch (error) {
    console.error(error);
    tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">${error.message}</td></tr>`;
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
  tableBody = document.querySelector('#patients-table tbody');
  paginationContainer = document.querySelector('[data-pagination]');
  searchInput = document.getElementById('search-patients');
  riskFilter = document.getElementById('filter-risk');
  modal = document.getElementById('patient-modal');
  modalContent = document.querySelector('#patient-modal .modal__dialog');
  setupFilters();
  loadPatients();
}

document.addEventListener('DOMContentLoaded', init);
