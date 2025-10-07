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

INSERT INTO system_settings (id, brand_name, support_email, primary_color, secondary_color, logo_url, contact_phone, default_locale, default_timezone, maintenance_mode, maintenance_message)
VALUES (1, 'HeartGuard', 'support@heartguard.com', '#0ea5e9', '#1e293b', NULL, '+52 55 1234 5678', 'es-MX', 'America/Mexico_City', FALSE, NULL)
ON CONFLICT (id) DO NOTHING;

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

INSERT INTO content_categories(code,label,color) VALUES
  ('clinical_guides','Guías clínicas','#38bdf8'),
  ('alert_protocols','Protocolos de alerta','#f97316'),
  ('faq','Preguntas frecuentes','#22d3ee'),
  ('education','Educación','#a855f7'),
  ('communications','Comunicaciones','#f43f5e')
ON CONFLICT (code) DO NOTHING;

INSERT INTO content_statuses(code,label,weight) VALUES
  ('draft','Borrador',10),
  ('in_review','En revisión',20),
  ('scheduled','Programado',30),
  ('published','Publicado',40),
  ('archived','Archivado',50)
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

INSERT INTO organizations(code,name) VALUES
  ('CLIN-001','Clínica Central'),
  ('OPS-001','Servicios Operativos HG')
ON CONFLICT (code) DO NOTHING;

