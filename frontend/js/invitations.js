import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser, hasRole } from './auth.js';
import {
  initSidebarToggle,
  showLoader,
  hideLoader,
  xmlCollectionToArray,
  xmlNodeText,
  formatDateTime,
  validateEmail,
  ensurePositiveInteger,
  t
} from './utils.js';

let invitations = [];
let tableBody;
let createForm;
let feedback;

function renderInvitations() {
  if (!tableBody) return;
  tableBody.innerHTML = '';

  if (invitations.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.className = 'table-empty';
    cell.textContent = t('noResults');
    row.appendChild(cell);
    tableBody.appendChild(row);
    return;
  }

  invitations.forEach((invitation) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${invitation.email}</td>
      <td>${invitation.role}</td>
      <td>${invitation.status}</td>
      <td>${formatDateTime(invitation.expires_at)}</td>
      <td>
        <div class="badge badge-info" aria-label="Token de invitación">${invitation.token}</div>
      </td>
      <td>
        ${invitation.status === 'pending' ? `<button type="button" class="button button--ghost" data-cancel="${invitation.id}">Cancelar</button>` : ''}
      </td>
    `;
    tableBody.appendChild(row);
  });

  tableBody.querySelectorAll('[data-cancel]').forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.getAttribute('data-cancel');
      if (confirm(t('confirmCancelInvitation'))) {
        cancelInvitation(id);
      }
    });
  });
}

async function cancelInvitation(invitationId) {
  try {
    await apiClient.request(`/organization/invitations/${invitationId}/cancel`, {
      method: 'POST',
      body: `<CancelInvitationRequest><id>${invitationId}</id></CancelInvitationRequest>`
    });
    await loadInvitations();
    setFeedback('Invitación cancelada correctamente.', 'success');
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

function setFeedback(message, variant = 'info') {
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = `alert alert--${variant}`;
  feedback.hidden = false;
}

async function handleCreateInvitation(event) {
  event.preventDefault();
  if (!hasRole('org_admin')) {
    setFeedback('No tienes permisos para crear invitaciones.', 'danger');
    return;
  }

  const formData = new FormData(createForm);
  const email = formData.get('email').trim();
  const role = formData.get('role');
  const ttl = formData.get('ttl_hours');
  const orgId = getOrgId();

  if (!validateEmail(email)) {
    setFeedback('Correo inválido.', 'danger');
    return;
  }

  if (!ensurePositiveInteger(ttl)) {
    setFeedback('TTL debe ser un entero positivo.', 'danger');
    return;
  }

  const body = `
    <InvitationRequest>
      <org_id>${orgId}</org_id>
      <email>${email}</email>
      <role>${role}</role>
      <ttl_hours>${ttl}</ttl_hours>
    </InvitationRequest>
  `;

  try {
    const xml = await apiClient.request('/organization/invitations', {
      method: 'POST',
      body
    });
    if (!xml) return;
    const token = xmlNodeText(xml, 'token');
    setFeedback(`Invitación creada. Token: ${token}`, 'success');
    createForm.reset();
    await loadInvitations();
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

async function loadInvitations() {
  const orgId = getOrgId();
  if (!orgId) return;
  showLoader(tableBody);
  try {
    const xml = await apiClient.request('/organization/invitations');
    if (!xml) {
      tableBody.innerHTML = '';
      return;
    }
    invitations = xmlCollectionToArray(xml, 'Invitation')
      .filter((node) => xmlNodeText(node, 'org_id') === orgId)
      .map((node) => ({
        id: xmlNodeText(node, 'id'),
        email: xmlNodeText(node, 'email'),
        role: xmlNodeText(node, 'role'),
        status: xmlNodeText(node, 'status'),
        token: xmlNodeText(node, 'token'),
        expires_at: xmlNodeText(node, 'expires_at')
      }));
    renderInvitations();
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
  tableBody = document.querySelector('#invitations-table tbody');
  createForm = document.getElementById('invitation-form');
  feedback = document.getElementById('invitation-feedback');
  if (createForm) {
    createForm.addEventListener('submit', handleCreateInvitation);
    if (!hasRole('org_admin')) {
      createForm.querySelectorAll('input, select, button').forEach((el) => {
        el.disabled = true;
      });
      setFeedback('Tu rol no permite crear invitaciones.', 'warning');
    }
  }
  loadInvitations();
}

document.addEventListener('DOMContentLoaded', init);
