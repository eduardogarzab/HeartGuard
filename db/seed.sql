-- =========================================================
-- HeartGuard DB (v2.5) - SEED (datos iniciales)
-- =========================================================

-- Conectarse a la base de datos heartguard
\connect heartguard

-- Configurar search_path para usar el schema heartguard
SET search_path = heartguard, public;

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

INSERT INTO device_types(code,label) VALUES
  ('ECG_1LEAD','ECG portátil de una derivación'),
  ('PULSE_OX','Oxímetro de pulso domiciliario')
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

INSERT INTO risk_levels(code, label, weight) VALUES
  ('low', 'Bajo', 1),
  ('medium', 'Medio', 2),
  ('high', 'Alto', 3)
ON CONFLICT (code) DO NOTHING;

INSERT INTO team_member_roles(code, label) VALUES
  ('doctor', 'Doctor/a'),
  ('nurse', 'Enfermero/a'),
  ('admin', 'Administrador/a de Equipo'),
  ('specialist', 'Especialista')
ON CONFLICT (code) DO NOTHING;

-- Roles del sistema
INSERT INTO roles(code, label, description) VALUES
  ('superadmin','Superadministrador','Acceso completo al panel de superadministración'),
  ('user','Usuario','Usuario normal del sistema sin acceso al panel de superadmin'),
  ('org_admin','Admin de Organización','Administrador con permisos completos en la organización'),
  ('org_viewer','Observador de Organización','Acceso de solo lectura a datos de la organización')
ON CONFLICT (code) DO NOTHING;

INSERT INTO system_settings (id, brand_name, support_email, primary_color, secondary_color, logo_url, contact_phone, default_locale, default_timezone, maintenance_mode, maintenance_message)
VALUES (1, 'HeartGuard', 'support@heartguard.com', '#0ea5e9', '#1e293b', NULL, '+52 55 1234 5678', 'es-MX', 'America/Mexico_City', FALSE, NULL)
ON CONFLICT (id) DO NOTHING;

-- Estados de alerta
INSERT INTO alert_status(code, description, step_order) VALUES
  ('created','Generada por regla/modelo',1),
  ('notified','Notificada a canal/es',2),
  ('ack','Reconocida por usuario',3),
  ('resolved','Resuelta',4),
  ('closed','Cerrada',5)
ON CONFLICT (code) DO NOTHING;

-- Tipos de alerta (rango de severidad por nivel)
-- Incluye todos los tipos que el modelo de IA puede generar
INSERT INTO alert_types(code, description, severity_min_id, severity_max_id)
SELECT x.code, x.description,
       (SELECT id FROM alert_levels WHERE code = x.min_code),
       (SELECT id FROM alert_levels WHERE code = x.max_code)
FROM (VALUES
  ('GENERAL_RISK','Riesgo general de salud','low','critical'),
  ('ARRHYTHMIA','Arritmia - Ritmo cardiaco anómalo','medium','critical'),
  ('DESAT','Desaturación de oxígeno','low','critical'),
  ('HYPERTENSION','Hipertensión arterial','medium','critical'),
  ('HYPOTENSION','Hipotensión arterial','medium','critical'),
  ('FEVER','Fiebre','low','high'),
  ('HYPOTHERMIA','Hipotermia','medium','critical')
) AS x(code,description,min_code,max_code)
ON CONFLICT (code) DO NOTHING;

-- Tipos de evento (severidad por defecto)
-- Incluye todos los tipos que el modelo de IA puede detectar
INSERT INTO event_types(code, description, severity_default_id)
SELECT x.code, x.description, (SELECT id FROM alert_levels WHERE code = x.def_level)
FROM (VALUES
  ('GENERAL_RISK','Riesgo general de salud detectado por IA','medium'),
  ('ARRHYTHMIA','Arritmia - Frecuencia cardiaca anormal','high'),
  ('DESAT','Desaturación de oxígeno','high'),
  ('HYPERTENSION','Hipertensión arterial','medium'),
  ('HYPOTENSION','Hipotensión arterial','high'),
  ('FEVER','Fiebre - Temperatura elevada','medium'),
  ('HYPOTHERMIA','Hipotermia - Temperatura baja','high')
) AS x(code,description,def_level)
ON CONFLICT (code) DO NOTHING;

-- Tipos de dispositivo
INSERT INTO device_types(code, label) VALUES
  ('ECG_1LEAD','ECG de una derivación'),
  ('PULSE_OX','Pulsioxímetro')
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
INSERT INTO users (name, email, password_hash, user_status_id, role_code, two_factor_enabled, created_at)
VALUES (
  'Super Admin',
  'admin@heartguard.com',
  crypt('Admin#2025', gen_salt('bf', 10)),
  (SELECT id FROM user_statuses WHERE code='active'),
  'superadmin',
  FALSE,
  NOW()
)
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    password_hash = EXCLUDED.password_hash,
    user_status_id = EXCLUDED.user_status_id,
    role_code = EXCLUDED.role_code;

-- Organización demo
INSERT INTO organizations(code,name) VALUES ('FAM-001','Familia García')
ON CONFLICT (code) DO NOTHING;

