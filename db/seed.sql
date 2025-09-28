-- =========================================================
-- HeartGuard DB (v2.5) - SEED (datos iniciales)
-- =========================================================

-- Requerido para bcrypt (crypt/gen_salt) y gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Catálogos base
INSERT INTO user_statuses(code,label) VALUES
  ('active','Activo'),('blocked','Bloqueado'),('pending','Pendiente')
ON CONFLICT (code) DO NOTHING;

INSERT INTO sexes(code,label) VALUES
  ('M','Masculino'),('F','Femenino'),('O','Otro/No especifica')
ON CONFLICT (code) DO NOTHING;

INSERT INTO signal_types(code,label) VALUES
  ('ECG','Electrocardiograma (ECG)'),
  ('HR','Frecuencia cardiaca'),
  ('SpO2','Saturación oxígeno'),
  ('HRV','Variabilidad FC'),
  ('BP','Presión arterial')
ON CONFLICT (code) DO NOTHING;

INSERT INTO alert_channels(code,label) VALUES
  ('SMS','Mensaje SMS'),('EMAIL','Correo electrónico'),('PUSH','Notificación push')
ON CONFLICT (code) DO NOTHING;

INSERT INTO alert_levels(code,weight,label) VALUES
  ('low',1,'Bajo'),('medium',2,'Medio'),('high',3,'Alto'),('critical',4,'Crítico')
ON CONFLICT (code) DO NOTHING;

INSERT INTO platforms(code,label) VALUES
  ('android','Android'),('ios','iOS'),('web','Web')
ON CONFLICT (code) DO NOTHING;

INSERT INTO service_statuses(code,label) VALUES
  ('up','Operativo'),('down','Caído'),('error','Error'),('degraded','Degradado')
ON CONFLICT (code) DO NOTHING;

INSERT INTO delivery_statuses(code,label) VALUES
  ('SENT','Enviado'),('DELIVERED','Entregado'),('FAILED','Fallido')
ON CONFLICT (code) DO NOTHING;

INSERT INTO batch_export_statuses(code,label) VALUES
  ('queued','En cola'),('running','Ejecutando'),('done','Completado'),('error','Error')
ON CONFLICT (code) DO NOTHING;

-- Roles globales y permisos
INSERT INTO roles(name, description) VALUES
  ('superadmin','Full system access'),
  ('clinician','Healthcare professional'),
  ('caregiver','Family/guardian'),
  ('ops','Operations/DevOps')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions(code, description) VALUES
  ('alerts.read','Ver alertas'),
  ('alerts.manage','Atender/cerrar alertas'),
  ('patients.read','Ver pacientes'),
  ('patients.manage','Crear/editar pacientes'),
  ('services.read','Ver servicios'),
  ('services.manage','Configurar servicios')
ON CONFLICT (code) DO NOTHING;

-- superadmin: todos los permisos
INSERT INTO role_permission(role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
WHERE r.name='superadmin'
ON CONFLICT DO NOTHING;

-- clinician / caregiver: lectura básica
INSERT INTO role_permission(role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p ON p.code IN ('alerts.read','patients.read')
WHERE r.name IN ('clinician','caregiver')
ON CONFLICT DO NOTHING;

-- ops: servicios.*
INSERT INTO role_permission(role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p ON p.code IN ('services.read','services.manage')
WHERE r.name='ops'
ON CONFLICT DO NOTHING;

-- Estados de alerta
INSERT INTO alert_status(code, description, step_order) VALUES
  ('created','Generada por regla/modelo',1),
  ('notified','Notificada a canal/es',2),
  ('ack','Reconocida por usuario',3),
  ('resolved','Resuelta',4),
  ('closed','Cerrada',5)
ON CONFLICT (code) DO NOTHING;

-- Tipos de alerta (rango de severidad por nivel)
INSERT INTO alert_types(code, description, severity_min_id, severity_max_id)
SELECT x.code, x.description,
       (SELECT id FROM alert_levels WHERE code = x.min_code),
       (SELECT id FROM alert_levels WHERE code = x.max_code)
FROM (VALUES
  ('ARRHYTHMIA','Ritmo cardiaco anómalo','medium','critical'),
  ('DESAT','Desaturación de oxígeno','low','critical'),
  ('HYPERTENSION','Presión arterial elevada','medium','critical')
) AS x(code,description,min_code,max_code)
ON CONFLICT (code) DO NOTHING;

-- Tipos de evento (severidad por defecto)
INSERT INTO event_types(code, description, severity_default_id)
SELECT x.code, x.description, (SELECT id FROM alert_levels WHERE code = x.def_level)
FROM (VALUES
  ('AFIB','Fibrilación auricular','high'),
  ('TACHY','Taquicardia','medium'),
  ('DESAT','Desaturación O2','high'),
  ('HYPERTENSION','Hipertensión','medium')
) AS x(code,description,def_level)
ON CONFLICT (code) DO NOTHING;

-- Tipos de dispositivo
INSERT INTO device_types(code, description) VALUES
  ('ECG_1LEAD','ECG de una derivación'),
  ('PULSE_OX','Pulsioxímetro')
ON CONFLICT (code) DO NOTHING;

-- Roles por organización
INSERT INTO org_roles(code,label) VALUES
  ('org_admin','Administrador de organización'),
  ('org_user','Usuario de organización'),
  ('viewer','Solo lectura')
ON CONFLICT (code) DO NOTHING;

-- Relación cuidador
INSERT INTO caregiver_relationship_types(code,label) VALUES
 ('parent','Padre/Madre'),('spouse','Esposo/a'),('sibling','Hermano/a'),
 ('child','Hijo/a'),('friend','Amigo/a')
ON CONFLICT (code) DO NOTHING;

-- =========================================================
-- Usuario superadmin demo (password fijo: Admin#2025)
-- - Usa bcrypt generado por pgcrypto (crypt + gen_salt('bf', 10))
-- - ON CONFLICT actualiza password/status para mantener el acceso
-- =========================================================
INSERT INTO users (name, email, password_hash, user_status_id, two_factor_enabled, created_at)
VALUES (
  'Super Admin',
  'admin@heartguard.com',
  crypt('Admin#2025', gen_salt('bf', 10)),
  (SELECT id FROM user_statuses WHERE code='active'),
  FALSE,
  NOW()
)
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    password_hash = EXCLUDED.password_hash,
    user_status_id = EXCLUDED.user_status_id;

-- Asignar rol superadmin
INSERT INTO user_role(user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.email='admin@heartguard.com' AND r.name='superadmin'
ON CONFLICT DO NOTHING;

-- Organización demo
INSERT INTO organizations(code,name) VALUES ('FAM-001','Familia García')
ON CONFLICT (code) DO NOTHING;
