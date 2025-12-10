-- Migración para añadir campos tipo_operacion y direccion a ruta_paradas

-- Añadir columna 'direccion' si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN direccion VARCHAR(300);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "direccion" of relation "ruta_paradas" already exists, skipping';
END $$;

-- Crear tipo ENUM para TipoOperacion
DROP TYPE IF EXISTS TipoOperacion CASCADE;
CREATE TYPE TipoOperacion AS ENUM ('carga', 'descarga');

-- Añadir columna 'tipo_operacion' si no existe
DO $$ BEGIN
    ALTER TABLE ruta_paradas ADD COLUMN tipo_operacion TipoOperacion;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column "tipo_operacion" of relation "ruta_paradas" already exists, skipping';
END $$;

-- Actualizar direcciones existentes desde los pedidos
UPDATE ruta_paradas rp
SET direccion = CASE 
    WHEN rp.tipo_operacion IS NULL OR rp.tipo_operacion = 'carga'::TipoOperacion THEN p.origen
    ELSE p.destino
END,
tipo_operacion = COALESCE(rp.tipo_operacion, 'carga'::TipoOperacion)
FROM pedidos p
WHERE rp.pedido_id = p.id AND rp.direccion IS NULL;

-- Establecer valores por defecto si aún hay NULLs
UPDATE ruta_paradas 
SET direccion = 'Dirección no especificada',
    tipo_operacion = 'carga'::TipoOperacion
WHERE direccion IS NULL OR tipo_operacion IS NULL;

-- Asegurar que las columnas no sean nulas
ALTER TABLE ruta_paradas ALTER COLUMN direccion SET NOT NULL;
ALTER TABLE ruta_paradas ALTER COLUMN tipo_operacion SET NOT NULL;

