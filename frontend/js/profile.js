import { apiClient } from './api.js';
import { requireAuth, getCurrentUser } from './auth.js';
import { initSidebarToggle } from './utils.js';

let form;
let feedback;

function populateUserContext() {
  const user = getCurrentUser();
  const orgName = document.querySelector('[data-org-name]');
  if (orgName && user?.organization_name) {
    orgName.textContent = user.organization_name;
  }
}

function loadProfile() {
  const user = getCurrentUser();
  if (!user || !form) return;
  form.elements['language'].value = localStorage.getItem('pref_language') || 'es';
  form.elements['timezone'].value = localStorage.getItem('pref_timezone') || Intl.DateTimeFormat().resolvedOptions().timeZone;
  form.elements['notifications'].checked = localStorage.getItem('pref_notifications') !== 'off';
  form.elements['theme'].value = localStorage.getItem('pref_theme') || 'light';
  form.elements['email'].value = user.email;
}

function setFeedback(message, variant = 'info') {
  if (!feedback) return;
  feedback.hidden = false;
  feedback.textContent = message;
  feedback.className = `alert alert--${variant}`;
}

async function handleSubmit(event) {
  event.preventDefault();
  const user = getCurrentUser();
  if (!user) return;
  const formData = new FormData(form);
  const body = `
    <UserPreferences>
      <language>${formData.get('language')}</language>
      <timezone>${formData.get('timezone')}</timezone>
      <notifications>${formData.get('notifications') ? 'on' : 'off'}</notifications>
      <theme>${formData.get('theme')}</theme>
    </UserPreferences>
  `;
  try {
    await apiClient.request(`/users/${user.id}`, {
      method: 'PATCH',
      body
    });
    localStorage.setItem('pref_language', formData.get('language'));
    localStorage.setItem('pref_timezone', formData.get('timezone'));
    localStorage.setItem('pref_notifications', formData.get('notifications') ? 'on' : 'off');
    localStorage.setItem('pref_theme', formData.get('theme'));
    setFeedback('Preferencias actualizadas correctamente.', 'success');
  } catch (error) {
    console.error(error);
    setFeedback(error.message, 'danger');
  }
}

function init() {
  requireAuth();
  initSidebarToggle();
  populateUserContext();
  form = document.getElementById('profile-form');
  feedback = document.getElementById('profile-feedback');
  if (form) {
    form.addEventListener('submit', handleSubmit);
  }
  loadProfile();
}

document.addEventListener('DOMContentLoaded', init);
