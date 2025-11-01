import { apiClient } from './api.js';
import { requireAuth, getOrgId, getCurrentUser, hasRole } from './auth.js';
import { initSidebarToggle, showLoader, xmlNodeText } from './utils.js';

let form;
let feedback;

function populateUserContext() {
  const user = getCurrentUser();
  const orgName = document.querySelector('[data-org-name]');
  if (orgName && user?.organization_name) {
    orgName.textContent = user.organization_name;
  }
}

async function loadOrganization() {
  const orgId = getOrgId();
  if (!orgId || !form) return;
  showLoader(form);
  try {
    const xml = await apiClient.request(`/organization/${orgId}`);
    if (!xml) return;
    const org = xml.querySelector('Organization');
    if (!org) return;

    form.innerHTML = '';
    form.insertAdjacentHTML(
      'beforeend',
      `
        <div class="card card--form">
          <div class="card__header">
            <h2 class="card__title">Identidad de la organización</h2>
            <p class="card__subtitle">Sincroniza la información corporativa que consumen los microservicios.</p>
          </div>
          <div class="filter-bar">
            <div class="filter-bar__group">
              <label for="org-name">Nombre</label>
              <input id="org-name" name="name" type="text" value="${xmlNodeText(org, 'name')}" required />
            </div>
            <div class="filter-bar__group">
              <label for="org-brand">Branding</label>
              <input id="org-brand" name="branding" type="text" value="${xmlNodeText(org, 'branding')}" />
            </div>
          </div>
          <div class="filter-bar">
            <div class="filter-bar__group">
              <label for="org-contact-email">Email de contacto</label>
              <input id="org-contact-email" name="contact_email" type="email" value="${xmlNodeText(org, 'contact_email')}" required />
            </div>
            <div class="filter-bar__group">
              <label for="org-contact-phone">Teléfono</label>
              <input id="org-contact-phone" name="contact_phone" type="text" value="${xmlNodeText(org, 'contact_phone')}" />
            </div>
          </div>
          <div class="filter-bar">
            <div class="filter-bar__group filter-bar__group--full">
              <label for="org-address">Dirección</label>
              <textarea id="org-address" name="address" rows="3">${xmlNodeText(org, 'address')}</textarea>
            </div>
          </div>
          <button class="button" type="submit">Guardar cambios</button>
        </div>
      `
    );

    if (!hasRole('org_admin')) {
      form.querySelectorAll('input, textarea, button').forEach((el) => {
        el.disabled = true;
      });
      setFeedback('Solo los administradores pueden editar la organización.', 'info');
    }
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

async function handleSubmit(event) {
  event.preventDefault();
  if (!hasRole('org_admin')) {
    setFeedback('No tienes permisos para actualizar.', 'danger');
    return;
  }
  const formData = new FormData(form);
  const body = `
    <OrganizationUpdate>
      <name>${formData.get('name').trim()}</name>
      <branding>${formData.get('branding').trim()}</branding>
      <contact_email>${formData.get('contact_email').trim()}</contact_email>
      <contact_phone>${formData.get('contact_phone').trim()}</contact_phone>
      <address>${formData.get('address').trim()}</address>
    </OrganizationUpdate>
  `;
  try {
    await apiClient.request(`/organization/${getOrgId()}`, {
      method: 'PATCH',
      body
    });
    setFeedback('Organización actualizada correctamente.', 'success');
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

function init() {
  requireAuth();
  initSidebarToggle();
  populateUserContext();
  form = document.getElementById('organization-form');
  feedback = document.getElementById('organization-feedback');
  if (form) {
    form.addEventListener('submit', handleSubmit);
  }
  loadOrganization();
}

document.addEventListener('DOMContentLoaded', init);
