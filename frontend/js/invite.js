const API_BASE_URL = 'http://136.115.53.140:5000';

import { parseXml, xmlNodeText, formatDateTime } from './utils.js';

const feedback = document.querySelector('#invite-feedback');
const subtitle = document.querySelector('[data-invite-subtitle]');
const summary = document.querySelector('[data-invite-summary]');
const orgNameEl = document.querySelector('[data-org-name]');
const roleLabelEl = document.querySelector('[data-role-label]');
const expirationEl = document.querySelector('[data-expiration]');
const choiceForm = document.querySelector('#invite-choice');
const userForm = document.querySelector('#invite-user-form');
const patientForm = document.querySelector('#invite-patient-form');

let currentToken = null;
let invitationDetails = null;

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function showFeedback(message, variant = 'info') {
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = `alert alert--${variant}`;
  feedback.hidden = false;
}

function hideFeedback() {
  if (!feedback) return;
  feedback.hidden = true;
}

function extractToken() {
  const pathMatch = window.location.pathname.match(/invite\/([^/]+)/);
  if (pathMatch && pathMatch[1]) {
    return decodeURIComponent(pathMatch[1]);
  }
  const url = new URL(window.location.href);
  return url.searchParams.get('token');
}

async function request(path, { method = 'GET', body = null } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/xml',
      Accept: 'application/xml'
    },
    body
  });

  const text = await response.text();
  if (!response.ok) {
    let message = `Error ${response.status}`;
    if (text) {
      try {
        const xml = parseXml(text);
        message = xml.querySelector('message')?.textContent || message;
      } catch (error) {
        message = `${message}: ${text}`;
      }
    }
    throw new Error(message);
  }
  return text ? parseXml(text) : null;
}

function toggleForms(mode) {
  if (!choiceForm || !userForm || !patientForm) return;
  userForm.hidden = mode !== 'user';
  patientForm.hidden = mode !== 'patient';
}

function disableForms() {
  [userForm, patientForm].forEach((form) => {
    if (!form) return;
    Array.from(form.elements).forEach((element) => {
      if ('disabled' in element) {
        element.disabled = true;
      }
    });
  });
}

function populateSummary(xml) {
  if (!summary) return;
  const invitationNode = xml.querySelector('invitation');
  const metadataNode = xml.querySelector('metadata');
  invitationDetails = {
    email: xmlNodeText(invitationNode, 'email'),
    orgId: xmlNodeText(invitationNode, 'org_id'),
    orgRoleId: xmlNodeText(invitationNode, 'org_role_id'),
  };

  const organizationName = xmlNodeText(metadataNode, 'organization > name') || xmlNodeText(metadataNode, 'organization name');
  const roleLabel = xmlNodeText(metadataNode, 'suggested_role > label') || xmlNodeText(metadataNode, 'suggested_role label');
  const expiresAt = xmlNodeText(metadataNode, 'expires_at');

  if (subtitle) {
    subtitle.textContent = 'Confirma los detalles y completa el registro.';
  }
  if (orgNameEl) {
    orgNameEl.textContent = organizationName || '—';
  }
  if (roleLabelEl) {
    roleLabelEl.textContent = roleLabel || '—';
  }
  if (expirationEl) {
    expirationEl.textContent = expiresAt ? formatDateTime(expiresAt) : '—';
  }

  summary.hidden = false;
  if (choiceForm) {
    choiceForm.hidden = false;
  }

  if (userForm) {
    userForm.hidden = false;
    if (invitationDetails.email) {
      userForm.querySelector('#invite-user-email').value = invitationDetails.email;
    }
  }
}

async function loadInvitation() {
  try {
    hideFeedback();
    const xml = await request(`/organization/invitations/${encodeURIComponent(currentToken)}/validate`);
    if (!xml) {
      showFeedback('No se pudo cargar la invitación.', 'danger');
      return;
    }
    populateSummary(xml);
  } catch (error) {
    console.error(error);
    showFeedback(error.message, 'danger');
    disableForms();
  }
}

function serializeUserForm() {
  const name = userForm.querySelector('#invite-user-name').value.trim();
  const email = userForm.querySelector('#invite-user-email').value.trim();
  const password = userForm.querySelector('#invite-user-password').value.trim();

  if (!name || !email || !password) {
    throw new Error('Completa todos los campos del usuario.');
  }

  return (
    '<UserRegistration>' +
    `<invite_token>${escapeXml(currentToken)}</invite_token>` +
    `<name>${escapeXml(name)}</name>` +
    `<email>${escapeXml(email)}</email>` +
    `<password>${escapeXml(password)}</password>` +
    '</UserRegistration>'
  );
}

function serializePatientForm() {
  const personName = patientForm.querySelector('#invite-patient-name').value.trim();
  if (!personName) {
    throw new Error('Indica el nombre del paciente.');
  }
  return (
    '<PatientRegistration>' +
    `<invite_token>${escapeXml(currentToken)}</invite_token>` +
    `<person_name>${escapeXml(personName)}</person_name>` +
    '</PatientRegistration>'
  );
}

async function submitUser(event) {
  event.preventDefault();
  try {
    const body = serializeUserForm();
    await request('/users/register', { method: 'POST', body });
    showFeedback('Cuenta creada correctamente. Ya puedes iniciar sesión.', 'success');
    disableForms();
  } catch (error) {
    console.error(error);
    showFeedback(error.message, 'danger');
  }
}

async function submitPatient(event) {
  event.preventDefault();
  try {
    const body = serializePatientForm();
    await request('/patients/register', { method: 'POST', body });
    showFeedback('Paciente registrado correctamente.', 'success');
    disableForms();
  } catch (error) {
    console.error(error);
    showFeedback(error.message, 'danger');
  }
}

function initChoiceHandlers() {
  if (!choiceForm) {
    return;
  }
  choiceForm.addEventListener('change', (event) => {
    if (event.target.name !== 'invite-mode') return;
    toggleForms(event.target.value);
  });
}

function initForms() {
  if (userForm) {
    userForm.addEventListener('submit', submitUser);
  }
  if (patientForm) {
    patientForm.addEventListener('submit', submitPatient);
  }
}

function initialize() {
  currentToken = extractToken();
  if (!currentToken) {
    showFeedback('No se encontró token de invitación en la URL.', 'danger');
    disableForms();
    return;
  }

  initChoiceHandlers();
  initForms();
  toggleForms('user');
  loadInvitation();
}

initialize();
