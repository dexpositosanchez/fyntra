-- Migración para actualizar la tabla pedidos con los nuevos campos requeridos

-- Eliminar tipo ENUM antiguo si existe y no está en uso
DROP TYPE IF EXISTS EstadoPedido CASCADE;

-- Crear nuevo tipo ENUM con todos los estados
CREATE TYPE EstadoPedido AS ENUM ('pendiente', 'en_ruta', 'entregado', 'incidencia', 'cancelado');

-- Añadir columna 'cliente' si no existe (renombrar de cliente_nombre si existe)
DO $$ 
BEGIN
    -- Si existe cliente_nombre, renombrarlo a cliente
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='pedidos' AND column_name='cliente_nombre') THEN
        ALTER TABLE pedidos RENAME COLUMN cliente_nombre TO cliente;
    -- Si no existe ninguna de las dos, crear cliente
    ELSIF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='pedidos' AND column_name='cliente') THEN
        ALTER TABLE pedidos ADD COLUMN cliente VARCHAR(100);
    END IF;
END $$;

-- Añadir columna 'tipo_mercancia' si no existe
DO $$ BEGIN
    ALTER TABLE pedidos ADD COLUMN tipo_mercancia VARCHAR(100);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "tipo_mercancia" of relation "pedidos" already exists, skipping';
END $$;

-- Añadir columna 'fecha_entrega_deseada' si no existe
DO $$ BEGIN
    ALTER TABLE pedidos ADD COLUMN fecha_entrega_deseada DATE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "fecha_entrega_deseada" of relation "pedidos" already exists, skipping';
END $$;

-- Actualizar columna 'estado' si existe como VARCHAR a ENUM
DO $$
BEGIN
    -- Si la columna estado existe como VARCHAR, necesitamos convertirla
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='pedidos' 
        AND column_name='estado' 
        AND data_type='character varying'
    ) THEN
        -- Crear columna temporal
        ALTER TABLE pedidos ADD COLUMN estado_temp EstadoPedido;
        
        -- Migrar datos
        UPDATE pedidos 
        SET estado_temp = CASE 
            WHEN estado::text = 'pendiente' THEN 'pendiente'::EstadoPedido
            WHEN estado::text = 'en_ruta' THEN 'en_ruta'::EstadoPedido
            WHEN estado::text = 'entregado' THEN 'entregado'::EstadoPedido
            WHEN estado::text = 'incidencia' THEN 'incidencia'::EstadoPedido
            WHEN estado::text = 'cancelado' THEN 'cancelado'::EstadoPedido
            ELSE 'pendiente'::EstadoPedido
        END;
        
        -- Eliminar columna antigua y renombrar la nueva
        ALTER TABLE pedidos DROP COLUMN estado;
        ALTER TABLE pedidos RENAME COLUMN estado_temp TO estado;
        ALTER TABLE pedidos ALTER COLUMN estado SET NOT NULL;
        ALTER TABLE pedidos ALTER COLUMN estado SET DEFAULT 'pendiente'::EstadoPedido;
    -- Si no existe, crearla
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='pedidos' 
        AND column_name='estado'
    ) THEN
        ALTER TABLE pedidos ADD COLUMN estado EstadoPedido NOT NULL DEFAULT 'pendiente'::EstadoPedido;
    END IF;
END $$;

-- Asegurar que las columnas obligatorias no sean nulas
DO $$
BEGIN
    -- Actualizar cliente si es NULL
    UPDATE pedidos SET cliente = 'Cliente Sin Nombre' WHERE cliente IS NULL;
    ALTER TABLE pedidos ALTER COLUMN cliente SET NOT NULL;
    
    -- Actualizar fecha_entrega_deseada si es NULL
    UPDATE pedidos SET fecha_entrega_deseada = CURRENT_DATE + INTERVAL '7 days' WHERE fecha_entrega_deseada IS NULL;
    ALTER TABLE pedidos ALTER COLUMN fecha_entrega_deseada SET NOT NULL;
END $$;

