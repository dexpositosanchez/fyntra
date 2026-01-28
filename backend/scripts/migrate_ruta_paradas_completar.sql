-- Migración para añadir campos de completado de paradas (foto, firma, fecha_hora_completada)
-- Fecha: 2026-01-27
-- Descripción: Añade campos para almacenar foto, firma y fecha de completado de paradas

-- Añadir columna 'fecha_hora_completada' si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN fecha_hora_completada TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_hora_completada" of relation "ruta_paradas" already exists, skipping';
END $$;

-- Añadir columna 'ruta_foto' si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN ruta_foto VARCHAR(500);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "ruta_foto" of relation "ruta_paradas" already exists, skipping';
END $$;

-- Añadir columna 'ruta_firma' si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN ruta_firma VARCHAR(500);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "ruta_firma" of relation "ruta_paradas" already exists, skipping';
END $$;

-- Comentarios en las columnas para documentación
COMMENT ON COLUMN ruta_paradas.fecha_hora_completada IS 'Fecha y hora real de completado de la parada';
COMMENT ON COLUMN ruta_paradas.ruta_foto IS 'Ruta del archivo de foto de la entrega';
COMMENT ON COLUMN ruta_paradas.ruta_firma IS 'Ruta del archivo de firma del cliente';
