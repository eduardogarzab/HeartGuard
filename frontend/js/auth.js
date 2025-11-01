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
    const xmlResponse = await sendXMLRequest("http://136.115.53.140:5000/auth/login", "POST", xmlBody);
    console.log("XML Response:", xmlResponse);
    
    const parser = new DOMParser();
    const xml = parser.parseFromString(xmlResponse, "application/xml");

    // Verificar si hay errores de parseo
    const parserError = xml.querySelector("parsererror");
    if (parserError) {
      console.error("Error al parsear XML:", parserError.textContent);
      message.textContent = "Error al procesar la respuesta del servidor";
      return;
    }

    // Buscar los nodos navegando por la estructura XML
    // La estructura es: response > data > tokens/user
    let accessTokenNode, refreshTokenNode, userIdNode, userNameNode, userEmailNode;
    
    // Buscar el nodo data
    const dataNode = xml.querySelector("data");
    if (dataNode) {
      // Buscar tokens dentro de data
      const tokensNode = dataNode.querySelector("tokens");
      if (tokensNode) {
        accessTokenNode = tokensNode.querySelector("access_token");
        refreshTokenNode = tokensNode.querySelector("refresh_token");
      }
      
      // Buscar user dentro de data
      const userNode = dataNode.querySelector("user");
      if (userNode) {
        userIdNode = userNode.querySelector("id");
        userNameNode = userNode.querySelector("name");
        userEmailNode = userNode.querySelector("email");
      }
    }

    console.log("Access Token:", accessTokenNode?.textContent?.substring(0, 50) + "...");
    console.log("User:", userNameNode?.textContent);
    console.log("Email:", userEmailNode?.textContent);
    console.log("User ID:", userIdNode?.textContent);

    if (accessTokenNode && userIdNode) {
      // Guardar tokens y datos de usuario
      localStorage.setItem("jwt", accessTokenNode.textContent);
      localStorage.setItem("refresh_token", refreshTokenNode?.textContent || "");
      localStorage.setItem("user_id", userIdNode.textContent);
      localStorage.setItem("user_name", userNameNode?.textContent || "");
      localStorage.setItem("user_email", userEmailNode?.textContent || "");
      
      // Extraer organizaciones del usuario
      const userNode = dataNode.querySelector("user");
      if (userNode) {
        const orgs = userNode.querySelectorAll("organizations item") || userNode.querySelectorAll("organization");
        if (orgs.length > 0) {
          const organizations = [];
          orgs.forEach(org => {
            const orgData = {
              id: org.querySelector("id")?.textContent,
              code: org.querySelector("code")?.textContent,
              name: org.querySelector("name")?.textContent,
              role_code: org.querySelector("role_code")?.textContent,
              role_name: org.querySelector("role_name")?.textContent
            };
            organizations.push(orgData);
          });
          
          // Guardar todas las organizaciones
          localStorage.setItem("organizations", JSON.stringify(organizations));
          
          // Guardar la primera organización como la activa (por defecto)
          if (organizations.length > 0) {
            localStorage.setItem("current_org_code", organizations[0].code);
            localStorage.setItem("current_org_name", organizations[0].name);
            localStorage.setItem("current_org_role", organizations[0].role_code);
          }
          
          console.log("Organizaciones del usuario:", organizations);
        }
      }
      
      // Decodificar el JWT para obtener roles (sin verificar la firma en el frontend)
      const tokenParts = accessTokenNode.textContent.split('.');
      if (tokenParts.length === 3) {
        try {
          const payload = JSON.parse(atob(tokenParts[1]));
          console.log("JWT Payload:", payload);
          
          // Guardar roles del JWT
          if (payload.roles) {
            localStorage.setItem("roles", JSON.stringify(payload.roles));
          }
        } catch (jwtError) {
          console.error("Error al decodificar JWT:", jwtError);
        }
      }
      
      message.textContent = "Autenticación exitosa, redirigiendo...";
      message.style.color = "green";
      
      // Redirigir al dashboard
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 500);
    } else {
      console.error("Nodos no encontrados en el XML");
      console.error("dataNode:", dataNode);
      message.textContent = "Error: Respuesta de autenticación inválida";
    }
  } catch (err) {
    console.error("Error completo:", err);
    message.textContent = "Error de autenticación: " + err.message;
  }
});
