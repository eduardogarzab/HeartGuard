-- =========================================================
-- HeartGuard - Sistema de Monitoreo de Salud para Colonias
-- Base de datos PostgreSQL para datos estructurados
-- =========================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================
-- Tabla: Colonias (Admin de admin)
-- =========================================================
CREATE TABLE colonias (
  colonia_id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  direccion TEXT,
  encargado_id INT, -- Referencia a un usuario admin de admin
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  activa BOOLEAN DEFAULT true
);

-- =========================================================
-- Tabla: Familias (Admin de familia)
-- =========================================================
CREATE TABLE familias (
  familia_id SERIAL PRIMARY KEY,
  colonia_id INT NOT NULL REFERENCES colonias(colonia_id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  admin_id INT, -- Referencia a un usuario admin de familia
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  activa BOOLEAN DEFAULT true
);

-- =========================================================
-- Tabla: Usuarios (Admin de familia y miembros)
-- =========================================================
CREATE TABLE usuarios (
  usuario_id SERIAL PRIMARY KEY,
  familia_id INT NOT NULL REFERENCES familias(familia_id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100),
  email VARCHAR(255) UNIQUE,
  telefono VARCHAR(20),
  fecha_nacimiento DATE,
  rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin_colonia', 'admin_familia', 'usuario')),
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  activo BOOLEAN DEFAULT true,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ultimo_acceso TIMESTAMP
);

-- =========================================================
-- Tabla: Contactos de Emergencia
-- =========================================================
CREATE TABLE contactos_emergencia (
  contacto_id SERIAL PRIMARY KEY,
  usuario_id INT NOT NULL REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  relacion VARCHAR(50),
  telefono VARCHAR(20) NOT NULL,
  email VARCHAR(100),
  es_principal BOOLEAN DEFAULT false,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Tabla: Alertas Históricas
-- =========================================================
CREATE TABLE alertas (
  alerta_id SERIAL PRIMARY KEY,
  usuario_id INT NOT NULL REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
  tipo VARCHAR(50) NOT NULL, -- 'frecuencia_cardiaca', 'presion_arterial', 'caida', 'ubicacion'
  nivel VARCHAR(20) NOT NULL, -- 'bajo', 'medio', 'alto', 'critico'
  mensaje TEXT,
  datos_adicionales JSONB, -- Para almacenar valores específicos de la métrica
  resuelta BOOLEAN DEFAULT false,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_resolucion TIMESTAMP
);

-- =========================================================
-- Tabla: Sesiones de Usuario (para Redis)
-- =========================================================
CREATE TABLE sesiones_usuario (
  sesion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  usuario_id INT NOT NULL REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
  token_jwt TEXT NOT NULL,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_expiracion TIMESTAMP NOT NULL,
  activa BOOLEAN DEFAULT true,
  ip_address INET,
  user_agent TEXT
);

-- =========================================================
-- Índices para optimizar consultas
-- =========================================================
CREATE INDEX idx_usuarios_familia ON usuarios(familia_id);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);
CREATE INDEX idx_familias_colonia ON familias(colonia_id);
CREATE INDEX idx_alertas_usuario ON alertas(usuario_id);
CREATE INDEX idx_alertas_fecha ON alertas(fecha_creacion);
CREATE INDEX idx_contactos_usuario ON contactos_emergencia(usuario_id);
CREATE INDEX idx_sesiones_usuario ON sesiones_usuario(usuario_id);
CREATE INDEX idx_sesiones_activa ON sesiones_usuario(activa);

-- =========================================================
-- Constraints de integridad
-- =========================================================

-- Solo un admin de colonia por colonia (a través de familia)
CREATE UNIQUE INDEX unique_admin_colonia_per_familia
ON usuarios(familia_id)
WHERE rol = 'admin_colonia' AND activo = true;

-- Solo un admin de familia por familia
CREATE UNIQUE INDEX unique_admin_familia_per_familia
ON usuarios(familia_id)
WHERE rol = 'admin_familia' AND activo = true;

-- =========================================================
-- Datos de ejemplo para testing
-- =========================================================

-- Insertar colonia de ejemplo
INSERT INTO colonias (nombre, direccion) 
VALUES ('Colonia Las Palmas', 'Av. Principal 123, Ciudad de México');

-- Insertar familia de ejemplo
INSERT INTO familias (colonia_id, nombre) 
VALUES (1, 'Familia García');

-- Insertar admin de colonia
INSERT INTO usuarios (familia_id, nombre, apellido, email, rol, username, password_hash)
VALUES (
  1,
  'María',
  'García',
  'maria.garcia@heartguard.com',
  'admin_colonia',
  'maria_admin',
  '$2a$10$uzRA0yR9IewAEtTBmT.CjOD/Bka4NcBwnHQCS3XqgX721gT7IkCqS' -- hash de "admin123"
);

-- Insertar admin de familia
INSERT INTO usuarios (familia_id, nombre, apellido, email, rol, username, password_hash)
VALUES (
  1,
  'Carlos',
  'García',
  'carlos.garcia@heartguard.com',
  'admin_familia',
  'carlos_admin',
  '$2a$10$uzRA0yR9IewAEtTBmT.CjOD/Bka4NcBwnHQCS3XqgX721gT7IkCqS' -- hash de "admin123"
);

-- Insertar usuario normal
INSERT INTO usuarios (familia_id, nombre, apellido, email, rol, username, password_hash)
VALUES (
  1,
  'Ana',
  'García',
  'ana.garcia@heartguard.com',
  'usuario',
  'ana_user',
  '$2a$10$uzRA0yR9IewAEtTBmT.CjOD/Bka4NcBwnHQCS3XqgX721gT7IkCqS' -- hash de "admin123"
);

-- Insertar contactos de emergencia
INSERT INTO contactos_emergencia (usuario_id, nombre, relacion, telefono, email, es_principal)
VALUES 
(3, 'Dr. Juan Pérez', 'Médico de cabecera', '+52-55-1234-5678', 'dr.perez@hospital.com', true),
(3, 'María García', 'Madre', '+52-55-8765-4321', 'maria.madre@email.com', false);

-- Actualizar referencias de admin en las tablas
UPDATE colonias SET encargado_id = 1 WHERE colonia_id = 1;
UPDATE familias SET admin_id = 2 WHERE familia_id = 1;
