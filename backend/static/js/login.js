document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await res.json();

  if (res.status !== 200) {
    document.getElementById("error").innerText = data.error || "Error al iniciar sesión";
    return;
  }

  // ⚡ Solo admins pueden usar este backend
  if (data.role === "admin") {
    localStorage.setItem("org_id", data.org_id);
    localStorage.setItem("role", "admin");
    localStorage.setItem("username", username);

    window.location.href = "/admin";
  } else {
    document.getElementById("error").innerText = "Acceso denegado: este portal es solo para administradores.";
  }
});
