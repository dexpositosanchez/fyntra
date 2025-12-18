-- Migración: Añadir usuario_id a proveedores para RF15
-- Permite que los proveedores tengan acceso al sistema como usuarios

-- Añadir columna usuario_id a proveedores
ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS usuario_id INTEGER UNIQUE REFERENCES usuarios(id);

-- Crear índice para mejorar búsquedas
CREATE INDEX IF NOT EXISTS idx_proveedores_usuario_id ON proveedores(usuario_id);

