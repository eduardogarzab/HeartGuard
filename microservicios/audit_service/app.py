import os
from flask import Flask, jsonify, request
from config import settings
import db
import repository

app = Flask(__name__)
db.init_app(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Verificación de salud del servicio."""
    return jsonify({"status": "ok", "service": "audit_service"}), 200


@app.route('/v1/audit', methods=['POST'])
def create_audit_log():
    """
    Endpoint para CREAR un nuevo registro de auditoría.
    Llamado por otros microservicios (a través del Gateway).
    """
    data = request.get_json()
    if not data or not data.get('action'):
        return jsonify({"message": "El campo 'action' es requerido"}), 400
    
    try:
        new_log = repository.create_log_entry(data)
        return jsonify(new_log), 201
    except Exception as e:
        return jsonify({"message": "Error interno al crear log", "error": str(e)}), 500


@app.route('/v1/audit', methods=['GET'])
def get_audit_logs():
    """
    Endpoint para CONSULTAR registros de auditoría.
    Usado por el panel de superadmin (a través del Gateway).
    Filtros: from_date, to_date, user_id, action
    """
    params = {
        'from_date': request.args.get('from'),
        'to_date': request.args.get('to'),
        'user_id': request.args.get('user_id'),
        'action': request.args.get('action')
    }
    # Filtrar params que son None
    query_params = {k: v for k, v in params.items() if v is not None}
    
    try:
        logs = repository.get_logs(query_params)
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({"message": "Error interno al consultar logs", "error": str(e)}), 500


if __name__ == '__main__':
    port = settings.SERVICE_PORT
    debug = settings.FLASK_ENV == 'development'
    print(f"--- Iniciando AuditService en modo {'DEBUG' if debug else 'PROD'} en puerto {port} ---")
    app.run(host='0.0.0.0', port=port, debug=debug)