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

function parseBoolean(value, defaultValue = false) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (['1', 'true', 'yes', 'on'].includes(normalized)) return true;
    if (['0', 'false', 'no', 'off'].includes(normalized)) return false;
  }
  return defaultValue;
}

function readUserPreferencesFromXml(userNode) {
  const preferences = {
    language: userNode.querySelector('language')?.textContent?.trim() || '',
    timezone: userNode.querySelector('timezone')?.textContent?.trim() || '',
    theme: userNode.querySelector('theme')?.textContent?.trim() || '',
    notificationsEnabled: true
  };

  const notificationsNode = userNode.querySelector('notifications');
  if (notificationsNode) {
    const emailNode = notificationsNode.querySelector('email');
    const smsNode = notificationsNode.querySelector('sms');
    const pushNode = notificationsNode.querySelector('push');
    if (emailNode || smsNode || pushNode) {
      const email = parseBoolean(emailNode?.textContent ?? '', false);
      const sms = parseBoolean(smsNode?.textContent ?? '', false);
      const push = parseBoolean(pushNode?.textContent ?? '', false);
      preferences.notificationsEnabled = email || sms || push;
    } else {
      preferences.notificationsEnabled = parseBoolean(notificationsNode.textContent, true);
    }
  }

  return preferences;
}

async function loadProfile() {
  const user = getCurrentUser();
  if (!user || !form) return;

  const cachedLanguage = localStorage.getItem('pref_language') || '';
  const cachedTimezone = localStorage.getItem('pref_timezone') || '';
  const cachedTheme = localStorage.getItem('pref_theme') || '';
  const cachedNotifications = localStorage.getItem('pref_notifications');

  form.elements['language'].value = cachedLanguage || 'es';
  form.elements['timezone'].value = cachedTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  form.elements['notifications'].checked = cachedNotifications ? cachedNotifications !== 'off' : true;
  form.elements['theme'].value = cachedTheme || 'light';
  form.elements['email'].value = user.email;

  try {
    const xml = await apiClient.request(`/users/${user.id}`);
    if (!xml) return;
    const userNode = xml.querySelector('response > data > user');
    if (!userNode) return;
    const preferences = readUserPreferencesFromXml(userNode);

    const language = preferences.language || 'es';
    const timezone = preferences.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    const theme = preferences.theme || 'light';
    const notificationsEnabled = preferences.notificationsEnabled;

    form.elements['language'].value = language;
    form.elements['timezone'].value = timezone;
    form.elements['notifications'].checked = notificationsEnabled;
    form.elements['theme'].value = theme;

    localStorage.setItem('pref_language', language);
    localStorage.setItem('pref_timezone', timezone);
    localStorage.setItem('pref_notifications', notificationsEnabled ? 'on' : 'off');
    localStorage.setItem('pref_theme', theme);
  } catch (error) {
    console.error('Failed to load profile preferences', error);
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
  const user = getCurrentUser();
  if (!user) return;
  const formData = new FormData(form);
  const notificationsEnabled = Boolean(formData.get('notifications'));
  const body = `
    <UserPreferences>
      <language>${formData.get('language')}</language>
      <timezone>${formData.get('timezone')}</timezone>
      <theme>${formData.get('theme')}</theme>
      <notifications>
        <email>${notificationsEnabled}</email>
        <sms>${notificationsEnabled}</sms>
        <push>${notificationsEnabled}</push>
      </notifications>
    </UserPreferences>
  `;
  try {
    const xml = await apiClient.request(`/users/${user.id}`, {
      method: 'PATCH',
      body
    });
    if (xml) {
      const userNode = xml.querySelector('response > data > user');
      if (userNode) {
        const preferences = readUserPreferencesFromXml(userNode);
        const language = preferences.language || formData.get('language') || 'es';
        const timezone = preferences.timezone || formData.get('timezone') || Intl.DateTimeFormat().resolvedOptions().timeZone;
        const theme = preferences.theme || formData.get('theme') || 'light';
        const notifications = preferences.notificationsEnabled;

        localStorage.setItem('pref_language', language);
        localStorage.setItem('pref_timezone', timezone);
        localStorage.setItem('pref_notifications', notifications ? 'on' : 'off');
        localStorage.setItem('pref_theme', theme);
      }
    }
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
