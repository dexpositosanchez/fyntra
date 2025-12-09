-- Script de migración para actualizar la tabla conductores
-- Añade campos: apellidos, dni, fecha_caducidad_licencia

-- Añadir nuevas columnas si no existen
ALTER TABLE conductores 
    ADD COLUMN IF NOT EXISTS apellidos VARCHAR(100),
    ADD COLUMN IF NOT EXISTS dni VARCHAR(20),
    ADD COLUMN IF NOT EXISTS fecha_caducidad_licencia DATE;

-- Establecer valores por defecto para fecha_caducidad_licencia (1 año desde hoy)
UPDATE conductores 
SET fecha_caducidad_licencia = CURRENT_DATE + INTERVAL '1 year'
WHERE fecha_caducidad_licencia IS NULL;

-- Hacer fecha_caducidad_licencia NOT NULL después de actualizar los valores
ALTER TABLE conductores 
    ALTER COLUMN fecha_caducidad_licencia SET NOT NULL;

-- Crear índice único para DNI si no existe
CREATE UNIQUE INDEX IF NOT EXISTS ix_conductores_dni ON conductores(dni) WHERE dni IS NOT NULL;

