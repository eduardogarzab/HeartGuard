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
INSERT INTO device_types(code, label) VALUES
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
SELECT '9d1df8a3-a474-4e4a-bf92-04d5f67c7c4b'::uuid,
       (SELECT id FROM services WHERE name='superadmin-api'),
       NOW() - INTERVAL '2 days',
       (SELECT id FROM service_statuses WHERE code='up'),
       215,
       '1.8.4'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='9d1df8a3-a474-4e4a-bf92-04d5f67c7c4b'::uuid);

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT 'd680df49-439e-4343-9cb8-babf20481505'::uuid,
       (SELECT id FROM services WHERE name='superadmin-api'),
       NOW() - INTERVAL '6 hours',
       (SELECT id FROM service_statuses WHERE code='degraded'),
       380,
       '1.8.5'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='d680df49-439e-4343-9cb8-babf20481505'::uuid);

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT 'dfc8dca4-620a-4642-80ca-7d0fc7ab7a23'::uuid,
       (SELECT id FROM services WHERE name='streaming-hub'),
       NOW() - INTERVAL '1 day',
       (SELECT id FROM service_statuses WHERE code='up'),
       180,
       '2.4.1'
WHERE NOT EXISTS (SELECT 1 FROM service_health WHERE id='dfc8dca4-620a-4642-80ca-7d0fc7ab7a23'::uuid);

-- Contenido editorial demo
INSERT INTO content_types(code, label, description) VALUES
  ('article','Artículo','Artículos y guías gestionadas desde el panel'),
  ('page','Página','Contenido informativo estático'),
  ('block','Bloque','Fragmentos reutilizables para otras páginas')
ON CONFLICT (code) DO NOTHING;

INSERT INTO content_block_types(code, label, description) VALUES
  ('richtext','Texto enriquecido','Bloque de texto principal'),
  ('callout','Llamado a la acción','Destacar notas o avisos'),
  ('checklist','Lista de verificación','Pasos secuenciales para validar procesos'),
  ('quote','Cita','Testimonios o fragmentos destacados'),
  ('media','Multimedia','Bloques para imágenes o video')
ON CONFLICT (code) DO NOTHING;

