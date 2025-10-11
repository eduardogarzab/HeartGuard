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
    '00000000-0000-0000-0000-000000000101',
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
    '00000000-0000-0000-0000-000000000102',
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
    '00000000-0000-0000-0000-000000000103',
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
    '00000000-0000-0000-0000-000000000104',
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
    '00000000-0000-0000-0000-000000000105',
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
    '00000000-0000-0000-0000-000000000106',
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
    '00000000-0000-0000-0000-000000000107',
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
    '00000000-0000-0000-0000-000000000108',
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
    '00000000-0000-0000-0000-000000000109',
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
  ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000101', 1, 'Checklist completo de signos vitales y acciones posoperatorias para los primeros siete días.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '200 days', TRUE),
  ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000102', 1, 'Secuencia de triage para alertas cardíacas con tiempos objetivo y responsables.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '40 days', TRUE),
  ('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000103', 1, 'Respuestas frecuentes sobre configuración, conectividad y soporte para telemetría domiciliaria.', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '25 days', TRUE),
  ('00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000104', 1, 'Boletín educativo con consejos para pacientes hipertensos y recordatorios de seguimiento.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '7 days', FALSE),
  ('00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000105', 1, 'Guion telefónico con preguntas clave y registro de observaciones para cuidadores.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '12 days', FALSE),
  ('00000000-0000-0000-0000-000000000306', '00000000-0000-0000-0000-000000000106', 1, 'Procedimiento histórico documentado para cerrar alertas críticas de forma manual.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '320 days', FALSE),
  ('00000000-0000-0000-0000-000000000307', '00000000-0000-0000-0000-000000000107', 1, 'Pasos detallados para configurar dispositivos y calibrar sensores domiciliarios.', (SELECT id FROM users WHERE email='sofia.care@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '5 days', FALSE),
  ('00000000-0000-0000-0000-000000000308', '00000000-0000-0000-0000-000000000108', 1, 'Resumen ejecutivo con métricas clave y acciones recomendadas de la última semana.', (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '2 days', TRUE),
  ('00000000-0000-0000-0000-000000000309', '00000000-0000-0000-0000-000000000109', 1, 'Checklist preoperatorio con validaciones clínicas y requisitos administrativos.', (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'Versión inicial', 'seed', NOW() - INTERVAL '260 days', TRUE)
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
    ('00000000-0000-0000-0000-000000000401'::uuid, '00000000-0000-0000-0000-000000000301'::uuid, 'Checklist completo de signos vitales y acciones posoperatorias para los primeros siete días.', NOW() - INTERVAL '200 days'),
    ('00000000-0000-0000-0000-000000000402'::uuid, '00000000-0000-0000-0000-000000000302'::uuid, 'Secuencia de triage para alertas cardíacas con tiempos objetivo y responsables.', NOW() - INTERVAL '40 days'),
    ('00000000-0000-0000-0000-000000000403'::uuid, '00000000-0000-0000-0000-000000000303'::uuid, 'Respuestas frecuentes sobre configuración, conectividad y soporte para telemetría domiciliaria.', NOW() - INTERVAL '25 days'),
    ('00000000-0000-0000-0000-000000000404'::uuid, '00000000-0000-0000-0000-000000000304'::uuid, 'Boletín educativo con consejos para pacientes hipertensos y recordatorios de seguimiento.', NOW() - INTERVAL '7 days'),
    ('00000000-0000-0000-0000-000000000405'::uuid, '00000000-0000-0000-0000-000000000305'::uuid, 'Guion telefónico con preguntas clave y registro de observaciones para cuidadores.', NOW() - INTERVAL '12 days'),
    ('00000000-0000-0000-0000-000000000406'::uuid, '00000000-0000-0000-0000-000000000306'::uuid, 'Procedimiento histórico documentado para cerrar alertas críticas de forma manual.', NOW() - INTERVAL '320 days'),
    ('00000000-0000-0000-0000-000000000407'::uuid, '00000000-0000-0000-0000-000000000307'::uuid, 'Pasos detallados para configurar dispositivos y calibrar sensores domiciliarios.', NOW() - INTERVAL '5 days'),
    ('00000000-0000-0000-0000-000000000408'::uuid, '00000000-0000-0000-0000-000000000308'::uuid, 'Resumen ejecutivo con métricas clave y acciones recomendadas de la última semana.', NOW() - INTERVAL '2 days'),
    ('00000000-0000-0000-0000-000000000409'::uuid, '00000000-0000-0000-0000-000000000309'::uuid, 'Checklist preoperatorio con validaciones clínicas y requisitos administrativos.', NOW() - INTERVAL '260 days')
) AS v(block_id, version_id, body, created_at)
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
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip)
VALUES
  (
    '00000000-0000-0000-0000-00000000B101',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'ORG_CREATE',
    'organization',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    NOW() - INTERVAL '6 days',
    '10.0.0.10'
  ),
  (
    '00000000-0000-0000-0000-00000000B102',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'INVITE_CREATE',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-001'),
    NOW() - INTERVAL '5 days',
    '10.0.0.10'
  ),
  (
    '00000000-0000-0000-0000-00000000B103',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'MEMBER_ADD',
    'membership',
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '3 days',
    '10.0.0.10'
  ),
  (
    '00000000-0000-0000-0000-00000000B104',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    'USER_STATUS_UPDATE',
    'user',
    (SELECT id FROM users WHERE email='carlos.vega@heartguard.com'),
    NOW() - INTERVAL '1 day',
    '10.0.0.11'
  ),
  (
    '00000000-0000-0000-0000-00000000B105',
    (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
    'INVITE_CANCEL',
    'org_invitation',
    (SELECT id FROM org_invitations WHERE token='INVITE-DEMO-003'),
    NOW() - INTERVAL '2 days',
    '10.0.0.12'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO audit_log_details (audit_log_id, detail_key, value_json)
VALUES
  ('00000000-0000-0000-0000-00000000B101', 'code', '"CLIN-001"'),
  ('00000000-0000-0000-0000-00000000B102', 'token', '"INVITE-DEMO-001"'),
  ('00000000-0000-0000-0000-00000000B103', 'org', '"FAM-001"'),
  ('00000000-0000-0000-0000-00000000B103', 'user', '"ana.ruiz@heartguard.com"'),
  ('00000000-0000-0000-0000-00000000B104', 'email', '"carlos.vega@heartguard.com"'),
  ('00000000-0000-0000-0000-00000000B104', 'status', '"blocked"'),
  ('00000000-0000-0000-0000-00000000B105', 'token', '"INVITE-DEMO-003"')
ON CONFLICT (audit_log_id, detail_key) DO NOTHING;

-- =========================================================
-- Datos demo clínicos y operativos
-- =========================================================

INSERT INTO patients (id, org_id, person_name, birthdate, sex_id, risk_level, created_at)
VALUES
  (
    '00000000-0000-0000-0000-000000000501',
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'María Delgado',
    '1978-03-22',
    (SELECT id FROM sexes WHERE code='F'),
    'high',
    NOW() - INTERVAL '120 days'
  ),
  (
    '00000000-0000-0000-0000-000000000502',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'José Hernández',
    '1965-11-04',
    (SELECT id FROM sexes WHERE code='M'),
    'medium',
    NOW() - INTERVAL '180 days'
  ),
  (
    '00000000-0000-0000-0000-000000000503',
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
    '00000000-0000-0000-0000-000000000601',
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'Equipo Cardiología Familiar',
    NOW() - INTERVAL '140 days'
  ),
  (
    '00000000-0000-0000-0000-000000000602',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'Unidad Telemetría Clínica',
    NOW() - INTERVAL '200 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT '00000000-0000-0000-0000-000000000601'::uuid, u.id, 'Cardióloga tratante', NOW() - INTERVAL '120 days'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT '00000000-0000-0000-0000-000000000601'::uuid, u.id, 'Analista de monitoreo', NOW() - INTERVAL '100 days'
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_in_team, joined_at)
SELECT '00000000-0000-0000-0000-000000000602'::uuid, u.id, 'Supervisor clínico', NOW() - INTERVAL '150 days'
FROM users u
WHERE u.email='admin@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO patient_care_team (patient_id, care_team_id)
VALUES
  ('00000000-0000-0000-0000-000000000501'::uuid, '00000000-0000-0000-0000-000000000601'::uuid),
  ('00000000-0000-0000-0000-000000000502'::uuid, '00000000-0000-0000-0000-000000000602'::uuid),
  ('00000000-0000-0000-0000-000000000503'::uuid, '00000000-0000-0000-0000-000000000601'::uuid)
ON CONFLICT DO NOTHING;

INSERT INTO caregiver_patient (patient_id, user_id, rel_type_id, is_primary, started_at, note)
SELECT
  '00000000-0000-0000-0000-000000000501'::uuid,
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
  '00000000-0000-0000-0000-000000000503'::uuid,
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
    '00000000-0000-0000-0000-000000000701',
    '00000000-0000-0000-0000-000000000501',
    NOW() - INTERVAL '10 hours',
    ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326),
    'manual',
    35.50
  ),
  (
    '00000000-0000-0000-0000-000000000702',
    '00000000-0000-0000-0000-000000000501',
    NOW() - INTERVAL '2 hours',
    ST_SetSRID(ST_MakePoint(-99.1400, 19.4305), 4326),
    'caregiver',
    18.00
  ),
  (
    '00000000-0000-0000-0000-000000000703',
    '00000000-0000-0000-0000-000000000502',
    NOW() - INTERVAL '1 day',
    ST_SetSRID(ST_MakePoint(-98.2063, 19.0413), 4326),
    'sync',
    12.40
  ),
  (
    '00000000-0000-0000-0000-000000000704',
    '00000000-0000-0000-0000-000000000503',
    NOW() - INTERVAL '3 days',
    ST_SetSRID(ST_MakePoint(-100.3161, 25.6866), 4326),
    'manual',
    42.00
  )
ON CONFLICT (patient_id, ts) DO NOTHING;

INSERT INTO user_locations (id, user_id, ts, geom, source, accuracy_m)
SELECT
  '00000000-0000-0000-0000-000000000710',
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
  '00000000-0000-0000-0000-000000000711',
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
  '00000000-0000-0000-0000-000000000712',
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
  '00000000-0000-0000-0000-000000000720',
  '00000000-0000-0000-0000-000000000501'::uuid,
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
  '00000000-0000-0000-0000-000000000721',
  '00000000-0000-0000-0000-000000000502'::uuid,
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
    '00000000-0000-0000-0000-000000000730',
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'HG-ECG-001',
    'Cardia',
    'Wave Pro',
    (SELECT id FROM device_types WHERE code='ECG_1LEAD'),
    '00000000-0000-0000-0000-000000000501',
    NOW() - INTERVAL '200 days',
    TRUE
  ),
  (
    '00000000-0000-0000-0000-000000000731',
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'HG-PUL-201',
    'OxyCare',
    'PulseSat Mini',
    (SELECT id FROM device_types WHERE code='PULSE_OX'),
    '00000000-0000-0000-0000-000000000502',
    NOW() - INTERVAL '90 days',
    TRUE
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO signal_streams (id, patient_id, device_id, signal_type_id, sample_rate_hz, started_at, ended_at)
VALUES
  (
    '00000000-0000-0000-0000-000000000740',
    '00000000-0000-0000-0000-000000000501',
    '00000000-0000-0000-0000-000000000730',
    (SELECT id FROM signal_types WHERE code='ECG'),
    256,
    NOW() - INTERVAL '7 days',
    NULL
  ),
  (
    '00000000-0000-0000-0000-000000000741',
    '00000000-0000-0000-0000-000000000502',
    '00000000-0000-0000-0000-000000000731',
    (SELECT id FROM signal_types WHERE code='SpO2'),
    1,
    NOW() - INTERVAL '3 days',
    NOW() - INTERVAL '1 day'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO timeseries_binding (id, stream_id, influx_org, influx_bucket, measurement, retention_hint, created_at)
VALUES
  (
    '00000000-0000-0000-0000-000000000750',
    '00000000-0000-0000-0000-000000000740',
    'heartguard-lab',
    'telemetria',
    'ecg_waveform',
    '30d',
    NOW() - INTERVAL '7 days'
  ),
  (
    '00000000-0000-0000-0000-000000000751',
    '00000000-0000-0000-0000-000000000741',
    'heartguard-lab',
    'telemetria',
    'spo2_series',
    '14d',
    NOW() - INTERVAL '3 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO timeseries_binding_tag (id, binding_id, tag_key, tag_value)
VALUES
  ('00000000-0000-0000-0000-000000000760', '00000000-0000-0000-0000-000000000750', 'patient_uuid', '00000000-0000-0000-0000-000000000501'),
  ('00000000-0000-0000-0000-000000000761', '00000000-0000-0000-0000-000000000750', 'org_code', 'FAM-001'),
  ('00000000-0000-0000-0000-000000000762', '00000000-0000-0000-0000-000000000751', 'patient_uuid', '00000000-0000-0000-0000-000000000502')
ON CONFLICT (binding_id, tag_key) DO NOTHING;

INSERT INTO models (id, name, version, task, training_data_ref, created_at)
VALUES
  (
    '00000000-0000-0000-0000-000000000770',
    'CardioNet Arrhythmia',
    '1.3.0',
    'arrhythmia_detection',
    's3://heartguard-models/cardionet/v1.3.0',
    NOW() - INTERVAL '120 days'
  ),
  (
    '00000000-0000-0000-0000-000000000771',
    'Oxymap Guardian',
    '0.9.2',
    'desaturation_detection',
    's3://heartguard-models/oxymap/v0.9.2',
    NOW() - INTERVAL '80 days'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO model_hyperparameters (model_id, param_key, value_json)
VALUES
  ('00000000-0000-0000-0000-000000000770', 'threshold', '0.80'),
  ('00000000-0000-0000-0000-000000000770', 'window_s', '120'),
  ('00000000-0000-0000-0000-000000000771', 'min_spo2', '0.9')
ON CONFLICT (model_id, param_key) DO NOTHING;

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, created_at, series_ref)
SELECT
  '00000000-0000-0000-0000-000000000780',
  '00000000-0000-0000-0000-000000000770',
  '00000000-0000-0000-0000-000000000740',
  NOW() - INTERVAL '2 hours',
  NOW() - INTERVAL '1 hour 55 minutes',
  et.id,
  0.873,
  0.800,
  NOW() - INTERVAL '1 hour 54 minutes',
  'streams/000000000740/chunk-001'
FROM event_types et
WHERE et.code='AFIB'
ON CONFLICT (id) DO NOTHING;

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, created_at, series_ref)
SELECT
  '00000000-0000-0000-0000-000000000781',
  '00000000-0000-0000-0000-000000000771',
  '00000000-0000-0000-0000-000000000741',
  NOW() - INTERVAL '32 hours',
  NOW() - INTERVAL '31 hours 55 minutes',
  et.id,
  0.642,
  0.600,
  NOW() - INTERVAL '31 hours 50 minutes',
  'streams/000000000741/chunk-014'
FROM event_types et
WHERE et.code='DESAT'
ON CONFLICT (id) DO NOTHING;

INSERT INTO inference_metadata (inference_id, entry_key, value_json)
VALUES
  ('00000000-0000-0000-0000-000000000780', 'lead_quality', '"good"'),
  ('00000000-0000-0000-0000-000000000781', 'min_spo2', '0.88')
ON CONFLICT (inference_id, entry_key) DO NOTHING;

INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
SELECT
  '00000000-0000-0000-0000-000000000790',
  '00000000-0000-0000-0000-000000000501'::uuid,
  at.id,
  '00000000-0000-0000-0000-000000000770',
  '00000000-0000-0000-0000-000000000780',
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
  '00000000-0000-0000-0000-000000000791',
  '00000000-0000-0000-0000-000000000502'::uuid,
  at.id,
  '00000000-0000-0000-0000-000000000771',
  '00000000-0000-0000-0000-000000000781',
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
  '00000000-0000-0000-0000-000000000790'::uuid,
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
  '00000000-0000-0000-0000-000000000791'::uuid,
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
  '00000000-0000-0000-0000-0000000007A0',
  '00000000-0000-0000-0000-000000000790'::uuid,
  u.id,
  NOW() - INTERVAL '80 minutes',
  'Revisando telemetría en tiempo real'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_ack (id, alert_id, ack_by_user_id, ack_at, note)
SELECT
  '00000000-0000-0000-0000-0000000007A1',
  '00000000-0000-0000-0000-000000000791'::uuid,
  u.id,
  NOW() - INTERVAL '30 hours',
  'Confirmado con paciente, escalado a guardia médica'
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
SELECT
  '00000000-0000-0000-0000-0000000007B0',
  '00000000-0000-0000-0000-000000000791'::uuid,
  u.id,
  NOW() - INTERVAL '30 hours 30 minutes',
  'Stabilized',
  'Paciente respondió favorablemente a intervención remota'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id)
SELECT
  '00000000-0000-0000-0000-0000000007C0',
  '00000000-0000-0000-0000-000000000790'::uuid,
  ch.id,
  'HG-APP-ANA',
  NOW() - INTERVAL '95 minutes',
  (SELECT id FROM delivery_statuses WHERE code='DELIVERED')
FROM alert_channels ch
WHERE ch.code='PUSH'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id)
SELECT
  '00000000-0000-0000-0000-0000000007C1',
  '00000000-0000-0000-0000-000000000790'::uuid,
  ch.id,
  'ana.ruiz@heartguard.com',
  NOW() - INTERVAL '94 minutes',
  (SELECT id FROM delivery_statuses WHERE code='DELIVERED')
FROM alert_channels ch
WHERE ch.code='EMAIL'
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_delivery (id, alert_id, channel_id, target, sent_at, delivery_status_id)
SELECT
  '00000000-0000-0000-0000-0000000007C2',
  '00000000-0000-0000-0000-000000000791'::uuid,
  ch.id,
  '+52 555 123 4567',
  NOW() - INTERVAL '32 hours',
  (SELECT id FROM delivery_statuses WHERE code='SENT')
FROM alert_channels ch
WHERE ch.code='SMS'
ON CONFLICT (id) DO NOTHING;

INSERT INTO push_devices (id, user_id, platform_id, push_token, last_seen_at, active)
SELECT
  '00000000-0000-0000-0000-0000000007D0',
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
  '00000000-0000-0000-0000-0000000007D1',
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

INSERT INTO batch_exports (id, purpose, target_ref, requested_by, requested_at, completed_at, batch_export_status_id)
VALUES
  (
    '00000000-0000-0000-0000-0000000007E0',
    'alerts_csv',
    's3://demo-exports/alerts-2025-10-10.csv',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '23 hours',
    (SELECT id FROM batch_export_statuses WHERE code='done')
  ),
  (
    '00000000-0000-0000-0000-0000000007E1',
    'patients_snapshot',
    's3://demo-exports/patients-queue.csv',
    (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
    NOW() - INTERVAL '6 hours',
    NULL,
    (SELECT id FROM batch_export_statuses WHERE code='running')
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO batch_export_details (export_id, detail_key, value_json)
VALUES
  ('00000000-0000-0000-0000-0000000007E0', 'row_count', '52'),
  ('00000000-0000-0000-0000-0000000007E0', 'filters', '{"status":["ack","resolved"]}'),
  ('00000000-0000-0000-0000-0000000007E1', 'org', '"FAM-001"')
ON CONFLICT (export_id, detail_key) DO NOTHING;

INSERT INTO api_keys (id, owner_user_id, key_hash, label, created_at, expires_at, revoked_at, scopes)
VALUES
  (
    '00000000-0000-0000-0000-0000000007F0',
    (SELECT id FROM users WHERE email='admin@heartguard.com'),
    encode(digest('HGDEMO-KEY-1', 'sha256'), 'hex'),
    'Demo - Integración CLI',
    NOW() - INTERVAL '15 days',
    NOW() + INTERVAL '15 days',
    NULL,
    ARRAY['alerts.read','patients.read']
  ),
  (
    '00000000-0000-0000-0000-0000000007F1',
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
SELECT '00000000-0000-0000-0000-0000000007F0'::uuid, p.id
FROM permissions p
WHERE p.code IN ('alerts.read','patients.read')
ON CONFLICT DO NOTHING;

INSERT INTO api_key_permission (api_key_id, permission_id)
SELECT '00000000-0000-0000-0000-0000000007F1'::uuid, p.id
FROM permissions p
WHERE p.code IN ('alerts.manage')
ON CONFLICT DO NOTHING;
