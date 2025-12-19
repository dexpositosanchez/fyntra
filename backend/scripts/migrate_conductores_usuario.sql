-- Migración: Añadir usuario_id a conductores
ALTER TABLE conductores
ADD COLUMN IF NOT EXISTS usuario_id INTEGER UNIQUE REFERENCES usuarios(id) ON DELETE SET NULL;

