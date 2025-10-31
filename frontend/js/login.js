import { apiClient } from './api.js';
import { saveSession } from './auth.js';
import { parseXml, xmlNodeText, validateEmail } from './utils.js';

function handleLoginSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const email = form.elements['email'].value.trim();
  const password = form.elements['password'].value.trim();

  if (!validateEmail(email)) {
    displayError('Ingrese un correo electrónico válido.');
    return;
  }

  if (password.length < 8) {
    displayError('La contraseña debe tener al menos 8 caracteres.');
    return;
  }

  submitLogin(email, password, form);
}

async function submitLogin(email, password, form) {
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.dataset.originalText = submitButton.textContent;
  submitButton.textContent = 'Verificando…';

  try {
    const body = `<LoginRequest><email>${email}</email><password>${password}</password></LoginRequest>`;
    const xml = await apiClient.request('/auth/login', {
      method: 'POST',
      requireAuth: false,
      body
    });

    if (!xml) {
      throw new Error('Respuesta inesperada del servidor.');
    }

    const accessToken = xmlNodeText(xml, 'access_token');
    const refreshToken = xmlNodeText(xml, 'refresh_token');
    const roles = xmlNodeText(xml, 'roles').split(',').map((role) => role.trim()).filter(Boolean);
    const userId = xmlNodeText(xml, 'user_id');
    const orgId = xmlNodeText(xml, 'org_id');
    const organizationName = xmlNodeText(xml, 'organization_name');

    saveSession({
      accessToken,
      refreshToken,
      user: {
        id: userId,
        roles,
        org_id: orgId,
        organization_name: organizationName,
        email
      }
    });

    window.location.href = 'index.html';
  } catch (error) {
    console.error(error);
    const maybeXml = error.message.includes('<?xml') ? parseXml(error.message) : null;
    if (maybeXml) {
      displayError(xmlNodeText(maybeXml, 'message') || 'Error al iniciar sesión.');
    } else {
      displayError(error.message);
    }
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = submitButton.dataset.originalText;
  }
}

function displayError(message) {
  const container = document.getElementById('login-error');
  if (!container) return;
  container.textContent = message;
  container.hidden = false;
}

function initLogin() {
  document.body.classList.add('auth-layout');
  const form = document.getElementById('login-form');
  if (form) {
    form.addEventListener('submit', handleLoginSubmit);
  }
}

document.addEventListener('DOMContentLoaded', initLogin);
