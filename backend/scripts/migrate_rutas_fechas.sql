-- Migración para añadir campos fecha_inicio, fecha_fin a rutas y fecha_hora_llegada a ruta_paradas

-- Añadir columna 'fecha_inicio' a rutas si no existe
DO $$ BEGIN
    ALTER TABLE rutas ADD COLUMN fecha_inicio TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_inicio" of relation "rutas" already exists, skipping';
END $$;

-- Añadir columna 'fecha_fin' a rutas si no existe
DO $$ BEGIN
    ALTER TABLE rutas ADD COLUMN fecha_fin TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_fin" of relation "rutas" already exists, skipping';
END $$;

-- Añadir columna 'fecha_hora_llegada' a ruta_paradas si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN fecha_hora_llegada TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_hora_llegada" of relation "ruta_paradas" already exists, skipping';
END $$;

