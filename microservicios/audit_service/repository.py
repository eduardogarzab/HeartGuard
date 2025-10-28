from db import get_db
import json

def create_log_entry(data):
    """
    Inserta un nuevo registro de auditoría en la base de datos.
    'data' es un diccionario que coincide con los campos de la API.
    """
    db = get_db()
    cursor = db.cursor()
    
    # Extraer datos, proveyendo None como default si la llave no existe
    user_id = data.get('user_id')
    org_id = data.get('org_id')
    action = data.get('action')
    entity = data.get('entity')
    entity_id = data.get('entity_id')
    ip = data.get('ip')
    details = data.get('details') # Debe ser un dict
    
    # 'details' debe ser un string JSONB
    details_json = json.dumps(details) if details else None

    # Consulta SQL basada en la tabla 'audit_logs'
    sql = """
        INSERT INTO audit_logs 
        (user_id, org_id, action, entity, entity_id, ip, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, ts;
    """
    try:
        cursor.execute(sql, (
            user_id, org_id, action, entity, entity_id, ip, details_json
        ))
        new_log = cursor.fetchone()
        db.commit()
        return new_log
    except Exception as e:
        db.rollback()
        print(f"Error al insertar log: {e}")
        raise
    finally:
        cursor.close()

def get_logs(params):
    """
    Consulta registros de auditoría con filtros.
    'params' es un dict con query params: from_date, to_date, user_id, action.
    """
    db = get_db()
    cursor = db.cursor()
    
    # Base de la consulta
    sql = """
        SELECT l.id, l.ts, l.action, l.entity, l.entity_id, l.ip,
               u.email as user_email, o.name as org_name, l.details
        FROM audit_logs l
        LEFT JOIN users u ON l.user_id = u.id
        LEFT JOIN organizations o ON l.org_id = o.id
    """
    
    filters = []
    args = []
    
    # Construir filtros dinámicamente
    if params.get('from_date'):
        filters.append("l.ts >= %s")
        args.append(params['from_date'])
        
    if params.get('to_date'):
        filters.append("l.ts <= %s")
        args.append(params['to_date'])
        
    if params.get('user_id'):
        filters.append("l.user_id = %s")
        args.append(params['user_id'])
        
    if params.get('action'):
        filters.append("l.action = %s")
        args.append(params['action'])

    if filters:
        sql += " WHERE " + " AND ".join(filters)
        
    sql += " ORDER BY l.ts DESC LIMIT 100;" # Limitar a 100 resultados

    try:
        cursor.execute(sql, tuple(args))
        logs = cursor.fetchall()
        return logs
    except Exception as e:
        print(f"Error al consultar logs: {e}")
        raise
    finally:
        cursor.close()