INSERT INTO content_items (id, title, summary, slug, locale, category_id, status_id, content_type_id, author_user_id, created_at, updated_at, published_at, archived_at)
VALUES
  (
    'ff7bfdf1-b20b-4e4c-8553-146acf69a474',
    'Guía rápida de monitoreo post-operatorio',
    'Checklist actualizado para pacientes en recuperación cardiovascular.',
    'guia-rapida-monitoreo-post-operatorio',
    'es',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '330 days',
    NOW() - INTERVAL '200 days',
    NOW() - INTERVAL '327 days',
    NULL
  ),
  (
    '02492215-8764-4c8d-9c3e-b20ed0306dd5',
    'Protocolos de triage cardiaco',
    'Flujo para escalar alertas críticas en menos de cinco minutos.',
    'protocolos-triage-cardiaco',
    'es',
    (SELECT id FROM content_categories WHERE code='alert_protocols'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    NOW() - INTERVAL '270 days',
    NOW() - INTERVAL '40 days',
    NOW() - INTERVAL '266 days',
    NULL
  ),
  (
    '36592f52-e8ca-4343-8e77-9394aacac8c2',
    'Preguntas frecuentes sobre telemetría domiciliaria',
    'Respuestas rápidas para cuidadores sobre dispositivos y soporte.',
    'faq-telemetria-domiciliaria',
    'es',
    (SELECT id FROM content_categories WHERE code='faq'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM content_types WHERE code='page'),
    (SELECT id FROM users WHERE email='sofia.care@heartguard.com'),
    NOW() - INTERVAL '210 days',
    NOW() - INTERVAL '25 days',
    NOW() - INTERVAL '205 days',
    NULL
  ),
  (
    'efb38308-5f7f-46df-acdb-cafaf7faf8a8',
    'Boletín educativo: manejo de hipertensión',
    'Campaña educativa para pacientes con seguimiento remoto.',
    'boletin-manejo-hipertension',
    'es',
    (SELECT id FROM content_categories WHERE code='education'),
    (SELECT id FROM content_statuses WHERE code='scheduled'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '150 days',
    NOW() - INTERVAL '7 days',
    NOW() + INTERVAL '12 days',
    NULL
  ),
  (
    '92d368b1-37b3-478d-abcd-d17f1405d653',
    'Script de seguimiento telefónico',
    'Guion para llamadas de verificación después de eventos de riesgo.',
    'script-seguimiento-telefonico',
    'es',
    (SELECT id FROM content_categories WHERE code='communications'),
    (SELECT id FROM content_statuses WHERE code='in_review'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    NOW() - INTERVAL '110 days',
    NOW() - INTERVAL '12 days',
    NULL,
    NULL
  ),
  (
    'a172e937-5644-44bd-8a74-be8c094462c5',
    'Protocolo de cierre de alertas',
    'Procedimiento histórico para cerrar alertas tras verificación manual.',
    'protocolo-cierre-alertas',
    'es',
    (SELECT id FROM content_categories WHERE code='alert_protocols'),
    (SELECT id FROM content_statuses WHERE code='archived'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    NOW() - INTERVAL '380 days',
    NOW() - INTERVAL '320 days',
    NOW() - INTERVAL '376 days',
    NOW() - INTERVAL '310 days'
  ),
  (
    'cc60ff3d-cf31-411f-985b-579a6e2a4f15',
    'Guía de configuración para nuevos dispositivos',
    'Procedimiento paso a paso para instalar sensores domiciliarios.',
    'guia-configuracion-dispositivos',
    'es',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='draft'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='sofia.care@heartguard.com'),
    NOW() - INTERVAL '45 days',
    NOW() - INTERVAL '5 days',
    NULL,
    NULL
  ),
  (
    '3b8803de-cb8e-4406-af91-9e867281348f',
    'Resumen semanal de incidencias',
    'Resumen ejecutivo con insights del monitoreo semanal.',
    'resumen-semanal-incidencias',
    'es',
    (SELECT id FROM content_categories WHERE code='communications'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM content_types WHERE code='page'),
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    NOW() - INTERVAL '20 days',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '18 days',
    NULL
  ),
  (
    '4d878fd6-f5bc-48c0-a137-31473ccd8446',
    'Checklist pre-implante para dispositivos implantables',
    'Evaluación previa a la implantación de sensores cardíacos.',
    'checklist-pre-implante-dispositivos',
    'es',
    (SELECT id FROM content_categories WHERE code='clinical_guides'),
    (SELECT id FROM content_statuses WHERE code='published'),
    (SELECT id FROM content_types WHERE code='article'),
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '420 days',
    NOW() - INTERVAL '260 days',
    NOW() - INTERVAL '415 days',
    NULL
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_versions (id, content_id, version_no, body, editor_user_id, note, change_type, created_at, published)
VALUES
  ('06f8058e-582f-475c-a94d-986a54198832', 'ff7bfdf1-b20b-4e4c-8553-146acf69a474', 1, 'Checklist completo de signos vitales y acciones posoperatorias para los primeros siete días.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '200 days', TRUE),
  ('507b6fb2-74dc-4ae5-8dc2-49501d43bb8f', '02492215-8764-4c8d-9c3e-b20ed0306dd5', 1, 'Secuencia de triage para alertas cardíacas con tiempos objetivo y responsables.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '40 days', TRUE),
  ('069ec287-d08a-4510-b539-7716e4f9ebbc', '36592f52-e8ca-4343-8e77-9394aacac8c2', 1, 'Respuestas frecuentes sobre configuración, conectividad y soporte para telemetría domiciliaria.', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '25 days', TRUE),
  ('875e798d-63b5-41b3-b3a5-bc9308fb60a5', 'efb38308-5f7f-46df-acdb-cafaf7faf8a8', 1, 'Boletín educativo con consejos para pacientes hipertensos y recordatorios de seguimiento.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '7 days', FALSE),
  ('29946d21-3cd8-40f3-868d-74a25d9ab86c', '92d368b1-37b3-478d-abcd-d17f1405d653', 1, 'Guion telefónico con preguntas clave y registro de observaciones para cuidadores.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '12 days', FALSE),
  ('06df3264-d9b0-4a8b-8ea6-2cea973378ba', 'a172e937-5644-44bd-8a74-be8c094462c5', 1, 'Procedimiento histórico documentado para cerrar alertas críticas de forma manual.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '320 days', FALSE),
  ('a712c8c6-f66d-4a45-b74b-2347e70b0a30', 'cc60ff3d-cf31-411f-985b-579a6e2a4f15', 1, 'Pasos detallados para configurar dispositivos y calibrar sensores domiciliarios.', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '5 days', FALSE),
  ('af0af772-e599-4bb4-b879-4338fd30aa82', '3b8803de-cb8e-4406-af91-9e867281348f', 1, 'Resumen ejecutivo con métricas clave y acciones recomendadas de la última semana.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '2 days', TRUE),
  ('cd43ad56-7c91-45da-a083-a5a11b889a66', '4d878fd6-f5bc-48c0-a137-31473ccd8446', 1, 'Checklist preoperatorio con validaciones clínicas y requisitos administrativos.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '260 days', TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_blocks (id, version_id, block_type_id, position, title, content, created_at)
SELECT
  v.block_id,
  v.version_id,
  (SELECT id FROM content_block_types WHERE code='richtext'),
  0,
  NULL,
  v.body,
  v.created_at
FROM (
  VALUES
    ('12dd5b08-542d-4f94-8235-58d0dd53e696'::uuid, '06f8058e-582f-475c-a94d-986a54198832'::uuid, 'Checklist completo de signos vitales y acciones posoperatorias para los primeros siete días.', NOW() - INTERVAL '200 days'),
    ('e90efa7f-c658-4aa5-94cc-e3ad77e5704c'::uuid, '507b6fb2-74dc-4ae5-8dc2-49501d43bb8f'::uuid, 'Secuencia de triage para alertas cardíacas con tiempos objetivo y responsables.', NOW() - INTERVAL '40 days'),
    ('0811abbc-bc61-4e38-8e00-5ef8a3c82fd1'::uuid, '069ec287-d08a-4510-b539-7716e4f9ebbc'::uuid, 'Respuestas frecuentes sobre configuración, conectividad y soporte para telemetría domiciliaria.', NOW() - INTERVAL '25 days'),
    ('5e47a57e-2416-47aa-a6a1-65bcb7e7eaf2'::uuid, '875e798d-63b5-41b3-b3a5-bc9308fb60a5'::uuid, 'Boletín educativo con consejos para pacientes hipertensos y recordatorios de seguimiento.', NOW() - INTERVAL '7 days'),
    ('85aa51c6-0d7a-4415-8b9c-614ee34d1bb1'::uuid, '29946d21-3cd8-40f3-868d-74a25d9ab86c'::uuid, 'Guion telefónico con preguntas clave y registro de observaciones para cuidadores.', NOW() - INTERVAL '12 days'),
    ('a3aa7067-aacb-41b9-9ac6-1c9bea7e86c4'::uuid, '06df3264-d9b0-4a8b-8ea6-2cea973378ba'::uuid, 'Procedimiento histórico documentado para cerrar alertas críticas de forma manual.', NOW() - INTERVAL '320 days'),
    ('f5e9155e-2972-4f6d-b342-f4c902de7fb4'::uuid, 'a712c8c6-f66d-4a45-b74b-2347e70b0a30'::uuid, 'Pasos detallados para configurar dispositivos y calibrar sensores domiciliarios.', NOW() - INTERVAL '5 days'),
    ('1ce5af9f-d970-4170-b4a3-9d0e7191c49c'::uuid, 'af0af772-e599-4bb4-b879-4338fd30aa82'::uuid, 'Resumen ejecutivo con métricas clave y acciones recomendadas de la última semana.', NOW() - INTERVAL '2 days'),
    ('7d856f79-25fa-4008-880d-a7e0e6753f82'::uuid, 'cd43ad56-7c91-45da-a083-a5a11b889a66'::uuid, 'Checklist preoperatorio con validaciones clínicas y requisitos administrativos.', NOW() - INTERVAL '260 days')
) AS v(block_id, version_id, body, created_at)
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_updates (id, content_id, editor_user_id, change_type, note, created_at)
VALUES
  ('d91e40a9-6de3-4df5-8597-bf4368b59a69', 'ff7bfdf1-b20b-4e4c-8553-146acf69a474', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'review', 'Se actualizó tabla de signos vitales.', NOW() - INTERVAL '320 days'),
  ('8441a3d5-bd2e-4890-ad74-b051ce60f299', 'ff7bfdf1-b20b-4e4c-8553-146acf69a474', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'edit', 'Se añadió checklist quirúrgico.', NOW() - INTERVAL '210 days'),
  ('d3e8abba-4c09-410f-97b5-a23c8eef36c5', '02492215-8764-4c8d-9c3e-b20ed0306dd5', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Se incorporaron tiempos objetivo de respuesta.', NOW() - INTERVAL '60 days'),
  ('d2d56c40-56c1-4070-99cc-f6e69c6544a0', '02492215-8764-4c8d-9c3e-b20ed0306dd5', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Validación operativa.', NOW() - INTERVAL '35 days'),
  ('0b895ef9-b616-4031-8bb3-12e63809ec3d', '36592f52-e8ca-4343-8e77-9394aacac8c2', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'edit', 'Se añadieron preguntas sobre conectividad.', NOW() - INTERVAL '120 days'),
  ('b782c4c6-edc1-4fff-a4c2-0bce2ef09e79', '36592f52-e8ca-4343-8e77-9394aacac8c2', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Clarificación sobre soporte técnico.', NOW() - INTERVAL '20 days'),
  ('029ebff0-badf-4088-8bdb-adbac437cd12', 'efb38308-5f7f-46df-acdb-cafaf7faf8a8', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'edit', 'Actualización de gráficos de presión arterial.', NOW() - INTERVAL '30 days'),
  ('4a9a0e1e-1811-4d7d-80d3-80601c26a4d0', 'efb38308-5f7f-46df-acdb-cafaf7faf8a8', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'review', 'Se programó envío a pacientes.', NOW() - INTERVAL '5 days'),
  ('44c4d1c8-8da3-4021-8587-d5d996d1a03c', '92d368b1-37b3-478d-abcd-d17f1405d653', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Ajuste de tiempos de seguimiento.', NOW() - INTERVAL '28 days'),
  ('81568cc7-5f07-4913-9781-980b45aee0c5', '92d368b1-37b3-478d-abcd-d17f1405d653', (SELECT id FROM users WHERE email='admin@heartguard.com'), 'review', 'Retroalimentación de calidad.', NOW() - INTERVAL '10 days'),
  ('29020bb4-6c65-4f26-bb0c-551b432ed123', 'cc60ff3d-cf31-411f-985b-579a6e2a4f15', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'edit', 'Se añadió sección de calibración.', NOW() - INTERVAL '18 days'),
  ('ef21ba6f-6d03-43ea-968d-96192e0bdb2b', 'cc60ff3d-cf31-411f-985b-579a6e2a4f15', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'review', 'Checklist técnico.', NOW() - INTERVAL '6 days'),
  ('53f03a0b-8327-4095-890a-7bd787188b83', '3b8803de-cb8e-4406-af91-9e867281348f', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Consolidación de nuevos KPIs semanales.', NOW() - INTERVAL '15 days'),
  ('16d28f0d-82fd-4d9e-b43e-6c7c0a41cccd', '3b8803de-cb8e-4406-af91-9e867281348f', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'review', 'Validación médica de cifras clave.', NOW() - INTERVAL '7 days'),
  ('4da49bb6-b1d4-4985-a229-e387f83ed759', '3b8803de-cb8e-4406-af91-9e867281348f', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'edit', 'Ajuste en narrativa ejecutiva.', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- Auditoría demo (últimos 30 días)
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip, details)
VALUES
  (
    '2b39b9fe-9c6e-4ac5-a6a8-106164b35835',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'ORG_CREATE',
    'organization',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    NOW() - INTERVAL '6 days',
    '10.0.0.10',
    '{"code":"CLIN-001"}'::jsonb
  ),
  (
    'b40ab4a5-7ff3-4e40-bdd2-28ba606f1a27',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'INVITE_CREATE',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-001'),
    NOW() - INTERVAL '5 days',
    '10.0.0.10',
    '{"token":"INVITE-DEMO-001"}'::jsonb
  ),
  (
    'ae3b6423-0a96-4a4a-8d96-1cc23c871e0c',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'MEMBER_ADD',
    'membership',
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '3 days',
    '10.0.0.10',
    '{"org":"FAM-001","user":"ana.ruiz@heartguard.com"}'::jsonb
  ),
  (
    '6d752c42-d99e-4c90-a4ee-b863d961eb25',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'USER_STATUS_UPDATE',
    'user',
    (SELECT id FROM users WHERE email='carlos.vega@heartguard.com'),
    NOW() - INTERVAL '1 day',
    '10.0.0.11',
    '{"email":"carlos.vega@heartguard.com","status":"blocked"}'::jsonb
  ),
  (
    '178f6b31-89a3-4f75-8828-e34bc5594046',
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'INVITE_CANCEL',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-003'),
    NOW() - INTERVAL '2 days',
    '10.0.0.12',
    '{"token":"INVITE-DEMO-003"}'::jsonb
  )
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Datos demo clínicos y operativos
-- =========================================================

INSERT INTO patients (id, org_id, person_name, birthdate, sex_id, risk_level, created_at)
VALUES
  (
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'María Delgado',
    '1978-03-22',
    (SELECT id FROM sexes WHERE code='F'),
    'high',
    NOW() - INTERVAL '120 days'
  ),
  (
    'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'José Hernández',
    '1965-11-04',
    (SELECT id FROM sexes WHERE code='M'),
    'medium',
    NOW() - INTERVAL '180 days'
  ),
  (
    'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'Valeria Ortiz',
    '1992-07-15',
    (SELECT id FROM sexes WHERE code='F'),
    'low',
    NOW() - INTERVAL '45 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO care_teams (id, org_id, name, created_at)
VALUES
  (
    '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'Equipo Cardiología Familiar',
    NOW() - INTERVAL '140 days'
  ),
  (
    'a9c83e54-30e5-4487-abb5-1f97a10cca17'::uuid,
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'Unidad Telemetría Clínica',
    NOW() - INTERVAL '200 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid, u.id, 'Cardióloga tratante', NOW() - INTERVAL '120 days'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid, u.id, 'Analista de monitoreo', NOW() - INTERVAL '100 days'
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT 'a9c83e54-30e5-4487-abb5-1f97a10cca17'::uuid, u.id, 'Supervisor clínico', NOW() - INTERVAL '150 days'
FROM users u
WHERE u.email='admin@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO patient_care_team (patient_id, care_team_id)
VALUES
  ('8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid, '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid),
  ('fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid, 'a9c83e54-30e5-4487-abb5-1f97a10cca17'::uuid),
  ('ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid, '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid)
ON CONFLICT DO NOTHING;

INSERT INTO caregiver_patient (patient_id, user_id, rel_type_id, is_primary, started_at, note)
SELECT
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  u.id,
  (SELECT id FROM caregiver_relationship_types WHERE code='spouse'),
  TRUE,
  NOW() - INTERVAL '45 days',
  'Contacto principal domiciliario'
FROM users u
WHERE u.email='sofia.care@heartguard.com'
ON CONFLICT (patient_id, user_id) DO NOTHING;

INSERT INTO caregiver_patient (patient_id, user_id, rel_type_id, is_primary, started_at, note)
SELECT
  'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
  u.id,
  (SELECT id FROM caregiver_relationship_types WHERE code='friend'),
  FALSE,
  NOW() - INTERVAL '20 days',
  'Contacto auxiliar para turnos nocturnos'
FROM users u
WHERE u.email='carlos.vega@heartguard.com'
ON CONFLICT (patient_id, user_id) DO NOTHING;

INSERT INTO patient_locations (id, patient_id, ts, geom, source, accuracy_m)
VALUES
  (
    'd3b657d5-d23d-4461-a096-0af90b981c9d'::uuid,
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    NOW() - INTERVAL '10 hours',
    ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326),
    'manual',
    35.50
  ),
  (
    'c9e70ea3-2cdb-4449-b62d-53d2327286da'::uuid,
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    NOW() - INTERVAL '2 hours',
    ST_SetSRID(ST_MakePoint(-99.1400, 19.4305), 4326),
    'caregiver',
    18.00
  ),
  (
    'b00ce392-4324-4532-b663-541086b06030'::uuid,
    'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
    NOW() - INTERVAL '1 day',
    ST_SetSRID(ST_MakePoint(-98.2063, 19.0413), 4326),
    'sync',
    12.40
  ),
  (
    '732741d8-7679-4884-b208-24d03e9d3fcf'::uuid,
    'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
    NOW() - INTERVAL '3 days',
    ST_SetSRID(ST_MakePoint(-100.3161, 25.6866), 4326),
    'manual',
    42.00
  )
ON CONFLICT (patient_id, ts) DO NOTHING;

INSERT INTO user_locations (id, user_id, ts, geom, source, accuracy_m)
SELECT
  '135c06c7-e1d0-4520-b8a3-cafd7c02821a'::uuid,
  u.id,
  NOW() - INTERVAL '3 hours',
  ST_SetSRID(ST_MakePoint(-99.1100, 19.4400), 4326),
  'mobile-app',
  15.20
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT (user_id, ts) DO NOTHING;

INSERT INTO user_locations (id, user_id, ts, geom, source, accuracy_m)
SELECT
  '8a5c5b38-4f54-44f4-a374-8c513757bc0f'::uuid,
  u.id,
  NOW() - INTERVAL '5 hours',
  ST_SetSRID(ST_MakePoint(-99.1500, 19.4200), 4326),
  'caregiver-app',
  22.00
FROM users u
WHERE u.email='sofia.care@heartguard.com'
ON CONFLICT (user_id, ts) DO NOTHING;

INSERT INTO user_locations (id, user_id, ts, geom, source, accuracy_m)
SELECT
  'b198d173-864c-4b47-a5c8-f50d36e79f76'::uuid,
  u.id,
  NOW() - INTERVAL '1 day',
  ST_SetSRID(ST_MakePoint(-99.2000, 19.4000), 4326),
  'vpn-monitor',
  9.80
FROM users u
WHERE u.email='admin@heartguard.com'
ON CONFLICT (user_id, ts) DO NOTHING;

INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  '6212c577-1103-46b0-a314-9800a3995c61'::uuid,
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  et.id,
  NOW() - INTERVAL '26 hours',
  NOW() - INTERVAL '25 hours 30 minutes',
  (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  'manual-review',
  'Arritmia confirmada en monitoreo nocturno'
FROM event_types et
WHERE et.code='AFIB'
ON CONFLICT (id) DO NOTHING;

INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  '5374534c-783a-49c8-a976-0913eec27c93'::uuid,
  'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
  et.id,
  NOW() - INTERVAL '32 hours',
  NOW() - INTERVAL '31 hours 15 minutes',
  (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
  'device-sync',
  'Evento de desaturación confirmado con oxímetro domiciliario'
FROM event_types et
WHERE et.code='DESAT'
ON CONFLICT (id) DO NOTHING;

INSERT INTO devices (id, org_id, serial, brand, model, device_type_id, owner_patient_id, registered_at, active)
VALUES
  (
    '1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'HG-ECG-001',
    'Cardia',
    'Wave Pro',
    (SELECT id FROM device_types WHERE code='ECG_1LEAD'),
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    NOW() - INTERVAL '200 days',
    TRUE
  ),
  (
    'e085ff18-d8bd-46f6-b34c-26bb0b797a14'::uuid,
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'HG-PUL-201',
    'OxyCare',
    'PulseSat Mini',
    (SELECT id FROM device_types WHERE code='PULSE_OX'),
    'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
    NOW() - INTERVAL '90 days',
    TRUE
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO signal_streams (id, patient_id, device_id, signal_type_id, sample_rate_hz, started_at, ended_at)
VALUES
  (
    'f171d21c-a837-4d03-8233-9d80a20911ca'::uuid,
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    '1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d'::uuid,
    (SELECT id FROM signal_types WHERE code='ECG'),
    256,
    NOW() - INTERVAL '7 days',
    NULL
  ),
  (
    '7470ea38-4d6d-4519-9bb8-766d2dee575a'::uuid,
    'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
    'e085ff18-d8bd-46f6-b34c-26bb0b797a14'::uuid,
    (SELECT id FROM signal_types WHERE code='SpO2'),
    1,
    NOW() - INTERVAL '3 days',
    NOW() - INTERVAL '1 day'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO timeseries_binding (id, stream_id, influx_org, influx_bucket, measurement, retention_hint, created_at)
VALUES
  (
    '86eee85e-de79-4414-9986-15d2930271aa',
    'f171d21c-a837-4d03-8233-9d80a20911ca',
    'heartguard-lab',
    'telemetria',
    'ecg_waveform',
    '30d',
    NOW() - INTERVAL '7 days'
  ),
  (
    '333d08ad-b521-4d3b-9259-9013ff6aa360',
    '7470ea38-4d6d-4519-9bb8-766d2dee575a',
    'heartguard-lab',
    'telemetria',
    'spo2_series',
    '14d',
    NOW() - INTERVAL '3 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO timeseries_binding_tag (id, binding_id, tag_key, tag_value)
VALUES
  ('153f0fe6-7c02-4af3-8005-fced200b2257'::uuid, '86eee85e-de79-4414-9986-15d2930271aa'::uuid, 'patient_uuid', '8c9436b4-f085-405f-a3d2-87cb1d1cf097'),
  ('36c1321b-6058-49a2-ac41-48cf600c584a'::uuid, '86eee85e-de79-4414-9986-15d2930271aa'::uuid, 'org_code', 'FAM-001'),
  ('b9c0aea5-c49c-4f5d-a1ad-8383479e8257'::uuid, '333d08ad-b521-4d3b-9259-9013ff6aa360'::uuid, 'patient_uuid', 'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21')
ON CONFLICT (binding_id, tag_key) DO NOTHING;

INSERT INTO models (id, name, version, task, training_data_ref, hyperparams, created_at)
VALUES
  (
    '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
    'CardioNet Arrhythmia',
    '1.3.0',
    'arrhythmia_detection',
    's3://heartguard-models/cardionet/v1.3.0',
    '{"threshold":0.80,"window_s":120}'::jsonb,
    NOW() - INTERVAL '120 days'
  ),
  (
    'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid,
    'Oxymap Guardian',
    '0.9.2',
    'desaturation_detection',
    's3://heartguard-models/oxymap/v0.9.2',
    '{"min_spo2":0.9}'::jsonb,
    NOW() - INTERVAL '80 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT
  '4f5f27ff-b251-4e72-82cc-4ae1b8ee1dab'::uuid,
  '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
  'f171d21c-a837-4d03-8233-9d80a20911ca'::uuid,
  NOW() - INTERVAL '2 hours',
  NOW() - INTERVAL '1 hour 55 minutes',
  et.id,
  0.873,
  0.800,
  '{"lead_quality":"good"}'::jsonb,
  NOW() - INTERVAL '1 hour 54 minutes',
  'streams/000000000740/chunk-001'
FROM event_types et
WHERE et.code='AFIB'
ON CONFLICT (id) DO NOTHING;

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT
  '7e4b8ccd-57c8-460f-bfb9-ff96cff54b0c'::uuid,
  'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid,
  '7470ea38-4d6d-4519-9bb8-766d2dee575a'::uuid,
  NOW() - INTERVAL '32 hours',
  NOW() - INTERVAL '31 hours 55 minutes',
  et.id,
  0.642,
  0.600,
  '{"min_spo2":0.88}'::jsonb,
  NOW() - INTERVAL '31 hours 50 minutes',
  'streams/000000000741/chunk-014'
FROM event_types et
WHERE et.code='DESAT'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
SELECT
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  at.id,
  '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
  '4f5f27ff-b251-4e72-82cc-4ae1b8ee1dab'::uuid,
  (SELECT id FROM alert_levels WHERE code='high'),
  (SELECT id FROM alert_status WHERE code='ack'),
  NOW() - INTERVAL '1 hour 52 minutes',
  'Posible fibrilación detectada por CardioNet',
  ST_SetSRID(ST_MakePoint(-99.1350, 19.4320), 4326)
FROM alert_types at
WHERE at.code='ARRHYTHMIA'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
SELECT
  'e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0'::uuid,
  'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
  at.id,
  'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid,
  '7e4b8ccd-57c8-460f-bfb9-ff96cff54b0c'::uuid,
  (SELECT id FROM alert_levels WHERE code='medium'),
  (SELECT id FROM alert_status WHERE code='resolved'),
  NOW() - INTERVAL '31 hours 45 minutes',
  'Episodio de desaturación nocturna',
  ST_SetSRID(ST_MakePoint(-98.2000, 19.0400), 4326)
FROM alert_types at
WHERE at.code='DESAT'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_assignment (alert_id, assignee_user_id, assigned_by_user_id, assigned_at)
SELECT
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  assignee.id,
  assigner.id,
  NOW() - INTERVAL '90 minutes'
FROM users assignee
CROSS JOIN users assigner
WHERE assignee.email='ana.ruiz@heartguard.com'
  AND assigner.email='admin@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO alert_assignment (alert_id, assignee_user_id, assigned_by_user_id, assigned_at)
SELECT
  'e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0'::uuid,
  assignee.id,
  assigner.id,
  NOW() - INTERVAL '31 hours'
FROM users assignee
CROSS JOIN users assigner
WHERE assignee.email='martin.ops@heartguard.com'
  AND assigner.email='admin@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO alert_ack (id, alert_id, ack_by_user_id, ack_at, note)
SELECT
  '89457d54-bbb6-4bf8-befc-5f49bcbe89e5'::uuid,
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  u.id,
  NOW() - INTERVAL '80 minutes',
  'Revisando telemetría en tiempo real'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_ack (id, alert_id, ack_by_user_id, ack_at, note)
SELECT
  '97435a3c-e87a-4d75-9c21-8c93e290df01'::uuid,
  'e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0'::uuid,
  u.id,
  NOW() - INTERVAL '30 hours',
  'Confirmado con paciente, escalado a guardia médica'
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
SELECT
  '36d2632b-854c-449d-a7f9-a315b53c33fb'::uuid,
  'e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0'::uuid,
  u.id,
  NOW() - INTERVAL '30 hours 30 minutes',
  'Stabilized',
  'Paciente respondió favorablemente a intervención remota'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id, response_payload)
SELECT
  'c7e07f0a-eafb-49cb-b203-603f718bf251'::uuid,
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  ch.id,
  'HG-APP-ANA',
  NOW() - INTERVAL '95 minutes',
  (SELECT id FROM delivery_statuses WHERE code='DELIVERED'),
  NULL
FROM alert_channels ch
WHERE ch.code='PUSH'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id, response_payload)
SELECT
  '01acc92e-fbb2-4a82-ad4d-fb7e56f4659e'::uuid,
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  ch.id,
  'ana.ruiz@heartguard.com',
  NOW() - INTERVAL '94 minutes',
  (SELECT id FROM delivery_statuses WHERE code='DELIVERED'),
  NULL
FROM alert_channels ch
WHERE ch.code='EMAIL'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id, response_payload)
SELECT
  '7af2936b-1898-414a-9800-14a6a1febaf0'::uuid,
  'e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0'::uuid,
  ch.id,
  '+52 555 123 4567',
  NOW() - INTERVAL '32 hours',
  (SELECT id FROM delivery_statuses WHERE code='SENT'),
  NULL
FROM alert_channels ch
WHERE ch.code='SMS'
ON CONFLICT (id) DO NOTHING;

INSERT INTO push_devices (id, user_id, platform_id, push_token, last_seen_at, active)
SELECT
  'd27a6e1b-8def-423e-8d49-e59113d00ac5'::uuid,
  u.id,
  p.id,
  'ANA-DEVICE-TOKEN',
  NOW() - INTERVAL '1 hour',
  TRUE
FROM users u
CROSS JOIN platforms p
WHERE u.email='ana.ruiz@heartguard.com'
  AND p.code='ios'
ON CONFLICT (user_id, platform_id, push_token) DO NOTHING;

INSERT INTO push_devices (id, user_id, platform_id, push_token, last_seen_at, active)
SELECT
  'b8ffa975-0c3f-426e-8fa8-c18f259b939f'::uuid,
  u.id,
  p.id,
  'MARTIN-NEO-01',
  NOW() - INTERVAL '12 hours',
  TRUE
FROM users u
CROSS JOIN platforms p
WHERE u.email='martin.ops@heartguard.com'
  AND p.code='android'
ON CONFLICT (user_id, platform_id, push_token) DO NOTHING;

INSERT INTO batch_exports (id, purpose, target_ref, requested_by, requested_at, completed_at, batch_export_status_id, details)
VALUES
  (
    '791771c7-d51d-4d05-9e56-2ebfd2ff343a'::uuid,
    'alerts_csv',
    's3://demo-exports/alerts-2025-10-10.csv',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '23 hours',
    (SELECT id FROM batch_export_statuses WHERE code='done'),
    '{"row_count":52,"filters":{"status":["ack","resolved"]}}'::jsonb
  ),
  (
    '9f063660-1e77-4dd3-aacc-36aeddab5d06'::uuid,
    'patients_snapshot',
    's3://demo-exports/patients-queue.csv',
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '6 hours',
    NULL,
    (SELECT id FROM batch_export_statuses WHERE code='running'),
    '{"org":"FAM-001"}'::jsonb
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO api_keys (id, owner_user_id, key_hash, label, created_at, expires_at, revoked_at, scopes)
VALUES
  (
    'a79994c5-66a9-451a-b414-c864306416e3'::uuid,
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    encode(digest('HGDEMO-KEY-1', 'sha256'), 'hex'),
    'Demo - Integración CLI',
    NOW() - INTERVAL '15 days',
    NOW() + INTERVAL '15 days',
    NULL,
    ARRAY['alerts.read','patients.read']
  ),
  (
    '7c2746e8-848c-4a21-aa98-d58d84374e95'::uuid,
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    encode(digest('HGDEMO-KEY-2', 'sha256'), 'hex'),
    'Integración Operaciones (revocada)',
    NOW() - INTERVAL '120 days',
    NOW() - INTERVAL '30 days',
    NOW() - INTERVAL '10 days',
    ARRAY['alerts.manage']
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO api_key_permission (api_key_id, permission_id)
SELECT 'a79994c5-66a9-451a-b414-c864306416e3'::uuid, p.id
FROM permissions p
WHERE p.code IN ('alerts.read','patients.read')
ON CONFLICT DO NOTHING;

INSERT INTO api_key_permission (api_key_id, permission_id)
SELECT '7c2746e8-848c-4a21-aa98-d58d84374e95'::uuid, p.id
FROM permissions p
WHERE p.code IN ('alerts.manage')
ON CONFLICT DO NOTHING;
