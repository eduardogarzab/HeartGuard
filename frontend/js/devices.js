import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser } from './auth.js';
import {
  initSidebarToggle,
  showLoader,
  xmlCollectionToArray,
  xmlNodeText,
  formatDateTime,
  trapFocus,
  t
} from './utils.js';

let devices = [];
let tableBody;
let statusFilter;
let typeFilter;
let searchInput;
let modal;
let modalContent;

function renderDevices() {
  if (!tableBody) return;
  tableBody.innerHTML = '';
  const status = statusFilter?.value || 'all';
  const type = typeFilter?.value || 'all';
  const searchTerm = searchInput?.value.trim().toLowerCase() || '';

  const filtered = devices.filter((device) => {
    const matchesStatus = status === 'all' || device.status === status;
    const matchesType = type === 'all' || device.type === type;
    const matchesSearch =
      device.serial.toLowerCase().includes(searchTerm) ||
      device.patient_name.toLowerCase().includes(searchTerm);
    return matchesStatus && matchesType && matchesSearch;
  });

  if (filtered.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 6;
    cell.className = 'table-empty';
    cell.textContent = t('noResults');
    row.appendChild(cell);
    tableBody.appendChild(row);
    return;
  }

  filtered.forEach((device) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${device.serial}</td>
      <td>${device.type}</td>
      <td>${device.status}</td>
      <td>${device.patient_name || 'No asignado'}</td>
      <td>${formatDateTime(device.last_seen)}</td>
      <td><button class="button button--ghost" data-view="${device.id}">Ver detalles</button></td>
    `;
    tableBody.appendChild(row);
  });

  tableBody.querySelectorAll('[data-view]').forEach((button) => {
    button.addEventListener('click', () => {
      const device = devices.find((item) => item.id === button.getAttribute('data-view'));
      if (device) {
        openModal(device);
      }
    });
  });
}

function openModal(device) {
  if (!modal || !modalContent) return;
  modalContent.innerHTML = `
    <header>
      <h2>Dispositivo ${device.serial}</h2>
      <p>Estado: ${device.status}</p>
    </header>
    <section>
      <p><strong>Tipo:</strong> ${device.type}</p>
      <p><strong>Asignado a:</strong> ${device.patient_name || 'No asignado'}</p>
      <p><strong>Último ping:</strong> ${formatDateTime(device.last_seen)}</p>
      <p><strong>Firmware:</strong> ${device.firmware_version || 'N/D'}</p>
      <p><strong>Notas:</strong> ${device.notes || 'N/A'}</p>
    </section>
    <button class="modal__close" type="button" aria-label="${t('modalClose')}">&times;</button>
  `;
  modal.setAttribute('aria-hidden', 'false');
  modal.addEventListener('click', handleBackdropClick);
  const closeButton = modalContent.querySelector('.modal__close');
  closeButton.addEventListener('click', closeModal);
  trapFocus(modal);
}

function closeModal() {
  if (!modal) return;
  modal.setAttribute('aria-hidden', 'true');
  modal.removeEventListener('click', handleBackdropClick);
}

function handleBackdropClick(event) {
  if (event.target === modal) {
    closeModal();
  }
}

async function loadDevices() {
  const orgId = getOrgId();
  if (!orgId) return;
  showLoader(tableBody);
  try {
    const xml = await apiClient.request('/devices');
    if (!xml) {
      tableBody.innerHTML = '';
      return;
    }
    devices = xmlCollectionToArray(xml, 'Device')
      .filter((node) => xmlNodeText(node, 'org_id') === orgId)
      .map((node) => ({
        id: xmlNodeText(node, 'id'),
        serial: xmlNodeText(node, 'serial'),
        type: xmlNodeText(node, 'type'),
        status: xmlNodeText(node, 'status'),
        patient_name: xmlNodeText(node, 'patient_name'),
        last_seen: xmlNodeText(node, 'last_seen'),
        firmware_version: xmlNodeText(node, 'firmware_version'),
        notes: xmlNodeText(node, 'notes')
      }));
    renderDevices();
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
  tableBody = document.querySelector('#devices-table tbody');
  statusFilter = document.getElementById('filter-status');
  typeFilter = document.getElementById('filter-type');
  searchInput = document.getElementById('search-devices');
  modal = document.getElementById('device-modal');
  modalContent = document.querySelector('#device-modal .modal__dialog');

  if (statusFilter) statusFilter.addEventListener('change', renderDevices);
  if (typeFilter) typeFilter.addEventListener('change', renderDevices);
  if (searchInput) searchInput.addEventListener('input', renderDevices);

  loadDevices();
}

document.addEventListener('DOMContentLoaded', init);
