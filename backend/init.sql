-- =========================================================
-- HeartGuard - Sistema de Superadministración
-- Base de datos PostgreSQL NORMALIZADA con Stored Procedures
-- =========================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =========================================================
-- Tabla: Roles (Normalizada)
-- =========================================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    permisos JSONB DEFAULT '{}',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Tabla: Familias
-- =========================================================
CREATE TABLE familias (
    id SERIAL PRIMARY KEY,
    nombre_familia VARCHAR(100) NOT NULL,
    codigo_familia VARCHAR(20) UNIQUE, -- Código para invitaciones
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Tabla: Usuarios (Normalizada - con familia_id directo)
-- =========================================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INT NOT NULL REFERENCES roles(id),
    familia_id INT REFERENCES familias(id),
    latitud DECIMAL(9,6),   -- última ubicación rápida
    longitud DECIMAL(9,6),
    ultima_actualizacion TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- Tabla: Ubicaciones (Histórico)
-- =========================================================
CREATE TABLE ubicaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    latitud DECIMAL(9,6) NOT NULL,
    longitud DECIMAL(9,6) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    precision_metros INT,
    fuente VARCHAR(50) DEFAULT 'gps' -- gps, network, manual
);

-- =========================================================
-- Tabla: Alertas
-- =========================================================
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('bajo','medio','alto','critico')),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atendida BOOLEAN DEFAULT FALSE,
    fecha_atencion TIMESTAMP,
    atendido_por INT REFERENCES usuarios(id)
);

-- =========================================================
-- Tabla: Catálogos
-- =========================================================
CREATE TABLE catalogos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    clave VARCHAR(50) NOT NULL,
    valor VARCHAR(255) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tipo, clave)
);

-- =========================================================
-- Tabla: Logs del Sistema
-- =========================================================
CREATE TABLE logs_sistema (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id),
    accion VARCHAR(100),
    detalle JSONB,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Tabla: Microservicios
-- =========================================================
CREATE TABLE microservicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    url VARCHAR(255) NOT NULL,
    estado VARCHAR(20) DEFAULT 'inactivo' CHECK (estado IN ('activo', 'inactivo', 'error')),
    ultima_verificacion TIMESTAMP,
    version VARCHAR(20),
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- ÍNDICES OPTIMIZADOS
-- =========================================================

-- Índices para usuarios
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX idx_usuarios_fecha_creacion ON usuarios(fecha_creacion);

-- Índices para familias
CREATE INDEX idx_familias_codigo ON familias(codigo_familia);

-- Índices para usuarios (incluyendo familia_id)
CREATE INDEX idx_usuarios_familia_id ON usuarios(familia_id);

-- Índices para ubicaciones
CREATE INDEX idx_ubicaciones_usuario_id ON ubicaciones(usuario_id);
CREATE INDEX idx_ubicaciones_timestamp ON ubicaciones(timestamp DESC);
CREATE INDEX idx_ubicaciones_usuario_timestamp ON ubicaciones(usuario_id, timestamp DESC);

-- Índices para alertas
CREATE INDEX idx_alertas_usuario_id ON alertas(usuario_id);
CREATE INDEX idx_alertas_fecha ON alertas(fecha DESC);
CREATE INDEX idx_alertas_atendida ON alertas(atendida) WHERE atendida = false;
CREATE INDEX idx_alertas_nivel ON alertas(nivel) WHERE nivel IN ('alto', 'critico');

-- Índices para catálogos
CREATE INDEX idx_catalogos_tipo ON catalogos(tipo);
CREATE INDEX idx_catalogos_tipo_clave ON catalogos(tipo, clave);

-- Índices para logs
CREATE INDEX idx_logs_usuario_id ON logs_sistema(usuario_id);
CREATE INDEX idx_logs_fecha ON logs_sistema(fecha DESC);
CREATE INDEX idx_logs_accion ON logs_sistema(accion);

-- Índices para microservicios
CREATE INDEX idx_microservicios_estado ON microservicios(estado);
CREATE INDEX idx_microservicios_nombre ON microservicios(nombre);

-- =========================================================
-- VISTAS ÚTILES
-- =========================================================

