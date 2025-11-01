export async function sendXMLRequest(url, method = "POST", xmlBody = null, token = null) {
  const headers = {
    "Content-Type": "application/xml",
    "Accept": "application/xml"
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const options = {
    method,
    headers
  };
  
  // Solo incluir body si no es GET o DELETE y si hay contenido
  if (method !== "GET" && method !== "DELETE" && xmlBody) {
    options.body = xmlBody;
  }

  const response = await fetch(url, options);

  const text = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${text}`);
  return text;
}
