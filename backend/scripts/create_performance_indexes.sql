-- Script para crear índices de rendimiento en tablas críticas
-- Estos índices mejoran significativamente el tiempo de respuesta de consultas frecuentes
-- según el RNF1: tiempo de respuesta < 2 segundos con 100 usuarios concurrentes

-- Índices para la tabla INCIDENCIAS
-- Consultas frecuentes: filtrar por estado y prioridad
CREATE INDEX IF NOT EXISTS idx_incidencias_estado_prioridad 
    ON incidencias(estado, prioridad);

-- Consultas frecuentes: filtrar por inmueble_id (para propietarios)
CREATE INDEX IF NOT EXISTS idx_incidencias_inmueble_id 
    ON incidencias(inmueble_id);

-- Consultas frecuentes: filtrar por proveedor_id (para proveedores)
CREATE INDEX IF NOT EXISTS idx_incidencias_proveedor_id 
    ON incidencias(proveedor_id);

-- Consultas frecuentes: ordenar por fecha_alta descendente
CREATE INDEX IF NOT EXISTS idx_incidencias_fecha_alta_desc 
    ON incidencias(fecha_alta DESC);

-- Índices para la tabla RUTAS
-- Consultas frecuentes: filtrar por fecha y estado
CREATE INDEX IF NOT EXISTS idx_rutas_fecha_estado 
    ON rutas(fecha, estado);

-- Consultas frecuentes: filtrar por conductor_id
CREATE INDEX IF NOT EXISTS idx_rutas_conductor_id 
    ON rutas(conductor_id);

-- Consultas frecuentes: filtrar por vehiculo_id
CREATE INDEX IF NOT EXISTS idx_rutas_vehiculo_id 
    ON rutas(vehiculo_id);

-- Consultas frecuentes: ordenar por fecha descendente
CREATE INDEX IF NOT EXISTS idx_rutas_fecha_desc 
    ON rutas(fecha DESC);

-- Índices para la tabla PEDIDOS
-- Consultas frecuentes: filtrar por estado y fecha de creación
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_creado_en 
    ON pedidos(estado, creado_en);

-- Consultas frecuentes: ordenar por fecha de creación descendente
CREATE INDEX IF NOT EXISTS idx_pedidos_creado_en_desc 
    ON pedidos(creado_en DESC);

-- Índices para la tabla USUARIOS
-- Consultas frecuentes: autenticación por email (ya debería existir como UNIQUE, pero asegurar índice)
CREATE INDEX IF NOT EXISTS idx_usuarios_email 
    ON usuarios(email);

-- Consultas frecuentes: filtrar por rol y activo
CREATE INDEX IF NOT EXISTS idx_usuarios_rol_activo 
    ON usuarios(rol, activo);

-- Índices para la tabla VEHICULOS
-- Consultas frecuentes: filtrar por estado
CREATE INDEX IF NOT EXISTS idx_vehiculos_estado 
    ON vehiculos(estado);

-- Consultas frecuentes: búsqueda por matrícula (ya debería ser UNIQUE, pero asegurar índice)
CREATE INDEX IF NOT EXISTS idx_vehiculos_matricula 
    ON vehiculos(matricula);

-- Índices para la tabla CONDUCTORES
-- Consultas frecuentes: filtrar por usuario_id (relación con usuarios)
CREATE INDEX IF NOT EXISTS idx_conductores_usuario_id 
    ON conductores(usuario_id);

-- Índices para la tabla INMUEBLES
-- Consultas frecuentes: filtrar por comunidad_id
CREATE INDEX IF NOT EXISTS idx_inmuebles_comunidad_id 
    ON inmuebles(comunidad_id);

-- Índices para la tabla PROPIETARIOS
-- Consultas frecuentes: filtrar por usuario_id
CREATE INDEX IF NOT EXISTS idx_propietarios_usuario_id 
    ON propietarios(usuario_id);

-- Índices para la tabla RUTA_PARADAS
-- Consultas frecuentes: filtrar por ruta_id y orden
CREATE INDEX IF NOT EXISTS idx_ruta_paradas_ruta_id_orden 
    ON ruta_paradas(ruta_id, orden);

-- Índices para la tabla ACTUACIONES
-- Consultas frecuentes: filtrar por incidencia_id
CREATE INDEX IF NOT EXISTS idx_actuaciones_incidencia_id 
    ON actuaciones(incidencia_id);

-- Índices para la tabla DOCUMENTOS
-- Consultas frecuentes: filtrar por incidencia_id
CREATE INDEX IF NOT EXISTS idx_documentos_incidencia_id 
    ON documentos(incidencia_id);

-- Índices para la tabla MENSAJES
-- Consultas frecuentes: filtrar por incidencia_id y ordenar por fecha
CREATE INDEX IF NOT EXISTS idx_mensajes_incidencia_id_creado_en 
    ON mensajes(incidencia_id, creado_en DESC);

-- Índices para la tabla HISTORIAL_INCIDENCIAS
-- Consultas frecuentes: filtrar por incidencia_id y ordenar por fecha
CREATE INDEX IF NOT EXISTS idx_historial_incidencias_incidencia_id_fecha 
    ON historial_incidencias(incidencia_id, fecha DESC);

-- Comentarios sobre los índices creados
COMMENT ON INDEX idx_incidencias_estado_prioridad IS 'Optimiza consultas de incidencias filtradas por estado y prioridad';
COMMENT ON INDEX idx_rutas_fecha_estado IS 'Optimiza consultas de rutas filtradas por fecha y estado';
COMMENT ON INDEX idx_pedidos_estado_creado_en IS 'Optimiza consultas de pedidos filtrados por estado y fecha de creación';
