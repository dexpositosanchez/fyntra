-- Migración para actualizar la tabla mantenimientos con los nuevos campos

-- Eliminar tipos ENUM antiguos si existen
DROP TYPE IF EXISTS TipoMantenimiento CASCADE;
DROP TYPE IF EXISTS EstadoMantenimiento CASCADE;

-- Crear nuevos tipos ENUM
CREATE TYPE TipoMantenimiento AS ENUM ('preventivo', 'correctivo', 'revision', 'itv', 'cambio_aceite');
CREATE TYPE EstadoMantenimiento AS ENUM ('programado', 'en_curso', 'completado', 'vencido', 'cancelado');

-- Añadir nuevas columnas si no existen
DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN descripcion VARCHAR(200);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "descripcion" already exists, skipping';
END $$;

DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN fecha_inicio TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_inicio" already exists, skipping';
END $$;

DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN fecha_fin TIMESTAMP WITH TIME ZONE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_fin" already exists, skipping';
END $$;

DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN estado EstadoMantenimiento;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "estado" already exists, skipping';
END $$;

DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN kilometraje INTEGER;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "kilometraje" already exists, skipping';
END $$;

DO $$ BEGIN
    ALTER TABLE mantenimientos ADD COLUMN proveedor VARCHAR(100);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "proveedor" already exists, skipping';
END $$;

-- Actualizar el tipo de la columna tipo si existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mantenimientos' AND column_name='tipo') THEN
        ALTER TABLE mantenimientos ALTER COLUMN tipo TYPE TipoMantenimiento USING tipo::text::TipoMantenimiento;
    ELSE
        ALTER TABLE mantenimientos ADD COLUMN tipo TipoMantenimiento NOT NULL;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error updating tipo column: %', SQLERRM;
END $$;

-- Actualizar el tipo de la columna coste si existe (de String a Float)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mantenimientos' AND column_name='coste') THEN
        -- Si coste es VARCHAR, intentar convertir a FLOAT
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='mantenimientos' 
            AND column_name='coste' 
            AND data_type='character varying'
        ) THEN
            ALTER TABLE mantenimientos ALTER COLUMN coste TYPE FLOAT USING NULLIF(coste, '')::FLOAT;
        END IF;
    ELSE
        ALTER TABLE mantenimientos ADD COLUMN coste FLOAT;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error updating coste column: %', SQLERRM;
END $$;

-- Renombrar fecha_real a fecha_fin si existe y fecha_fin no existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mantenimientos' AND column_name='fecha_real')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mantenimientos' AND column_name='fecha_fin') THEN
        ALTER TABLE mantenimientos RENAME COLUMN fecha_real TO fecha_fin;
    END IF;
END $$;

-- Establecer valores por defecto
UPDATE mantenimientos SET estado = 'programado'::EstadoMantenimiento WHERE estado IS NULL;

-- Asegurar que las columnas obligatorias no sean nulas
ALTER TABLE mantenimientos ALTER COLUMN tipo SET NOT NULL;
ALTER TABLE mantenimientos ALTER COLUMN fecha_programada SET NOT NULL;
ALTER TABLE mantenimientos ALTER COLUMN estado SET NOT NULL DEFAULT 'programado'::EstadoMantenimiento;

-- Crear índices si no existen
CREATE INDEX IF NOT EXISTS idx_mantenimientos_vehiculo_id ON mantenimientos(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_mantenimientos_fecha_programada ON mantenimientos(fecha_programada);
CREATE INDEX IF NOT EXISTS idx_mantenimientos_estado ON mantenimientos(estado);

