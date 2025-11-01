import { sendXMLRequest } from "./xmlClient.js";

const form = document.getElementById("loginForm");
const message = document.getElementById("loginMessage");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  message.textContent = "Autenticando...";

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const xmlBody = `
    <login_request>
      <email>${email}</email>
      <password>${password}</password>
    </login_request>
  `;

  try {
    const xmlResponse = await sendXMLRequest("http://136.115.53.140:5001/auth/login", "POST", xmlBody);
    const parser = new DOMParser();
    const xml = parser.parseFromString(xmlResponse, "application/xml");

    const tokenNode = xml.querySelector("token");
    const roleNode = xml.querySelector("role");
    const orgNode = xml.querySelector("organization_id");

    if (tokenNode && roleNode && roleNode.textContent === "org_admin") {
      localStorage.setItem("jwt", tokenNode.textContent);
      localStorage.setItem("organization_id", orgNode ? orgNode.textContent : "");
      window.location.href = "dashboard.html";
    } else {
      message.textContent = "Acceso restringido. Solo administradores.";
    }
  } catch (err) {
    message.textContent = "Error de autenticación: " + err.message;
  }
});