-- Vista: Usuarios con información completa
CREATE VIEW v_usuarios_completos AS
SELECT 
    u.id, u.nombre, u.email, u.latitud, u.longitud, 
    u.ultima_actualizacion, u.fecha_creacion,
    r.nombre as rol_nombre, r.descripcion as rol_descripcion,
    u.familia_id, f.nombre_familia,
    NULL as relacion, NULL as es_admin_familia
FROM usuarios u
JOIN roles r ON u.rol_id = r.id
LEFT JOIN familias f ON u.familia_id = f.id;

-- Vista: Alertas con información del usuario
CREATE VIEW v_alertas_completas AS
SELECT 
    a.id, a.usuario_id, u.nombre as usuario_nombre,
    f.nombre_familia, a.tipo, a.descripcion, a.nivel,
    a.fecha, a.atendida, a.fecha_atencion,
    u2.nombre as atendido_por_nombre
FROM alertas a
JOIN usuarios u ON a.usuario_id = u.id
LEFT JOIN familias f ON u.familia_id = f.id
LEFT JOIN usuarios u2 ON a.atendido_por = u2.id;

-- Vista: Estadísticas de familias
CREATE VIEW v_estadisticas_familias AS
SELECT 
    f.id, f.nombre_familia, f.fecha_creacion,
    COUNT(u.id) as total_miembros,
    COUNT(CASE WHEN u.rol_id = (SELECT r.id FROM roles r WHERE r.nombre = 'admin_familia') THEN 1 END) as total_admins
FROM familias f
LEFT JOIN usuarios u ON f.id = u.familia_id
GROUP BY f.id, f.nombre_familia, f.fecha_creacion;

-- =========================================================
-- DATOS INICIALES
-- =========================================================

-- Insertar roles por defecto
INSERT INTO roles (nombre, descripcion, permisos) VALUES
('superadmin', 'Superadministrador del sistema', '{"all": true}'),
('admin_familia', 'Administrador de familia', '{"familia": true, "miembros": true, "alertas": true}'),
('miembro', 'Miembro de familia', '{"perfil": true, "metricas": true}');

-- =========================================================
-- CREAR SUPERADMINISTRADOR POR DEFECTO
-- =========================================================

-- Nota: La creación del superadmin se hace después de definir las funciones

-- Insertar catálogos por defecto
INSERT INTO catalogos (tipo, clave, valor, descripcion, activo) VALUES
-- Tipos de alerta
('tipo_alerta', 'ritmo_irregular', 'Ritmo Irregular', 'Alerta por ritmo cardíaco irregular', true),
('tipo_alerta', 'presion_alta', 'Presión Alta', 'Alerta por presión arterial elevada', true),
('tipo_alerta', 'presion_baja', 'Presión Baja', 'Alerta por presión arterial baja', true),
('tipo_alerta', 'frecuencia_alta', 'Frecuencia Alta', 'Alerta por frecuencia cardíaca alta', true),
('tipo_alerta', 'frecuencia_baja', 'Frecuencia Baja', 'Alerta por frecuencia cardíaca baja', true),

-- Niveles de alerta
('nivel_alerta', 'critico', 'Crítico', 'Alerta crítica que requiere atención inmediata', true),
('nivel_alerta', 'alto', 'Alto', 'Alerta de nivel alto', true),
('nivel_alerta', 'medio', 'Medio', 'Alerta de nivel medio', true),
('nivel_alerta', 'bajo', 'Bajo', 'Alerta de nivel bajo', true),

-- Tipos de usuario
('tipo_usuario', 'superadmin', 'Super Administrador', 'Usuario con acceso completo al sistema', true),
('tipo_usuario', 'admin', 'Administrador', 'Usuario con permisos administrativos', true),

-- Estados del sistema
('estado_sistema', 'activo', 'Activo', 'Sistema funcionando correctamente', true),
('estado_sistema', 'mantenimiento', 'Mantenimiento', 'Sistema en mantenimiento', true),
('estado_sistema', 'inactivo', 'Inactivo', 'Sistema desactivado', true);