INSERT INTO organizations(code,name) VALUES
  ('CLIN-001','Clínica Central'),
  ('OPS-001','Servicios Operativos HG')
ON CONFLICT (code) DO NOTHING;

-- Usuarios adicionales para métricas (password demo: Demo#2025)
INSERT INTO users (name, email, password_hash, user_status_id, role_code, two_factor_enabled, created_at)
VALUES
  ('Dra. Ana Ruiz','ana.ruiz@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='active'), 'user', TRUE, NOW() - INTERVAL '90 days'),
  ('Martín López','martin.ops@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='active'), 'user', FALSE, NOW() - INTERVAL '60 days'),
  ('Sofía Care','sofia.care@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='pending'), 'user', FALSE, NOW() - INTERVAL '15 days'),
  ('Carlos Vega','carlos.vega@heartguard.com', crypt('Demo#2025', gen_salt('bf', 10)), (SELECT id FROM user_statuses WHERE code='blocked'), 'user', FALSE, NOW() - INTERVAL '120 days')
ON CONFLICT (email) DO NOTHING;

-- Membresías por organización
-- Membresías por organización
INSERT INTO user_org_membership (org_id, user_id, role_code, joined_at)
SELECT o.id, u.id, 'org_admin', NOW() - INTERVAL '60 days'
FROM organizations o, users u
WHERE o.code='FAM-001' AND u.email='ana.ruiz@heartguard.com'
ON CONFLICT (org_id, user_id) DO NOTHING;

INSERT INTO user_org_membership (org_id, user_id, role_code, joined_at)
SELECT o.id, u.id, 'org_admin', NOW() - INTERVAL '45 days'
FROM organizations o, users u
WHERE o.code='FAM-001' AND u.email='martin.ops@heartguard.com'
ON CONFLICT (org_id, user_id) DO NOTHING;

INSERT INTO user_org_membership (org_id, user_id, role_code, joined_at)
SELECT o.id, u.id, 'org_viewer', NOW() - INTERVAL '20 days'
FROM organizations o, users u
WHERE o.code='CLIN-001' AND u.email='sofia.care@heartguard.com'
ON CONFLICT (org_id, user_id) DO NOTHING;

-- Invitaciones demo (pendiente, usada, revocada)
INSERT INTO org_invitations (org_id, email, role_code, token, expires_at, used_at, revoked_at, created_by, created_at)
VALUES
  (
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'coordinador@heartguard.com',
    'org_admin',
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
    'org_admin',
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
    'org_viewer',
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

INSERT INTO patients (id, org_id, person_name, email, password_hash, birthdate, sex_id, risk_level_id, created_at)
VALUES
  (
    '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'María Delgado',
    'maria.delgado@patients.heartguard.com',
    crypt('Paciente#2025', gen_salt('bf', 10)),
    '1978-03-22',
    (SELECT id FROM sexes WHERE code='F'),
    (SELECT id FROM risk_levels WHERE code='high'),
    NOW() - INTERVAL '120 days'
  ),
  (
    'fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21'::uuid,
    (SELECT id FROM organizations WHERE code='CLIN-001'),
    'José Hernández',
    'jose.hernandez@patients.heartguard.com',
    crypt('Paciente#2025', gen_salt('bf', 10)),
    '1965-11-04',
    (SELECT id FROM sexes WHERE code='M'),
    (SELECT id FROM risk_levels WHERE code='medium'),
    NOW() - INTERVAL '180 days'
  ),
  (
    'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
    (SELECT id FROM organizations WHERE code='FAM-001'),
    'Valeria Ortiz',
    'valeria.ortiz@patients.heartguard.com',
    crypt('Paciente#2025', gen_salt('bf', 10)),
    '1992-07-15',
    (SELECT id FROM sexes WHERE code='F'),
    (SELECT id FROM risk_levels WHERE code='low'),
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

INSERT INTO care_team_member (care_team_id, user_id, role_id, joined_at)
SELECT '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid, u.id, (SELECT id FROM team_member_roles WHERE code='specialist'), NOW() - INTERVAL '120 days'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_id, joined_at)
SELECT '1ad17404-323c-4469-86eb-aef83336d1c9'::uuid, u.id, (SELECT id FROM team_member_roles WHERE code='admin'), NOW() - INTERVAL '100 days'
FROM users u
WHERE u.email='martin.ops@heartguard.com'
ON CONFLICT DO NOTHING;

INSERT INTO care_team_member (care_team_id, user_id, role_id, joined_at)
SELECT 'a9c83e54-30e5-4487-abb5-1f97a10cca17'::uuid, u.id, (SELECT id FROM team_member_roles WHERE code='doctor'), NOW() - INTERVAL '150 days'
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

-- Ground truth para María Delgado (8c9436b4-f085-405f-a3d2-87cb1d1cf097)
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

-- Ground truth adicional para María Delgado - Arritmia
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'a1b2c3d4-5678-90ab-cdef-000000000001'::uuid,
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  et.id,
  NOW() - INTERVAL '48 hours',
  NOW() - INTERVAL '47 hours 45 minutes',
  (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  'manual-review',
  'Episodio de taquicardia sinusal durante actividad física moderada'
FROM event_types et
WHERE et.code='ARRHYTHMIA'
ON CONFLICT (id) DO NOTHING;

-- Ground truth adicional para María Delgado - Desaturación
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'b2c3d4e5-6789-01bc-def1-000000000002'::uuid,
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  et.id,
  NOW() - INTERVAL '72 hours',
  NOW() - INTERVAL '71 hours 20 minutes',
  (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  'device-sync',
  'Episodio leve de desaturación durante ejercicio - patrón normal'
FROM event_types et
WHERE et.code='DESAT'
ON CONFLICT (id) DO NOTHING;

-- Ground truth adicional para María Delgado - Hipertensión
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'f1e2d3c4-b5a6-9788-0abc-000000000006'::uuid,
  '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid,
  et.id,
  NOW() - INTERVAL '96 hours',
  NOW() - INTERVAL '95 hours 30 minutes',
  (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
  'manual-review',
  'Pico hipertensivo relacionado con estrés - controlado'
FROM event_types et
WHERE et.code='HYPERTENSION'
ON CONFLICT (id) DO NOTHING;

-- Ground truth para José Hernández (fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21)
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

-- Ground truth para Valeria Ortiz (ae15cd87-5ac2-4f90-8712-184b02c541a5)
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'c3d4e5f6-7890-12cd-ef23-000000000003'::uuid,
  'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
  et.id,
  NOW() - INTERVAL '12 hours',
  NOW() - INTERVAL '11 hours 40 minutes',
  (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  'manual-review',
  'Arritmia leve detectada - episodio breve auto-limitado'
FROM event_types et
WHERE et.code='ARRHYTHMIA'
ON CONFLICT (id) DO NOTHING;

-- Ground truth adicional para Valeria Ortiz - Riesgo general
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'd4e5f6a7-8901-23de-f456-000000000004'::uuid,
  'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
  et.id,
  NOW() - INTERVAL '24 hours',
  NOW() - INTERVAL '23 hours 50 minutes',
  (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  'device-sync',
  'Patrón de riesgo bajo detectado durante ejercicio'
FROM event_types et
WHERE et.code='GENERAL_RISK'
ON CONFLICT (id) DO NOTHING;

-- Ground truth adicional para Valeria Ortiz - Hipotensión
INSERT INTO ground_truth_labels (id, patient_id, event_type_id, onset, offset_at, annotated_by_user_id, source, note)
SELECT
  'e5f6a7b8-9012-34ef-5678-000000000005'::uuid,
  'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid,
  et.id,
  NOW() - INTERVAL '36 hours',
  NOW() - INTERVAL '35 hours 45 minutes',
  (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
  'manual-review',
  'Episodio breve de hipotensión postural - sin complicaciones'
FROM event_types et
WHERE et.code='HYPOTENSION'
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
    'heartguard',
    'timeseries',
    'ecg_waveform',
    '30d',
    NOW() - INTERVAL '7 days'
  ),
  (
    '333d08ad-b521-4d3b-9259-9013ff6aa360',
    '7470ea38-4d6d-4519-9bb8-766d2dee575a',
    'heartguard',
    'timeseries',
    'spo2_series',
    '14d',
    NOW() - INTERVAL '3 days'
  )
ON CONFLICT (id) DO UPDATE SET influx_org = EXCLUDED.influx_org, influx_bucket = EXCLUDED.influx_bucket;

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
  ),
  (
    '988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc'::uuid,
    'HeartGuard RandomForest',
    '1.0.0',
    'health_anomaly_detection',
    's3://heartguard-models/randomforest/v1.0.0',
    '{"n_estimators":100,"max_depth":10,"min_samples_split":5}'::jsonb,
    NOW() - INTERVAL '30 days'
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
  (SELECT id FROM alert_status WHERE code='resolved'),
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
  NOW() - INTERVAL '30 hours',
  'Stabilized',
  'Paciente respondió favorablemente a intervención remota'
FROM users u
WHERE u.email='ana.ruiz@heartguard.com'
ON CONFLICT (id) DO NOTHING;

-- Resolución para la primera alerta 'c20277df-7c2f-417c-902e-776bf4bf74c3'
INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
SELECT
  'a1b2c3d4-5678-90ab-cdef-1234567890ab'::uuid,
  'c20277df-7c2f-417c-902e-776bf4bf74c3'::uuid,
  u.id,
  NOW() - INTERVAL '50 minutes',
  'Resolved',
  'Alerta resuelta después de seguimiento'
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

-- =========================================================
-- Adicional: poblar métricas/GRÁFICAS (más datos para KPIs)
-- =========================================================

-- Service health adicionales (últimas 7 días) para promediar latencia
INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT gen_random_uuid(), (SELECT id FROM services WHERE name='superadmin-api'), NOW() - INTERVAL '2 hours', (SELECT id FROM service_statuses WHERE code='up'), 190, '1.8.6'
WHERE NOT EXISTS (SELECT 1 FROM service_health sh WHERE sh.service_id = (SELECT id FROM services WHERE name='superadmin-api') AND sh.checked_at > NOW() - INTERVAL '3 hours');

INSERT INTO service_health (id, service_id, checked_at, service_status_id, latency_ms, version)
SELECT gen_random_uuid(), (SELECT id FROM services WHERE name='streaming-hub'), NOW() - INTERVAL '30 minutes', (SELECT id FROM service_statuses WHERE code='up'), 160, '2.4.2'
WHERE NOT EXISTS (SELECT 1 FROM service_health sh WHERE sh.service_id = (SELECT id FROM services WHERE name='streaming-hub') AND sh.checked_at > NOW() - INTERVAL '1 hour');

-- Señales activas recientes (para ActivePatientsCount)
INSERT INTO signal_streams (id, patient_id, device_id, signal_type_id, sample_rate_hz, started_at, ended_at)
SELECT gen_random_uuid()::uuid, 'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid, '1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d'::uuid, (SELECT id FROM signal_types WHERE code='HR'), 1, NOW() - INTERVAL '2 days', NULL
WHERE NOT EXISTS (SELECT 1 FROM signal_streams ss WHERE ss.patient_id = 'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid AND ss.started_at > NOW() - INTERVAL '7 days');

-- Añadir inferences para diversificar el breakdown de inferencias
INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT gen_random_uuid()::uuid, '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid, (SELECT ss.id FROM signal_streams ss JOIN devices d ON ss.device_id = d.id WHERE d.serial = 'HG-ECG-001' LIMIT 1), NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours 58 minutes', (SELECT id FROM event_types WHERE code='AFIB'), 0.91, 0.8, '{}'::jsonb, NOW() - INTERVAL '3 hours 58 minutes', 'sim/1'
WHERE NOT EXISTS (SELECT 1 FROM inferences i WHERE i.model_id = '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid AND i.created_at > NOW() - INTERVAL '5 hours');

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT gen_random_uuid()::uuid, 'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid, (SELECT ss.id FROM signal_streams ss JOIN devices d ON ss.device_id = d.id WHERE d.serial = 'HG-PUL-201' LIMIT 1), NOW() - INTERVAL '26 hours', NOW() - INTERVAL '25 hours 58 minutes', (SELECT id FROM event_types WHERE code='DESAT'), 0.72, 0.6, '{}'::jsonb, NOW() - INTERVAL '25 hours 58 minutes', 'sim/2'
WHERE NOT EXISTS (SELECT 1 FROM inferences i WHERE i.model_id = 'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid AND i.created_at > NOW() - INTERVAL '2 days');

-- Auditoría adicional para operaciones recientes
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip, details)
SELECT gen_random_uuid()::uuid, (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'), 'ALERT_ACK', 'alert', (SELECT id FROM alerts LIMIT 1), NOW() - INTERVAL '70 minutes', '10.0.0.15', jsonb_build_object('note','ACK desde UI')
WHERE NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.action='ALERT_ACK' AND a.ts > NOW() - INTERVAL '2 hours');

INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip, details)
SELECT gen_random_uuid()::uuid, (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), 'ALERT_RESOLVE', 'alert', (SELECT id FROM alerts WHERE status_id = (SELECT id FROM alert_status WHERE code='resolved') LIMIT 1), NOW() - INTERVAL '33 hours', '10.0.0.16', jsonb_build_object('outcome','Stabilized')
WHERE NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.action='ALERT_RESOLVE' AND a.ts > NOW() - INTERVAL '48 hours');

INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip, details)
SELECT gen_random_uuid()::uuid,
       (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
       'ALERT_RESOLUTION_CREATE',
       'alert_resolution',
       (SELECT id FROM alert_resolution ORDER BY resolved_at DESC LIMIT 1),
       NOW() - INTERVAL '33 hours',
       '10.0.0.16',
       jsonb_build_object('alert_id', (SELECT alert_id::text FROM alert_resolution ORDER BY resolved_at DESC LIMIT 1), 'outcome', 'Stabilized')
WHERE NOT EXISTS (
    SELECT 1 FROM audit_logs a
    WHERE a.action = 'ALERT_RESOLUTION_CREATE'
      AND a.ts > NOW() - INTERVAL '48 hours'
);

-- Alert resolutions/outcomes adicionales (para breakdown)
INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
SELECT gen_random_uuid()::uuid, a.id, (SELECT id FROM users WHERE email='martin.ops@heartguard.com'), NOW() - INTERVAL '5 days', 'Escalated', 'Derivado a equipo de guardia'
FROM alerts a
WHERE a.status_id = (SELECT id FROM alert_status WHERE code='resolved')
  AND NOT EXISTS (SELECT 1 FROM alert_resolution ar WHERE ar.alert_id = a.id AND ar.outcome = 'Escalated');

-- Disconnected device demo: a device active but sin señales recientes (>24h)
INSERT INTO devices (id, org_id, serial, brand, model, device_type_id, owner_patient_id, registered_at, active)
SELECT gen_random_uuid()::uuid, (SELECT id FROM organizations WHERE code='OPS-001'), 'HG-ECG-OLD-01', 'Cardia', 'Wave Legacy', (SELECT id FROM device_types WHERE code='ECG_1LEAD'), NULL, NOW() - INTERVAL '720 days', TRUE
WHERE NOT EXISTS (SELECT 1 FROM devices d WHERE d.serial='HG-ECG-OLD-01');

-- Ensure that this old device has no recent signal (simulate disconnected)
DELETE FROM signal_streams ss WHERE ss.device_id = (SELECT id FROM devices WHERE serial='HG-ECG-OLD-01') AND ss.started_at > NOW() - INTERVAL '30 days';


-- =========================================================
-- SINCRONIZACIÓN INFLUXDB-POSTGRESQL
-- =========================================================
-- Este script crea automáticamente streams y bindings para dispositivos
-- que están ASIGNADOS a pacientes y ACTIVOS.
-- 
-- Flujo de trabajo:
-- 1. Organización compra dispositivo (INSERT en devices con owner_patient_id=NULL)
-- 2. Administrador asigna dispositivo a paciente (UPDATE devices SET owner_patient_id=X)
-- 3. Este trigger automáticamente crea:
--    - signal_stream (para captura de datos)
--    - timeseries_binding (vinculación con InfluxDB)
--    - timeseries_binding_tag (tags custom: location, floor, GPS)

-- Trigger para crear automáticamente stream y binding cuando se asigna un dispositivo
CREATE OR REPLACE FUNCTION create_stream_on_device_assignment()
RETURNS TRIGGER AS $$
DECLARE
  v_signal_type_id UUID;
  v_stream_id UUID;
  v_binding_id UUID;
  v_location_geom GEOMETRY;
  v_gps_long DOUBLE PRECISION;
  v_gps_lat DOUBLE PRECISION;
BEGIN
  -- Solo procesar si:
  -- 1. El dispositivo se está asignando a un paciente (owner_patient_id cambió a NOT NULL)
  -- 2. El dispositivo está activo
  IF NEW.owner_patient_id IS NOT NULL AND NEW.active = TRUE AND 
     (TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND OLD.owner_patient_id IS DISTINCT FROM NEW.owner_patient_id)) THEN
    
    -- Obtener signal_type para vital signs (HR = Heart Rate, genérico para signos vitales)
    SELECT id INTO v_signal_type_id FROM signal_types WHERE code = 'HR' LIMIT 1;
    
    IF v_signal_type_id IS NULL THEN
      RAISE WARNING 'Signal type HR not found, cannot create stream for device %', NEW.serial;
      RETURN NEW;
    END IF;

    -- Verificar si ya existe un stream activo para este dispositivo
    SELECT id INTO v_stream_id
    FROM signal_streams
    WHERE device_id = NEW.id
      AND patient_id = NEW.owner_patient_id
      AND ended_at IS NULL
    LIMIT 1;

    -- Si no existe stream, crearlo
    IF v_stream_id IS NULL THEN
      INSERT INTO signal_streams (
        patient_id,
        device_id,
        signal_type_id,
        sample_rate_hz,
        started_at,
        ended_at
      ) VALUES (
        NEW.owner_patient_id,
        NEW.id,
        v_signal_type_id,
        1.0, -- 1 Hz (1 lectura por segundo)
        NOW(),
        NULL -- Stream activo
      ) RETURNING id INTO v_stream_id;

      RAISE NOTICE 'Stream created for device % assigned to patient %', NEW.serial, NEW.owner_patient_id;

      -- Crear binding a InfluxDB
      INSERT INTO timeseries_binding (
        stream_id,
        influx_org,
        influx_bucket,
        measurement,
        retention_hint
      ) VALUES (
        v_stream_id,
        'heartguard',
        'timeseries',
        'vital_signs',
        '30d'
      ) RETURNING id INTO v_binding_id;

      RAISE NOTICE 'InfluxDB binding created for stream %', v_stream_id;

      -- Obtener ubicación GPS del paciente (última conocida)
      SELECT geom INTO v_location_geom
      FROM patient_locations
      WHERE patient_id = NEW.owner_patient_id
      ORDER BY ts DESC
      LIMIT 1;

      -- Crear tags custom
      IF v_location_geom IS NOT NULL THEN
        v_gps_long := ST_X(v_location_geom);
        v_gps_lat := ST_Y(v_location_geom);

        INSERT INTO timeseries_binding_tag (binding_id, tag_key, tag_value) VALUES
          (v_binding_id, 'gps_longitude', v_gps_long::TEXT),
          (v_binding_id, 'gps_latitude', v_gps_lat::TEXT),
          (v_binding_id, 'location', 'hospital_main'),
          (v_binding_id, 'floor', '3');
      ELSE
        INSERT INTO timeseries_binding_tag (binding_id, tag_key, tag_value) VALUES
          (v_binding_id, 'location', 'hospital_main'),
          (v_binding_id, 'floor', '3');
      END IF;

      RAISE NOTICE 'Tags created for binding %', v_binding_id;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger en la tabla devices
DROP TRIGGER IF EXISTS trg_device_assignment ON devices;
CREATE TRIGGER trg_device_assignment
  AFTER INSERT OR UPDATE OF owner_patient_id, active ON devices
  FOR EACH ROW
  EXECUTE FUNCTION create_stream_on_device_assignment();

-- Ejecutar la lógica para dispositivos ya asignados (migración de datos existentes)
DO $$
DECLARE
  v_device RECORD;
BEGIN
  RAISE NOTICE '✓ Trigger de sincronización automática creado';
  
  FOR v_device IN 
    SELECT id, owner_patient_id FROM devices 
    WHERE owner_patient_id IS NOT NULL AND active = TRUE
  LOOP
    -- Esto disparará el trigger para crear streams si no existen
    UPDATE devices SET active = active WHERE id = v_device.id;
  END LOOP;
  
  RAISE NOTICE '✓ Streams creados para dispositivos existentes asignados';
END $$;


-- =========================================================
-- Datos adicionales para MTTR, volumen de inferencias y alertas sin asignar
-- =========================================================

-- Inferencias recientes (varios tipos) para poblar el breakdown por tipo
INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT gen_random_uuid()::uuid,
       '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
       (SELECT ss.id FROM signal_streams ss JOIN devices d ON ss.device_id = d.id WHERE d.serial = 'HG-ECG-001' ORDER BY ss.started_at DESC LIMIT 1),
       NOW() - INTERVAL '55 minutes',
       NOW() - INTERVAL '54 minutes',
       (SELECT id FROM event_types WHERE code='AFIB'),
       0.88,
       0.8,
       '{}'::jsonb,
       NOW() - INTERVAL '54 minutes',
       'sim/recent/afib'
WHERE NOT EXISTS (SELECT 1 FROM inferences i WHERE i.series_ref = 'sim/recent/afib');

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT gen_random_uuid()::uuid,
       '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
       (SELECT ss.id FROM signal_streams ss JOIN devices d ON ss.device_id = d.id WHERE d.serial = 'HG-ECG-001' ORDER BY ss.started_at DESC LIMIT 1),
       NOW() - INTERVAL '3 hours',
       NOW() - INTERVAL '2 hours 58 minutes',
       (SELECT id FROM event_types WHERE code='TACHY'),
       0.75,
       0.6,
       '{}'::jsonb,
       NOW() - INTERVAL '2 hours 58 minutes',
       'sim/recent/tachy'
WHERE EXISTS (SELECT 1 FROM event_types et WHERE et.code='TACHY')
  AND NOT EXISTS (SELECT 1 FROM inferences i WHERE i.series_ref = 'sim/recent/tachy');

INSERT INTO inferences (id, model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, created_at, series_ref)
SELECT gen_random_uuid()::uuid,
       'e6f09e19-d4c6-4525-976f-316404e4c228'::uuid,
       (SELECT ss.id FROM signal_streams ss JOIN devices d ON ss.device_id = d.id WHERE d.serial = 'HG-PUL-201' ORDER BY ss.started_at DESC LIMIT 1),
       NOW() - INTERVAL '6 hours',
       NOW() - INTERVAL '5 hours 58 minutes',
       (SELECT id FROM event_types WHERE code='DESAT'),
       0.70,
       0.6,
       '{}'::jsonb,
       NOW() - INTERVAL '5 hours 58 minutes',
       'sim/recent/desat'
WHERE NOT EXISTS (SELECT 1 FROM inferences i WHERE i.series_ref = 'sim/recent/desat');


-- Alerta sin asignar (para mostrar "Alertas sin Asignar")
INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
SELECT gen_random_uuid()::uuid,
       p.id,
       at.id,
       '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
       (SELECT id FROM inferences ORDER BY created_at DESC LIMIT 1),
       (SELECT id FROM alert_levels WHERE code='low'),
       (SELECT id FROM alert_status WHERE code='created'),
       NOW() - INTERVAL '30 minutes',
       'Alerta sin asignar: revisión requerida',
       ST_SetSRID(ST_MakePoint(-99.1405, 19.4310), 4326)
FROM patients p, alert_types at
WHERE p.id = 'ae15cd87-5ac2-4f90-8712-184b02c541a5'::uuid
  AND at.code = 'TACHY'
  AND NOT EXISTS (
    SELECT 1 FROM alerts a
    WHERE a.description = 'Alerta sin asignar: revisión requerida'
      AND a.created_at > NOW() - INTERVAL '1 day'
  );


-- Alerta resuelta reciente para MTTR (tiempo de resolución)
INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
SELECT gen_random_uuid()::uuid,
       p.id,
       at.id,
       '7baf7389-9677-4bb5-b533-f0067d2fa4ac'::uuid,
       (SELECT id FROM inferences WHERE series_ref = 'sim/recent/afib' LIMIT 1),
       (SELECT id FROM alert_levels WHERE code='high'),
       (SELECT id FROM alert_status WHERE code='resolved'),
       NOW() - INTERVAL '10 hours',
       'Alerta resuelta demo para cálculo MTTR',
       ST_SetSRID(ST_MakePoint(-99.1360, 19.4330), 4326)
FROM patients p, alert_types at
WHERE p.id = '8c9436b4-f085-405f-a3d2-87cb1d1cf097'::uuid
  AND at.code = 'ARRHYTHMIA'
  AND NOT EXISTS (
    SELECT 1 FROM alerts a
    WHERE a.description = 'Alerta resuelta demo para cálculo MTTR'
      AND a.created_at > NOW() - INTERVAL '7 days'
  );

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
SELECT gen_random_uuid()::uuid,
       a.id,
       (SELECT id FROM users WHERE email='ana.ruiz@heartguard.com'),
  NOW() - INTERVAL '9 hours',
       'Stabilized',
       'Cierre demo para MTTR'
FROM alerts a
WHERE a.description = 'Alerta resuelta demo para cálculo MTTR'
  AND NOT EXISTS (
    SELECT 1 FROM alert_resolution ar WHERE ar.alert_id = a.id AND ar.resolved_at > NOW() - INTERVAL '24 hours'
  );


-- Alertas resueltas adicionales para poblar MTTR
-- =========================================================
-- LIMPIEZA: Eliminar alertas de demo anteriores para evitar duplicados
-- =========================================================
DELETE FROM alert_resolution 
WHERE note IN ('Resolución rápida para MTTR', 'Resolución media para MTTR', 'Resolución lenta para MTTR', 'Demo MTTR reciente', 'Prueba de MTTR dinámico - resuelta rápidamente en 8 minutos', 'MTTR: 30 minutos', 'MTTR: 2 horas', '⚡ PRUEBA: 10 minutos');

DELETE FROM alerts 
WHERE description IN (
  'Alerta resuelta rápida para MTTR',
  'Alerta resuelta media para MTTR', 
  'Alerta resuelta lenta para MTTR',
  'Alerta resuelta demo reciente',
  'PRUEBA DINAMICA MTTR - 8 minutos de resolución',
  'MTTR Demo 1: Resolución rápida',
  'MTTR Demo 2: Resolución media',
  '⚡ PRUEBA DINAMICA: 10 minutos MTTR'
);

-- =========================================================
-- ALERTAS RESUELTAS PARA MTTR CON TIEMPOS CONTROLADOS
-- =========================================================

-- 1. Alerta resuelta rápida: 30 minutos de MTTR
INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
VALUES (
  'aaaaaaaa-1111-1111-1111-000000000001'::uuid,
  (SELECT id FROM patients LIMIT 1),
  (SELECT id FROM alert_types WHERE code='DESAT'),
  (SELECT id FROM models LIMIT 1),
  (SELECT id FROM inferences ORDER BY created_at DESC LIMIT 1),
  (SELECT id FROM alert_levels WHERE code='medium'),
  (SELECT id FROM alert_status WHERE code='resolved'),
  NOW() - INTERVAL '3 hours',
  'MTTR Demo 1: Resolución rápida',
  ST_SetSRID(ST_MakePoint(-99.1370, 19.4340), 4326)
);

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
VALUES (
  'bbbbbbbb-1111-1111-1111-000000000001'::uuid,
  'aaaaaaaa-1111-1111-1111-000000000001'::uuid,
  (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
  NOW() - INTERVAL '2 hours 30 minutes',
  'Resolved',
  'MTTR: 30 minutos'
);

-- 2. Alerta resuelta media: 2 horas de MTTR  
INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
VALUES (
  'aaaaaaaa-2222-2222-2222-000000000002'::uuid,
  (SELECT id FROM patients LIMIT 1),
  (SELECT id FROM alert_types WHERE code='ARRHYTHMIA'),
  (SELECT id FROM models LIMIT 1),
  (SELECT id FROM inferences ORDER BY created_at DESC LIMIT 1),
  (SELECT id FROM alert_levels WHERE code='high'),
  (SELECT id FROM alert_status WHERE code='resolved'),
  NOW() - INTERVAL '8 hours',
  'MTTR Demo 2: Resolución media',
  ST_SetSRID(ST_MakePoint(-99.1380, 19.4350), 4326)
);

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
VALUES (
  'bbbbbbbb-2222-2222-2222-000000000002'::uuid,
  'aaaaaaaa-2222-2222-2222-000000000002'::uuid,
  (SELECT id FROM users WHERE email='sofia.care@heartguard.com'),
  NOW() - INTERVAL '6 hours',
  'Resolved',
  'MTTR: 2 horas'
);

-- 3. ALERTA DE PRUEBA DINÁMICA: 10 minutos de MTTR
INSERT INTO alerts (id, patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, created_at, description, location)
VALUES (
  'aaaaaaaa-9999-9999-9999-000000000999'::uuid,
  (SELECT id FROM patients LIMIT 1),
  (SELECT id FROM alert_types WHERE code='ARRHYTHMIA'),
  (SELECT id FROM models LIMIT 1),
  (SELECT id FROM inferences ORDER BY created_at DESC LIMIT 1),
  (SELECT id FROM alert_levels WHERE code='low'),
  (SELECT id FROM alert_status WHERE code='resolved'),
  NOW() - INTERVAL '20 minutes',
  '⚡ PRUEBA DINAMICA: 10 minutos MTTR',
  ST_SetSRID(ST_MakePoint(-99.1355, 19.4325), 4326)
);

INSERT INTO alert_resolution (id, alert_id, resolved_by_user_id, resolved_at, outcome, note)
VALUES (
  'bbbbbbbb-9999-9999-9999-000000000999'::uuid,
  'aaaaaaaa-9999-9999-9999-000000000999'::uuid,
  (SELECT id FROM users WHERE email='martin.ops@heartguard.com'),
  NOW() - INTERVAL '10 minutes',
  'Resolved',
  '⚡ PRUEBA: 10 minutos'
);

-- =========================================================
-- Trigger: Reasignación Automática de Dispositivos
-- =========================================================
-- Ejecutar con: PGPASSWORD='postgres123' psql -h 134.199.204.58 -U postgres -d heartguard -f trigger_device_reassignment.sql

-- Función que se ejecuta cuando cambia owner_patient_id
CREATE OR REPLACE FUNCTION heartguard.reassign_device_stream()
RETURNS TRIGGER AS $$
DECLARE
    v_signal_type_id UUID;
    v_new_stream_id UUID;
    v_old_measurement TEXT;
    v_old_bucket TEXT;
    v_old_org TEXT;
BEGIN
    -- Solo actuar si cambió el owner_patient_id y no es NULL
    IF NEW.owner_patient_id IS DISTINCT FROM OLD.owner_patient_id 
       AND NEW.owner_patient_id IS NOT NULL THEN
        
        -- Obtener el measurement del stream anterior para replicarlo
        SELECT tb.measurement, tb.influx_bucket, tb.influx_org
        INTO v_old_measurement, v_old_bucket, v_old_org
        FROM heartguard.signal_streams ss
        JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
        WHERE ss.device_id = NEW.id 
          AND ss.ended_at IS NULL
        LIMIT 1;
        
        -- Si no hay stream anterior, usar valores por defecto
        IF v_old_measurement IS NULL THEN
            v_old_measurement := 'vital_signs';
            v_old_bucket := 'timeseries';
            v_old_org := 'heartguard';
        END IF;
        
        -- Terminar todos los streams activos del dispositivo
        UPDATE heartguard.signal_streams 
        SET ended_at = NOW()
        WHERE device_id = NEW.id 
          AND ended_at IS NULL;
        
        -- Obtener el signal_type_id del stream anterior o usar el primero disponible
        SELECT ss.signal_type_id INTO v_signal_type_id
        FROM heartguard.signal_streams ss
        WHERE ss.device_id = NEW.id
        ORDER BY ss.started_at DESC
        LIMIT 1;
        
        -- Si no hay signal_type previo, buscar uno por defecto (HR o el primero)
        IF v_signal_type_id IS NULL THEN
            SELECT id INTO v_signal_type_id
            FROM heartguard.signal_types
            WHERE code = 'HR'
            LIMIT 1;
            
            IF v_signal_type_id IS NULL THEN
                SELECT id INTO v_signal_type_id
                FROM heartguard.signal_types
                LIMIT 1;
            END IF;
        END IF;
        
        -- Crear nuevo stream para el nuevo owner
        INSERT INTO heartguard.signal_streams (device_id, patient_id, signal_type_id, started_at)
        VALUES (NEW.id, NEW.owner_patient_id, v_signal_type_id, NOW())
        RETURNING id INTO v_new_stream_id;
        
        -- Crear timeseries_binding para el nuevo stream
        INSERT INTO heartguard.timeseries_binding (stream_id, influx_bucket, influx_org, measurement)
        VALUES (v_new_stream_id, v_old_bucket, v_old_org, v_old_measurement);
        
        RAISE NOTICE 'Device % reassigned: stream % created for patient %', 
            NEW.serial, v_new_stream_id, NEW.owner_patient_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger (elimina el anterior si existe)
DROP TRIGGER IF EXISTS device_reassignment_trigger ON heartguard.devices;
CREATE TRIGGER device_reassignment_trigger
    AFTER UPDATE OF owner_patient_id ON heartguard.devices
    FOR EACH ROW
    EXECUTE FUNCTION heartguard.reassign_device_stream();

-- Confirmar creación
SELECT 'Trigger device_reassignment_trigger creado correctamente' as status;

-- =========================================================
-- 2. Trigger: Desactivación de Dispositivos
-- =========================================================
-- Se ejecuta cuando un dispositivo se desactiva (active: true -> false)
-- Termina automáticamente todos los streams activos

CREATE OR REPLACE FUNCTION heartguard.deactivate_device_streams()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el dispositivo se desactiva (active cambia de true a false)
    IF NEW.active = false AND OLD.active = true THEN
        -- Terminar todos los streams activos del dispositivo
        UPDATE heartguard.signal_streams 
        SET ended_at = NOW()
        WHERE device_id = NEW.id 
          AND ended_at IS NULL;
        
        RAISE NOTICE 'Device % deactivated: all active streams terminated', NEW.serial;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger de desactivación
DROP TRIGGER IF EXISTS device_deactivation_trigger ON heartguard.devices;
CREATE TRIGGER device_deactivation_trigger
    AFTER UPDATE OF active ON heartguard.devices
    FOR EACH ROW
    EXECUTE FUNCTION heartguard.deactivate_device_streams();

SELECT '✅ Trigger device_deactivation_trigger creado correctamente' as status;

-- =========================================================
-- Verificación
-- =========================================================
SELECT 
    trigger_name,
    event_manipulation as event,
    event_object_table as table,
    action_statement as function
FROM information_schema.triggers
WHERE trigger_schema = 'heartguard'
  AND event_object_table = 'devices'
ORDER BY trigger_name;

