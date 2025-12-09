-- Script para añadir columna nombre a la tabla vehiculos

-- Añadir columna nombre si no existe
ALTER TABLE vehiculos 
    ADD COLUMN IF NOT EXISTS nombre VARCHAR(100);

-- Establecer valores por defecto para registros existentes
UPDATE vehiculos 
SET nombre = CONCAT('Vehículo ', matricula)
WHERE nombre IS NULL OR nombre = '';

-- Hacer la columna NOT NULL después de actualizar los valores
ALTER TABLE vehiculos 
    ALTER COLUMN nombre SET NOT NULL;

