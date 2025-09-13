import { authService } from "./auth.js";
import { $ } from "./utils.js";

async function doLogin(e, { redirect }) {
	e.preventDefault();
	const user = $("#loginUser").value;
	const pass = $("#loginPass").value;

	try {
		await authService.login(user, pass);
		location.href = redirect;
	} catch (err) {
		alert("Credenciales incorrectas. Intenta de nuevo.");
		console.error(err);
	}
}

// Espera a que el DOM esté completamente cargado para evitar problemas
document.addEventListener("DOMContentLoaded", () => {
	// Si ya hay sesión, entra directo al dashboard
	if (authService.isAuthenticated()) {
		location.href = "dashboard.html";
		return; // Detiene la ejecución para evitar añadir listeners innecesarios
	}

	const form = document.getElementById("formLogin");
	if (form) {
		form.addEventListener("submit", (e) => doLogin(e, { redirect: "dashboard.html" }));
	}
});
