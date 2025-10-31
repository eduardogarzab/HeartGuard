import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser, hasRole } from './auth.js';
import {
  initSidebarToggle,
  showLoader,
  xmlCollectionToArray,
  xmlNodeText,
  t
} from './utils.js';

let users = [];
let tableBody;
let searchInput;
let roleFilter;
let statusFilter;
let feedback;

function renderUsers() {
  if (!tableBody) return;
  tableBody.innerHTML = '';
  const searchTerm = searchInput?.value.trim().toLowerCase() || '';
  const role = roleFilter?.value || 'all';
  const status = statusFilter?.value || 'all';

  const filtered = users.filter((user) => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm) || user.email.toLowerCase().includes(searchTerm);
    const matchesRole = role === 'all' || user.role === role;
    const matchesStatus = status === 'all' || user.status === status;
    return matchesSearch && matchesRole && matchesStatus;
  });

  if (filtered.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.className = 'table-empty';
    cell.textContent = t('noResults');
    row.appendChild(cell);
    tableBody.appendChild(row);
    return;
  }

  filtered.forEach((user) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${user.name}</td>
      <td>${user.email}</td>
      <td>${user.role}</td>
      <td>${user.status}</td>
      <td>
        ${hasRole('org_admin') ? `<button class="button button--ghost" data-edit="${user.id}">Editar</button>` : '—'}
      </td>
    `;
    tableBody.appendChild(row);
  });

  tableBody.querySelectorAll('[data-edit]').forEach((button) => {
    button.addEventListener('click', () => {
      setFeedback('Funcionalidad de edición en desarrollo.', 'info');
    });
  });
}

function setFeedback(message, variant = 'info') {
  if (!feedback) return;
  feedback.hidden = false;
  feedback.textContent = message;
  feedback.className = `alert alert--${variant}`;
}

async function loadUsers() {
  const orgId = getOrgId();
  if (!orgId) return;
  showLoader(tableBody);
  try {
    const xml = await apiClient.request('/users');
    if (!xml) {
      tableBody.innerHTML = '';
      return;
    }
    users = xmlCollectionToArray(xml, 'User')
      .filter((node) => xmlNodeText(node, 'org_id') === orgId)
      .map((node) => ({
        id: xmlNodeText(node, 'id'),
        name: xmlNodeText(node, 'name'),
        email: xmlNodeText(node, 'email'),
        role: xmlNodeText(node, 'role'),
        status: xmlNodeText(node, 'status')
      }));
    renderUsers();
  } catch (error) {
    console.error(error);
    tableBody.innerHTML = `<tr><td colspan="5" class="table-empty">${error.message}</td></tr>`;
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
  tableBody = document.querySelector('#users-table tbody');
  searchInput = document.getElementById('search-users');
  roleFilter = document.getElementById('filter-role');
  statusFilter = document.getElementById('filter-status');
  feedback = document.getElementById('users-feedback');

  if (searchInput) searchInput.addEventListener('input', renderUsers);
  if (roleFilter) roleFilter.addEventListener('change', renderUsers);
  if (statusFilter) statusFilter.addEventListener('change', renderUsers);

  loadUsers();
}

document.addEventListener('DOMContentLoaded', init);
