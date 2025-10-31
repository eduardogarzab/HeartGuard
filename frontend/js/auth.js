const LOGIN_PAGE = 'login.html';
const SESSION_KEYS = ['access_token', 'refresh_token', 'user'];

export function saveSession({ accessToken, refreshToken, user }) {
  if (accessToken) localStorage.setItem('access_token', accessToken);
  if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
  if (user) localStorage.setItem('user', JSON.stringify(user));
}

export function getCurrentUser() {
  const stored = localStorage.getItem('user');
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch (error) {
    console.error('Unable to parse stored user', error);
    return null;
  }
}

export function getOrgId() {
  return getCurrentUser()?.org_id ?? null;
}

export function hasRole(role) {
  const roles = getCurrentUser()?.roles ?? [];
  return roles.includes(role);
}

export function requireAuth() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  const user = getCurrentUser();

  if (!accessToken || !refreshToken || !user) {
    redirectToLogin();
    return;
  }

  attachUserMenu();
}

export function logout() {
  SESSION_KEYS.forEach((key) => localStorage.removeItem(key));
  redirectToLogin();
}

function redirectToLogin() {
  if (!window.location.pathname.endsWith(LOGIN_PAGE)) {
    window.location.href = LOGIN_PAGE;
  }
}

function attachUserMenu() {
  const menuButton = document.querySelector('[data-user-menu-button]');
  const menu = document.querySelector('[data-user-menu]');
  if (!menuButton || !menu) return;

  menuButton.addEventListener('click', () => {
    const expanded = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!expanded));
    menu.setAttribute('aria-hidden', String(expanded));
  });

  document.addEventListener('click', (event) => {
    if (!menu.contains(event.target) && event.target !== menuButton) {
      menuButton.setAttribute('aria-expanded', 'false');
      menu.setAttribute('aria-hidden', 'true');
    }
  });

  const logoutButton = menu.querySelector('[data-logout]');
  if (logoutButton) {
    logoutButton.addEventListener('click', () => logout());
  }
}