-- Insertar microservicios por defecto
INSERT INTO microservicios (nombre, url, estado, descripcion) VALUES
('Flask Metrics Service', 'http://localhost:5000', 'inactivo', 'Servicio para métricas fisiológicas'),
('Android API Service', 'http://localhost:8000', 'inactivo', 'API para aplicación móvil Android'),
('Notification Service', 'http://localhost:3000', 'inactivo', 'Servicio de notificaciones push');

-- =========================================================
-- DATOS DE EJEMPLO PARA PRUEBAS
-- =========================================================

-- Insertar familias de ejemplo
INSERT INTO familias (nombre_familia, codigo_familia, fecha_creacion) VALUES
('Familia García', 'GARCIA2024', CURRENT_TIMESTAMP),
('Familia Rodríguez', 'RODRIGUEZ2024', CURRENT_TIMESTAMP),
('Familia López', 'LOPEZ2024', CURRENT_TIMESTAMP);

-- =========================================================
-- FUNCIÓN PARA CREAR SUPERADMINISTRADOR
-- =========================================================
CREATE OR REPLACE FUNCTION crear_superadmin(
    p_nombre VARCHAR(100),
    p_email VARCHAR(150),
    p_password_hash TEXT
)
RETURNS INT AS $$
DECLARE
    v_usuario_id INT;
    v_rol_superadmin_id INT;
BEGIN
    -- Obtener ID del rol superadmin
    SELECT id INTO v_rol_superadmin_id FROM roles WHERE nombre = 'superadmin';
    
    -- Crear usuario superadmin
    INSERT INTO usuarios (nombre, email, password_hash, rol_id)
    VALUES (p_nombre, p_email, p_password_hash, v_rol_superadmin_id)
    RETURNING id INTO v_usuario_id;
    
    RETURN v_usuario_id;
END;
$$ LANGUAGE plpgsql;

-- Crear superadministrador por defecto (password: admin123)
SELECT crear_superadmin(
    'Super Administrador',
    'admin@heartguard.com',
    '$2a$10$N7KxoF.LMMfTn0rD04rc.eR3P5ENvz3hnhIhZMTrS4.QmGjTLo4.W'
);

-- Insertar usuarios adicionales (no superadmin)
INSERT INTO usuarios (nombre, email, password_hash, rol_id, fecha_creacion) VALUES
('Juan García', 'juan.garcia@email.com', '$2a$10$N7KxoF.LMMfTn0rD04rc.eR3P5ENvz3hnhIhZMTrS4.QmGjTLo4.W', 
 (SELECT id FROM roles WHERE nombre = 'admin_familia'), CURRENT_TIMESTAMP),
('María García', 'maria.garcia@email.com', '$2a$10$N7KxoF.LMMfTn0rD04rc.eR3P5ENvz3hnhIhZMTrS4.QmGjTLo4.W', 
 (SELECT id FROM roles WHERE nombre = 'miembro'), CURRENT_TIMESTAMP),
('Carlos Rodríguez', 'carlos.rodriguez@email.com', '$2a$10$N7KxoF.LMMfTn0rD04rc.eR3P5ENvz3hnhIhZMTrS4.QmGjTLo4.W', 
 (SELECT id FROM roles WHERE nombre = 'admin_familia'), CURRENT_TIMESTAMP),
('Ana López', 'ana.lopez@email.com', '$2a$10$N7KxoF.LMMfTn0rD04rc.eR3P5ENvz3hnhIhZMTrS4.QmGjTLo4.W', 
 (SELECT id FROM roles WHERE nombre = 'miembro'), CURRENT_TIMESTAMP);

-- Asignar usuarios a familias (usando la nueva estructura)
UPDATE usuarios SET familia_id = 2 WHERE id IN (2, 3);  -- Juan y María García a familia García
UPDATE usuarios SET familia_id = 3 WHERE id IN (4, 5);  -- Carlos y Ana a familia López

