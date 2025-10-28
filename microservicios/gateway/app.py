from __future__ import annotations

import os
import requests
from flask import Flask, request, jsonify, Response, g

from config import Config
from middleware.auth import token_required

app = Flask(__name__)
app.config.from_object(Config)


def _load_service_map() -> dict[str, str]:
    """Construye el mapa prefix -> URL destino, permitiendo overrides por env."""

    base_map = {
        "auth": Config.AUTH_SERVICE_URL,
        "orgs": Config.ORG_SERVICE_URL,
    # Mientras no exista patient_service reutilizamos org_service
    "patients": Config.ORG_SERVICE_URL,
    "audit": Config.AUDIT_SERVICE_URL,
    }

    raw_map = os.getenv("GATEWAY_SERVICE_MAP", "")
    if raw_map:
        for entry in raw_map.split(","):
            chunk = entry.strip()
            if not chunk:
                continue
            if "=" not in chunk:
                print(f"[Gateway] Ignorando entrada inválida en GATEWAY_SERVICE_MAP: '{chunk}'")
                continue
            prefix, url = chunk.split("=", 1)
            prefix = prefix.strip().strip("/")
            url = url.strip().rstrip("/")
            if not prefix or not url:
                print(f"[Gateway] Entrada incompleta para prefix '{prefix}' en GATEWAY_SERVICE_MAP")
                continue
            base_map[prefix] = url

    service_map = {prefix: url.rstrip("/") for prefix, url in base_map.items() if url}
    print("[Gateway] Rutas activas:", ", ".join(f"{p} -> {u}" for p, u in service_map.items()))
    return service_map


SERVICE_MAP = _load_service_map()

def _proxy_request(service_url: str, path: str):
    """Reenvía la petición entrante al microservicio correspondiente."""

    base_url = service_url.rstrip('/')
    sanitized_path = path.lstrip('/')
    destination_url = f"{base_url}/{sanitized_path}" if sanitized_path else base_url

    if request.query_string:
        destination_url += f"?{request.query_string.decode('utf-8')}"

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}

    if 'x-org-id' not in (k.lower() for k in headers.keys()):
        if hasattr(g, 'org_id') and g.org_id:
            headers['x-org-id'] = str(g.org_id)

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and 'x-forwarded-for' not in (k.lower() for k in headers.keys()):
        headers['X-Forwarded-For'] = client_ip
    if 'x-forwarded-proto' not in (k.lower() for k in headers.keys()):
        headers['X-Forwarded-Proto'] = request.scheme

    try:
        resp = requests.request(
            method=request.method,
            url=destination_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=15
        )

        excluded_headers = {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}
        response_headers = [
            (name, value) for (name, value) in resp.headers.items()
            if name.lower() not in excluded_headers
        ]

        return Response(resp.content, resp.status_code, response_headers)

    except requests.exceptions.ConnectionError:
        return jsonify({"message": f"Error de conexión con el servicio: {service_url}"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"message": f"Timeout del servicio: {service_url}"}), 504
    except Exception as e:
        return jsonify({"message": "Error interno del gateway", "error": str(e)}), 500


# --- Rutas Protegidas (Requieren JWT) ---
@app.route('/v1/<service_prefix>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], defaults={'path': ''})
@app.route('/v1/<service_prefix>/', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], defaults={'path': ''})
@app.route('/v1/<service_prefix>/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@token_required
def proxy_protected(service_prefix, path):
    """Catch-all para peticiones autenticadas hacia los microservicios internos."""
    service_url = SERVICE_MAP.get(service_prefix)
    if not service_url:
        return jsonify({"message": "Servicio no encontrado"}), 404

    normalized_path = path or ''
    if normalized_path:
        full_path = f"v1/{service_prefix}/{normalized_path}"
    else:
        full_path = f"v1/{service_prefix}"

    return _proxy_request(service_url, full_path)


# --- Rutas Públicas (Sin JWT) ---
# Debes definir explícitamente qué rutas NO necesitan token.
# Estas rutas NO usan @token_required.

@app.route('/v1/auth/login', methods=['POST'])
def proxy_login():
    """Ruta proxy pública para login."""
    return _proxy_request(Config.AUTH_SERVICE_URL, 'v1/auth/login')

@app.route('/v1/auth/register', methods=['POST'])
def proxy_register():
    """Ruta proxy pública para register."""
    return _proxy_request(Config.AUTH_SERVICE_URL, 'v1/auth/register')

@app.route('/v1/auth/refresh', methods=['POST'])
def proxy_refresh():
    """Ruta proxy pública para refresh token."""
    return _proxy_request(Config.AUTH_SERVICE_URL, 'v1/auth/refresh')

@app.route('/health', methods=['GET'])
def health_check():
    """Verificación de salud del Gateway."""
    return jsonify({"status": "ok", "service": "gateway"}), 200


if __name__ == '__main__':
    port = Config.SERVICE_PORT
    debug = Config.FLASK_ENV == 'development'
    print(f"--- Iniciando Gateway en modo {'DEBUG' if debug else 'PROD'} en puerto {port} ---")
    app.run(host='0.0.0.0', port=port, debug=debug)