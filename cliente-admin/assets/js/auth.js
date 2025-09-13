import { API } from "./api.js";
import { $ } from "./utils.js";
import { CONFIG } from "./config.js";
import { logger } from "./utils.js";

// Servicio de autenticación
class AuthService {
	constructor() {
		this.tokenKey = "jwt";
		this.userKey = "user";
		this.sessionTimer = null;
	}

	isAuthenticated() {
		return !!this.getToken();
	}

	getToken() {
		return localStorage.getItem(this.tokenKey);
	}

	getUser() {
		const userStr = localStorage.getItem(this.userKey);
		return userStr ? JSON.parse(userStr) : null;
	}

	async login(username, password) {
		try {
			const response = await API.login(username, password);
			this.setSession(response.token, response.user);
			return response;
		} catch (error) {
			logger.error("Login failed:", error);
			throw error;
		}
	}

	setSession(token, user) {
		localStorage.setItem(this.tokenKey, token);
		localStorage.setItem(this.userKey, JSON.stringify(user));
		this.startSessionTimer();
	}

	logout() {
		localStorage.removeItem(this.tokenKey);
		localStorage.removeItem(this.userKey);
		this.stopSessionTimer();
		window.location.href = "login.html";
	}

	startSessionTimer() {
		this.stopSessionTimer();
		this.sessionTimer = setTimeout(() => {
			alert("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.");
			this.logout();
		}, CONFIG.SESSION_TIMEOUT);
	}

	stopSessionTimer() {
		if (this.sessionTimer) {
			clearTimeout(this.sessionTimer);
			this.sessionTimer = null;
		}
	}

	requireAuth() {
		if (!this.isAuthenticated()) {
			window.location.href = "login.html";
			return false;
		}
		return true;
	}
}

export const authService = new AuthService();

export function wireLogout() {
	const btn = $("#btnLogout");
	if (btn) {
		btn.addEventListener("click", () => authService.logout());
	}
}
