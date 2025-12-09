-- Script de migración para actualizar la tabla vehiculos
-- Cambia de activo (boolean) a estado (enum) y añade nuevos campos

-- 1. Eliminar tipos ENUM si existen (para recrearlos)
DROP TYPE IF EXISTS estadovehiculo CASCADE;
DROP TYPE IF EXISTS tipocombustible CASCADE;

-- 2. Crear tipos ENUM
CREATE TYPE estadovehiculo AS ENUM ('activo', 'en_mantenimiento', 'inactivo');
CREATE TYPE tipocombustible AS ENUM ('gasolina', 'diesel', 'electrico', 'hibrido', 'gas');

-- 3. Añadir nuevas columnas si no existen
ALTER TABLE vehiculos 
    ADD COLUMN IF NOT EXISTS año INTEGER,
    ADD COLUMN IF NOT EXISTS tipo_combustible tipocombustible,
    ADD COLUMN IF NOT EXISTS estado_temp estadovehiculo;

-- 4. Migrar datos de activo a estado
UPDATE vehiculos 
SET estado_temp = CASE 
    WHEN activo = true THEN 'activo'::estadovehiculo
    ELSE 'inactivo'::estadovehiculo
END
WHERE estado_temp IS NULL;

-- 5. Establecer valores por defecto para registros sin estado
UPDATE vehiculos 
SET estado_temp = 'activo'::estadovehiculo
WHERE estado_temp IS NULL;

-- 6. Eliminar columna antigua
ALTER TABLE vehiculos 
    DROP COLUMN IF EXISTS activo;

-- 7. Renombrar la columna temporal a estado
ALTER TABLE vehiculos 
    RENAME COLUMN estado_temp TO estado;

-- 8. Establecer valor por defecto y NOT NULL
ALTER TABLE vehiculos 
    ALTER COLUMN estado SET DEFAULT 'activo'::estadovehiculo,
    ALTER COLUMN estado SET NOT NULL;

