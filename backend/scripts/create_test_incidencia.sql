-- Script para crear incidencia de prueba con ID 1 para pruebas de carga
-- Este script asegura que siempre exista una incidencia con ID 1

-- Resetear secuencia si es necesario (solo si no existe la incidencia)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM incidencias WHERE id = 1) THEN
        PERFORM setval('incidencias_id_seq', 1, false);
    END IF;
END $$;

-- Crear incidencia con ID 1 (si no existe)
INSERT INTO incidencias (
    id,
    inmueble_id,
    creador_usuario_id,
    titulo,
    descripcion,
    estado,
    prioridad,
    fecha_alta,
    creado_en
)
SELECT 
    1,
    i.id,
    u.id,
    'Incidencia de Prueba para Load Testing',
    'Esta incidencia se crea para pruebas de carga del sistema. Puede ser utilizada para verificar el rendimiento del endpoint GET /api/incidencias/1',
    'ABIERTA'::estadoincidencia,
    'MEDIA'::prioridadincidencia,
    NOW(),
    NOW()
FROM inmuebles i
CROSS JOIN usuarios u
WHERE i.referencia = 'PROP-001' 
  AND u.email = 'admin@fyntra.com'
ON CONFLICT (id) DO NOTHING;

-- Registrar en historial (solo si se creó la incidencia)
INSERT INTO historial_incidencias (
    incidencia_id,
    usuario_id,
    estado_anterior,
    estado_nuevo,
    comentario,
    fecha
)
SELECT 
    1,
    u.id,
    NULL,
    'ABIERTA',
    'Incidencia creada para pruebas de carga',
    NOW()
FROM usuarios u
WHERE u.email = 'admin@fyntra.com'
  AND EXISTS (SELECT 1 FROM incidencias WHERE id = 1)
  AND NOT EXISTS (
      SELECT 1 FROM historial_incidencias 
      WHERE incidencia_id = 1 
        AND comentario = 'Incidencia creada para pruebas de carga'
  );

-- Ajustar secuencia para que las siguientes incidencias tengan IDs incrementales
SELECT setval('incidencias_id_seq', COALESCE((SELECT MAX(id) FROM incidencias), 1));
