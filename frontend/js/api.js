import { parseXml } from './utils.js';
import { logout } from './auth.js';

const API_BASE_URL = 'http://34.70.7.33:5000';

class XMLApiClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request(path, { method = 'GET', body = null, requireAuth = true, headers = {} } = {}) {
    const requestHeaders = {
      'Content-Type': 'application/xml',
      Accept: 'application/xml',
      ...headers
    };

    const accessToken = localStorage.getItem('access_token');
    if (requireAuth && accessToken) {
      requestHeaders.Authorization = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: requestHeaders,
      body
    });

    if (response.status === 401 || response.status === 403) {
      const refreshed = await this.tryRefreshToken();
      if (!refreshed) {
        logout();
        return null;
      }
      return this.request(path, { method, body, requireAuth, headers });
    }

    const text = await response.text();

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      if (text) {
        try {
          const xmlError = parseXml(text);
          const xmlMessage = xmlError.querySelector('message')?.textContent;
          if (xmlMessage) {
            errorMessage = xmlMessage;
          }
        } catch (parseError) {
          errorMessage = `${errorMessage}: ${text}`;
        }
      }
      throw new Error(errorMessage);
    }

    if (!text) {
      return null;
    }
    return parseXml(text);
  }

  async tryRefreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/xml',
          Accept: 'application/xml'
        },
        body: `<RefreshRequest><refresh_token>${refreshToken}</refresh_token></RefreshRequest>`
      });

      if (!response.ok) {
        return false;
      }

      const xml = parseXml(await response.text());
      const newAccessToken = xml.querySelector('access_token')?.textContent;
      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to refresh token', error);
      return false;
    }
  }
}

export const apiClient = new XMLApiClient();