-- Insertar ubicaciones de ejemplo
INSERT INTO ubicaciones (usuario_id, latitud, longitud, timestamp, precision_metros, fuente) VALUES
(2, 19.4326, -99.1332, CURRENT_TIMESTAMP - INTERVAL '1 hour', 5, 'gps'),
(3, 19.4330, -99.1335, CURRENT_TIMESTAMP - INTERVAL '2 hours', 8, 'gps'),
(4, 19.4320, -99.1325, CURRENT_TIMESTAMP - INTERVAL '30 minutes', 3, 'gps'),
(5, 19.4335, -99.1340, CURRENT_TIMESTAMP - INTERVAL '1 hour 30 minutes', 6, 'gps');

-- Insertar alertas de ejemplo
INSERT INTO alertas (usuario_id, tipo, descripcion, nivel, fecha) VALUES
(3, 'frecuencia_cardiaca', 'Frecuencia cardíaca elevada detectada: 120 bpm', 'alto', CURRENT_TIMESTAMP - INTERVAL '30 minutes'),
(4, 'presion_arterial', 'Presión arterial alta: 150/95 mmHg', 'critico', CURRENT_TIMESTAMP - INTERVAL '1 hour'),
(5, 'oxigenacion', 'Saturación de oxígeno baja: 88%', 'medio', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
(2, 'frecuencia_cardiaca', 'Frecuencia cardíaca irregular detectada', 'alto', CURRENT_TIMESTAMP - INTERVAL '45 minutes');

-- =========================================================
-- STORED PROCEDURES
-- =========================================================

-- 1. Crear superadministrador (movido al inicio)

-- 2. Dashboard ejecutivo
CREATE OR REPLACE FUNCTION sp_dashboard_ejecutivo()
RETURNS TABLE (
    total_usuarios BIGINT,
    total_familias BIGINT,
    alertas_pendientes BIGINT,
    alertas_criticas BIGINT,
    microservicios_activos BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM usuarios WHERE rol_id != (SELECT id FROM roles WHERE nombre = 'superadmin')) as total_usuarios,
        (SELECT COUNT(*) FROM familias) as total_familias,
        (SELECT COUNT(*) FROM alertas WHERE atendida = false) as alertas_pendientes,
        (SELECT COUNT(*) FROM alertas WHERE atendida = false AND nivel IN ('alto', 'critico')) as alertas_criticas,
        4::BIGINT as microservicios_activos;
END;
$$ LANGUAGE plpgsql;

-- 3. Obtener usuarios con filtros
CREATE OR REPLACE FUNCTION sp_get_usuarios(
    p_limite INT DEFAULT 50,
    p_offset INT DEFAULT 0,
    p_rol_id INT DEFAULT NULL,
    p_familia_id INT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    nombre VARCHAR(100),
    email VARCHAR(150),
    rol_nombre VARCHAR(50),
    familia_nombre VARCHAR(100),
    relacion VARCHAR(50),
    es_admin_familia BOOLEAN,
    ultima_actualizacion TIMESTAMP,
    fecha_creacion TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id, u.nombre, u.email, r.nombre as rol_nombre,
        COALESCE(f.nombre_familia, 'Sin familia') as familia_nombre,
        NULL::VARCHAR(50) as relacion, NULL::BOOLEAN as es_admin_familia,
        u.ultima_actualizacion, u.fecha_creacion
    FROM usuarios u
    JOIN roles r ON u.rol_id = r.id
    LEFT JOIN familias f ON u.familia_id = f.id
    WHERE 
        (p_rol_id IS NULL OR u.rol_id = p_rol_id) AND
        (p_familia_id IS NULL OR u.familia_id = p_familia_id) AND
        (u.rol_id != 1)
    ORDER BY u.fecha_creacion DESC
    LIMIT p_limite OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 4. Crear alerta
CREATE OR REPLACE FUNCTION sp_create_alerta(
    p_usuario_id INT,
    p_tipo VARCHAR(50),
    p_descripcion TEXT,
    p_nivel VARCHAR(20)
)
RETURNS TABLE (
    alerta_id INT,
    fecha TIMESTAMP
) AS $$
BEGIN
    INSERT INTO alertas (usuario_id, tipo, descripcion, nivel, fecha)
    VALUES (p_usuario_id, p_tipo, p_descripcion, p_nivel, CURRENT_TIMESTAMP)
    RETURNING id, fecha INTO alerta_id, fecha;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- 5. Obtener alertas
CREATE OR REPLACE FUNCTION sp_get_alertas()
RETURNS TABLE (
    id INT,
    usuario_id INT,
    usuario_nombre VARCHAR(100),
    familia_nombre VARCHAR(100),
    tipo VARCHAR(50),
    descripcion TEXT,
    nivel VARCHAR(20),
    fecha TIMESTAMP,
    atendida BOOLEAN,
    fecha_atencion TIMESTAMP,
    atendido_por INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id, a.usuario_id, u.nombre as usuario_nombre, 
        COALESCE(f.nombre_familia, 'Sin familia') as familia_nombre,
        a.tipo, a.descripcion, a.nivel, a.fecha, a.atendida,
        a.fecha_atencion, a.atendido_por
    FROM alertas a
    JOIN usuarios u ON a.usuario_id = u.id
    LEFT JOIN familias f ON u.familia_id = f.id
    ORDER BY a.fecha DESC;
END;
$$ LANGUAGE plpgsql;

-- 6. Atender alerta
CREATE OR REPLACE FUNCTION sp_atender_alerta(
    p_alerta_id INT,
    p_atendido_por INT
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE alertas 
    SET atendida = true, 
        fecha_atencion = CURRENT_TIMESTAMP,
        atendido_por = p_atendido_por
    WHERE id = p_alerta_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 7. Registrar log del sistema
CREATE OR REPLACE FUNCTION registrar_log_sistema(
    p_usuario_id INT,
    p_accion VARCHAR(100),
    p_detalle TEXT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO logs_sistema (usuario_id, accion, detalle, fecha)
    VALUES (p_usuario_id, p_accion, p_detalle, CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

-- 8. Actualizar estado de microservicio
CREATE OR REPLACE FUNCTION actualizar_estado_microservicio(
    p_microservicio_id INT,
    p_estado VARCHAR(20)
)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM microservicios WHERE id = p_microservicio_id) THEN
        RETURN FALSE;
    END IF;
    
    UPDATE microservicios 
    SET estado = p_estado,
        ultima_verificacion = CURRENT_TIMESTAMP
    WHERE id = p_microservicio_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 9. Crear familia
CREATE OR REPLACE FUNCTION sp_create_familia(
    p_nombre_familia VARCHAR(100),
    p_codigo_familia VARCHAR(20) DEFAULT NULL,
    p_descripcion TEXT DEFAULT NULL
)
RETURNS TABLE (
    familia_id INT,
    familia_nombre VARCHAR(100),
    familia_codigo VARCHAR(20),
    familia_fecha_creacion TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    INSERT INTO familias (nombre_familia, codigo_familia, fecha_creacion)
    VALUES (p_nombre_familia, p_codigo_familia, CURRENT_TIMESTAMP)
    RETURNING id, nombre_familia, codigo_familia, fecha_creacion;
END;
$$ LANGUAGE plpgsql;

-- 10. Actualizar familia
CREATE OR REPLACE FUNCTION sp_update_familia(
    p_familia_id INT,
    p_nombre_familia VARCHAR(100) DEFAULT NULL,
    p_codigo_familia VARCHAR(20) DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM familias WHERE id = p_familia_id) THEN
        RETURN FALSE;
    END IF;
    
    UPDATE familias 
    SET 
        nombre_familia = COALESCE(p_nombre_familia, nombre_familia),
        codigo_familia = COALESCE(p_codigo_familia, codigo_familia)
    WHERE id = p_familia_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 11. Obtener familias con estadísticas
CREATE OR REPLACE FUNCTION sp_get_familias(
    p_limite INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id INT,
    nombre_familia VARCHAR(100),
    codigo_familia VARCHAR(20),
    fecha_creacion TIMESTAMP,
    total_miembros BIGINT,
    total_admins BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion,
        COUNT(u.id) as total_miembros,
        COUNT(CASE WHEN u.rol_id = (SELECT r.id FROM roles r WHERE r.nombre = 'admin_familia') THEN 1 END) as total_admins
    FROM familias f
    LEFT JOIN usuarios u ON f.id = u.familia_id
    GROUP BY f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion
    ORDER BY f.fecha_creacion DESC
    LIMIT p_limite OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 12. Obtener estadísticas del dashboard
CREATE OR REPLACE FUNCTION sp_get_dashboard_stats()
RETURNS TABLE (
    total_usuarios BIGINT,
    total_familias BIGINT,
    total_alertas BIGINT,
    alertas_pendientes BIGINT,
    usuarios_activos BIGINT,
    familias_activas BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM usuarios WHERE rol_id != 1) AS total_usuarios,
        (SELECT COUNT(*) FROM familias) AS total_familias,
        (SELECT COUNT(*) FROM alertas) AS total_alertas,
        (SELECT COUNT(*) FROM alertas WHERE atendida = false) AS alertas_pendientes,
        (SELECT COUNT(*) FROM usuarios WHERE rol_id != 1) AS usuarios_activos,
        (SELECT COUNT(*) FROM familias) AS familias_activas;
END;
$$ LANGUAGE plpgsql;

-- 13. Obtener ubicaciones con filtros
CREATE OR REPLACE FUNCTION sp_get_ubicaciones(
    p_limite INT DEFAULT 50,
    p_offset INT DEFAULT 0,
    p_usuario_id INT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    usuario_id INT,
    usuario_nombre VARCHAR(100),
    latitud DECIMAL(9,6),
    longitud DECIMAL(9,6),
    ubicacion_timestamp TIMESTAMP,
    precision_metros INT,
    fuente VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id, u.usuario_id, us.nombre as usuario_nombre,
        u.latitud, u.longitud, u.timestamp as ubicacion_timestamp,
        u.precision_metros, u.fuente
    FROM ubicaciones u
    JOIN usuarios us ON u.usuario_id = us.id
    WHERE (p_usuario_id IS NULL OR u.usuario_id = p_usuario_id)
    ORDER BY u.timestamp DESC
    LIMIT p_limite OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 14. Obtener ubicaciones de un usuario específico
CREATE OR REPLACE FUNCTION sp_get_ubicaciones_usuario(
    p_usuario_id INT,
    p_limite INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id INT,
    usuario_id INT,
    usuario_nombre VARCHAR(100),
    latitud DECIMAL(9,6),
    longitud DECIMAL(9,6),
    ubicacion_timestamp TIMESTAMP,
    precision_metros INT,
    fuente VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id, u.usuario_id, us.nombre as usuario_nombre,
        u.latitud, u.longitud, u.timestamp as ubicacion_timestamp,
        u.precision_metros, u.fuente
    FROM ubicaciones u
    JOIN usuarios us ON u.usuario_id = us.id
    WHERE u.usuario_id = p_usuario_id
    ORDER BY u.timestamp DESC
    LIMIT p_limite OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 15. Obtener logs del sistema con filtros
CREATE OR REPLACE FUNCTION sp_get_logs_sistema(
    p_limite INT DEFAULT 100,
    p_offset INT DEFAULT 0,
    p_usuario_id INT DEFAULT NULL,
    p_accion VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    usuario_id INT,
    usuario_nombre VARCHAR(100),
    accion VARCHAR(100),
    detalle TEXT,
    fecha TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id, l.usuario_id, COALESCE(u.nombre, 'Sistema') as usuario_nombre,
        l.accion, l.detalle, l.fecha
    FROM logs_sistema l
    LEFT JOIN usuarios u ON l.usuario_id = u.id
    WHERE (p_usuario_id IS NULL OR l.usuario_id = p_usuario_id)
      AND (p_accion IS NULL OR l.accion ILIKE '%' || p_accion || '%')
    ORDER BY l.fecha DESC
    LIMIT p_limite OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;




-- Registrar log de creación del superadmin
INSERT INTO logs_sistema (usuario_id, accion, detalle, fecha)
VALUES (1, 'SYSTEM_INIT', '{"message": "Sistema inicializado", "superadmin_created": true}', CURRENT_TIMESTAMP);