-- Usuarios adicionales para métricas (password demo: Demo#2025)
INSERT INTO users (name, email, password_hash, user_status_id, two_factor_enabled, created_at)
VALUES
  ('Dra. Ana Ruiz','ana.ruiz@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='active'), TRUE, NOW() - INTERVAL '90 days'),
  ('Martín López','martin.ops@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='active'), FALSE, NOW() - INTERVAL '60 days'),
  ('Sofía Care','sofia.care@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='pending'), FALSE, NOW() - INTERVAL '15 days'),
  ('Carlos Vega','carlos.vega@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='blocked'), FALSE, NOW() - INTERVAL '120 days')
ON CONFLICT (email) DO NOTHING;

-- Asignar roles globales
INSERT INTO user_role(user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = 'clinician'
WHERE u.email = 'ana.ruiz@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO user_role(user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = 'ops'
WHERE u.email = 'martin.ops@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO user_role(user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = 'caregiver'
WHERE u.email = 'sofia.care@heartguard.com'
ON CONFLICT DO NOTHING;

-- Membresías por organización
INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
SELECT o.id, u.id, r.id, NOW() - INTERVAL '60 days'
FROM organizations o, users u, org_roles r
WHERE o.code='FAM-001' AND u.email='ana.ruiz@heartguard.com' AND r.code='org_admin'
ON CONFLICT (org_id, user_id) DO NOTHING;

INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
SELECT o.id, u.id, r.id, NOW() - INTERVAL '45 days'
FROM organizations o, users u, org_roles r
WHERE o.code='FAM-001' AND u.email='martin.ops@heartguard.com' AND r.code='org_user'
ON CONFLICT (org_id, user_id) DO NOTHING;

INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
SELECT o.id, u.id, r.id, NOW() - INTERVAL '20 days'
FROM organizations o, users u, org_roles r
WHERE o.code='CLIN-001' AND u.email='sofia.care@heartguard.com' AND r.code='viewer'
ON CONFLICT (org_id, user_id) DO NOTHING;

-- Invitaciones demo (pendiente, usada, revocada)
INSERT INTO org_invitations (org_id, email, org_role_id, token, expires_at, used_at, revoked_at, created_by, created_at)
VALUES
  (
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'coordinador@heartguard.com',
    (SELECT id FROM org_roles WHERE code='org_admin'),
    'INVITE-DEMO-001',
    NOW() + INTERVAL '7 days',
    NULL,
    NULL,
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    NOW() - INTERVAL '2 days'
  ),
  (
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'analista@heartguard.com',
    (SELECT id FROM org_roles WHERE code='org_user'),
    'INVITE-DEMO-002',
    NOW() - INTERVAL '10 days',
    NOW() - INTERVAL '9 days',
    NULL,
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    NOW() - INTERVAL '12 days'
  ),
  (
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'visitante@heartguard.com',
    (SELECT id FROM org_roles WHERE code='viewer'),
    'INVITE-DEMO-003',
    NOW() + INTERVAL '14 days',
    NULL,
    NOW() - INTERVAL '3 days',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    NOW() - INTERVAL '5 days'
  )
ON CONFLICT (token) DO NOTHING;

-- Servicios y health checks
INSERT INTO services(name, url, description) VALUES
  ('superadmin-api','https://admin.heartguard.local','API Superadmin'),
  ('streaming-hub','https://stream.heartguard.local','Canal de telemetría')
ON CONFLICT (name) DO NOTHING;

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT '00000000-0000-0000-0000-00000000A101'::uuid,
       (SELECT id FROM services WHERE name='superadmin-api'),
       NOW() - INTERVAL '2 days',
       (SELECT id FROM service_statuses WHERE code='up'),
       215,
       '1.8.4'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='00000000-0000-0000-0000-00000000A101'::uuid);

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT '00000000-0000-0000-0000-00000000A102'::uuid,
       (SELECT id FROM services WHERE name='superadmin-api'),
       NOW() - INTERVAL '6 hours',
       (SELECT id FROM service_statuses WHERE code='degraded'),
       380,
       '1.8.5'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='00000000-0000-0000-0000-00000000A102'::uuid);

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT '00000000-0000-0000-0000-00000000A103'::uuid,
       (SELECT id FROM services WHERE name='streaming-hub'),
       NOW() - INTERVAL '1 day',
       (SELECT id FROM service_statuses WHERE code='up'),
       180,
       '2.4.1'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='00000000-0000-0000-0000-00000000A103'::uuid);

-- Contenido editorial demo
INSERT INTO content_items (id, title, category_id, status_id, author_user_id, summary, created_at, updated_at, published_at)
VALUES
  (
    '00000000-0000-0000-0000-000000000101',
    'Guía rápida de monitoreo post-operatorio',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    'Checklist actualizado para pacientes en recuperación cardiovascular.',
    NOW() - INTERVAL '330 days',
    NOW() - INTERVAL '200 days',
    NOW() - INTERVAL '327 days'
  ),
  (
    '00000000-0000-0000-0000-000000000102',
    'Protocolos de triage cardiaco',
    (SELECT id FROM content_categories WHERE code='alert_protocols'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'Flujo para escalar alertas críticas en menos de cinco minutos.',
    NOW() - INTERVAL '270 days',
    NOW() - INTERVAL '40 days',
    NOW() - INTERVAL '266 days'
  ),
  (
    '00000000-0000-0000-0000-000000000103',
    'Preguntas frecuentes sobre telemetría domiciliaria',
    (SELECT id FROM content_categories WHERE code='faq'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM users WHERE email='sofia.care@heartguard.com'),
    'Respuestas rápidas para cuidadores sobre dispositivos y soporte.',
    NOW() - INTERVAL '210 days',
    NOW() - INTERVAL '25 days',
    NOW() - INTERVAL '205 days'
  ),
  (
    '00000000-0000-0000-0000-000000000104',
    'Boletín educativo: manejo de hipertensión',
    (SELECT id FROM content_categories WHERE code='education'),
    (SELECT id FROM content_statuses WHERE code='scheduled'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    'Campaña educativa para pacientes con seguimiento remoto.',
    NOW() - INTERVAL '150 days',
    NOW() - INTERVAL '7 days',
    NOW() + INTERVAL '12 days'
  ),
  (
    '00000000-0000-0000-0000-000000000105',
    'Script de seguimiento telefónico',
    (SELECT id FROM content_categories WHERE code='communications'),
    (SELECT id FROM content_statuses WHERE code='in_review'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'Guion para llamadas de verificación después de eventos de riesgo.',
    NOW() - INTERVAL '110 days',
    NOW() - INTERVAL '12 days',
    NULL
  ),
  (
    '00000000-0000-0000-0000-000000000106',
    'Protocolo de cierre de alertas',
    (SELECT id FROM content_categories WHERE code='alert_protocols'),
    (SELECT id FROM content_statuses WHERE code='archived'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'Procedimiento histórico para cerrar alertas tras verificación manual.',
    NOW() - INTERVAL '380 days',
    NOW() - INTERVAL '320 days',
    NOW() - INTERVAL '376 days'
  ),
  (
    '00000000-0000-0000-0000-000000000107',
    'Guía de configuración para nuevos dispositivos',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='draft'),
    (SELECT id FROM users WHERE email='sofia.care@heartguard.com'),
    'Procedimiento paso a paso para instalar sensores domiciliarios.',
    NOW() - INTERVAL '45 days',
    NOW() - INTERVAL '5 days',
    NULL
  ),
  (
    '00000000-0000-0000-0000-000000000108',
    'Resumen semanal de incidencias',
    (SELECT id FROM content_categories WHERE code='communications'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'Resumen ejecutivo con insights del monitoreo semanal.',
    NOW() - INTERVAL '20 days',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '18 days'
  ),
  (
    '00000000-0000-0000-0000-000000000109',
    'Checklist pre-implante para dispositivos implantables',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    'Evaluación previa a la implantación de sensores cardíacos.',
    NOW() - INTERVAL '420 days',
    NOW() - INTERVAL '260 days',
    NOW() - INTERVAL '415 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_updates (id, content_id, editor_user_id, change_type, note, created_at)
VALUES
  ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000101', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'review', 'Se actualizó tabla de signos vitales.', NOW() - INTERVAL '320 days'),
  ('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000101', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'edit', 'Se añadió checklist quirúrgico.', NOW() - INTERVAL '210 days'),
  ('00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000102', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Se incorporaron tiempos objetivo de respuesta.', NOW() - INTERVAL '60 days'),
  ('00000000-0000-0000-0000-000000000204', '00000000-0000-0000-0000-000000000102', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Validación operativa.', NOW() - INTERVAL '35 days'),
  ('00000000-0000-0000-0000-000000000205', '00000000-0000-0000-0000-000000000103', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'edit', 'Se añadieron preguntas sobre conectividad.', NOW() - INTERVAL '120 days'),
  ('00000000-0000-0000-0000-000000000206', '00000000-0000-0000-0000-000000000103', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Clarificación sobre soporte técnico.', NOW() - INTERVAL '20 days'),
  ('00000000-0000-0000-0000-000000000207', '00000000-0000-0000-0000-000000000104', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'edit', 'Actualización de gráficos de presión arterial.', NOW() - INTERVAL '30 days'),
  ('00000000-0000-0000-0000-000000000208', '00000000-0000-0000-0000-000000000104', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'review', 'Se programó envío a pacientes.', NOW() - INTERVAL '5 days'),
  ('00000000-0000-0000-0000-000000000209', '00000000-0000-0000-0000-000000000105', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Ajuste de tiempos de seguimiento.', NOW() - INTERVAL '28 days'),
  ('00000000-0000-0000-0000-00000000020A', '00000000-0000-0000-0000-000000000105', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Retroalimentación de calidad.', NOW() - INTERVAL '10 days'),
  ('00000000-0000-0000-0000-00000000020B', '00000000-0000-0000-0000-000000000107', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'edit', 'Se añadió sección de calibración.', NOW() - INTERVAL '18 days'),
  ('00000000-0000-0000-0000-00000000020C', '00000000-0000-0000-0000-000000000107', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'review', 'Checklist técnico.', NOW() - INTERVAL '6 days'),
  ('00000000-0000-0000-0000-00000000020D', '00000000-0000-0000-0000-000000000108', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Consolidación de nuevos KPIs semanales.', NOW() - INTERVAL '15 days'),
  ('00000000-0000-0000-0000-00000000020E', '00000000-0000-0000-0000-000000000108', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'review', 'Validación médica de cifras clave.', NOW() - INTERVAL '7 days'),
  ('00000000-0000-0000-0000-00000000020F', '00000000-0000-0000-0000-000000000108', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Ajuste en narrativa ejecutiva.', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- Auditoría demo (últimos 30 días)
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip, details)
VALUES
  (
    '00000000-0000-0000-0000-00000000B101',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'ORG_CREATE',
    'organization',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    NOW() - INTERVAL '6 days',
    '10.0.0.10',
    '{"code":"CLIN-001"}'::jsonb
  ),
  (
    '00000000-0000-0000-0000-00000000B102',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'INVITE_CREATE',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-001'),
    NOW() - INTERVAL '5 days',
    '10.0.0.10',
    '{"token":"INVITE-DEMO-001"}'::jsonb
  ),
  (
    '00000000-0000-0000-0000-00000000B103',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'MEMBER_ADD',
    'membership',
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '3 days',
    '10.0.0.10',
    '{"org":"FAM-001","user":"ana.ruiz@heartguard.com"}'::jsonb
  ),
  (
    '00000000-0000-0000-0000-00000000B104',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'USER_STATUS_UPDATE',
    'user',
    (SELECT id FROM users WHERE email='carlos.vega@heartguard.com'),
    NOW() - INTERVAL '1 day',
    '10.0.0.11',
    '{"email":"carlos.vega@heartguard.com","status":"blocked"}'::jsonb
  ),
  (
    '00000000-0000-0000-0000-00000000B105',
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'INVITE_CANCEL',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-003'),
    NOW() - INTERVAL '2 days',
    '10.0.0.12',
    '{"token":"INVITE-DEMO-003"}'::jsonb
  )
ON CONFLICT (id) DO NOTHING;
