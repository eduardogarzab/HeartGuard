-- =========================================================
-- Reinicializar base de datos
-- =========================================================
DROP DATABASE IF EXISTS heartguard;
CREATE DATABASE heartguard;

-- Conectarse a la nueva base
\c heartguard;

-- =========================================================
-- Tabla de Organizaciones
-- =========================================================
CREATE TABLE organizaciones (
  org_id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  fecha_registro TIMESTAMP DEFAULT now()
);

-- =========================================================
-- Tabla de Pacientes (con credenciales y rol admin/paciente)
-- =========================================================
CREATE TABLE pacientes (
  patient_id SERIAL PRIMARY KEY,
  org_id INT NOT NULL REFERENCES organizaciones(org_id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  edad INT,
  sexo VARCHAR(10),
  altura_cm DECIMAL(5,2),
  peso_kg DECIMAL(5,2),
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_admin BOOLEAN DEFAULT false,
  fecha_registro TIMESTAMP DEFAULT now()
);

-- =========================================================
-- Constraint: solo un admin por organización
-- =========================================================
CREATE UNIQUE INDEX unique_admin_per_org
ON pacientes(org_id)
WHERE is_admin = true;

-- =========================================================
-- Tabla: Predicciones de IA
-- =========================================================
CREATE TABLE predicciones_ia (
  pred_id SERIAL PRIMARY KEY,
  patient_id INT NOT NULL REFERENCES pacientes(patient_id) ON DELETE CASCADE,
  modelo VARCHAR(50) NOT NULL,
  riesgo_estimado VARCHAR(20),
  probabilidad DECIMAL(5,2),
  detalles JSONB,
  timestamp TIMESTAMP DEFAULT now()
);

-- =========================================================
-- Tabla: Alertas
-- =========================================================
CREATE TABLE alertas (
  alert_id SERIAL PRIMARY KEY,
  patient_id INT NOT NULL REFERENCES pacientes(patient_id) ON DELETE CASCADE,
  pred_id INT REFERENCES predicciones_ia(pred_id) ON DELETE SET NULL,
  tipo_alerta VARCHAR(50),
  nivel_riesgo VARCHAR(20),
  timestamp TIMESTAMP DEFAULT now()
);

-- =========================================================
-- Tabla: Ubicaciones de Alertas
-- =========================================================
CREATE TABLE ubicaciones_alertas (
  ubicacion_id SERIAL PRIMARY KEY,
  alert_id INT NOT NULL REFERENCES alertas(alert_id) ON DELETE CASCADE,
  latitud DECIMAL(9,6) NOT NULL,
  longitud DECIMAL(9,6) NOT NULL,
  timestamp TIMESTAMP DEFAULT now()
);

-- =========================================================
-- Tabla: Contactos de Emergencia
-- =========================================================
CREATE TABLE contactos_emergencia (
  contacto_id SERIAL PRIMARY KEY,
  patient_id INT NOT NULL REFERENCES pacientes(patient_id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  relacion VARCHAR(50),
  telefono VARCHAR(20),
  email VARCHAR(100)
);

-- =========================================================
-- Datos de ejemplo (2 organizaciones con un admin cada una)
-- =========================================================

-- Org 1: Familia Jorge
INSERT INTO organizaciones (nombre) VALUES ('Familia Jorge');
INSERT INTO pacientes (org_id, nombre, username, password_hash, is_admin)
VALUES (
  1,
  'Jorge Admin',
  'jorge_admin',
  '$2a$12$WTeXNz2xL79kYzlXFvvde.IKcaphY5tNF3dEl0RTZhhmOnyP0VQpK', -- hash bcrypt de "jorge123"
  true
);

-- Org 2: Familia Pepe
INSERT INTO organizaciones (nombre) VALUES ('Familia Pepe');
INSERT INTO pacientes (org_id, nombre, username, password_hash, is_admin)
VALUES (
  2,
  'Pepe Admin',
  'pepe_admin',
  '$2a$12$f7/A/cWH/oH/wWjhd8CTBeRym.pFm6KY94yFk315SwgdFvEQYWwW6', -- hash bcrypt de "pepe123"
  true
);
