export async function sendXMLRequest(url, method = "POST", xmlBody = null, token = null) {
  const headers = {
    "Content-Type": "application/xml",
    "Accept": "application/xml"
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(url, {
    method,
    headers,
    body: xmlBody
  });

  const text = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${text}`);
  return text;
}
