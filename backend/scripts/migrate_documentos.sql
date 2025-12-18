-- Migración: Actualizar tabla documentos para RF16
-- Añade campos necesarios para gestión de documentos

-- Añadir columna usuario_id si no existe
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);

-- Renombrar columnas si es necesario (depende del estado actual)
-- ALTER TABLE documentos RENAME COLUMN url TO ruta_archivo;
-- ALTER TABLE documentos RENAME COLUMN nombre_archivo TO nombre;

-- Añadir nuevas columnas
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS nombre VARCHAR(200);
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS tipo_archivo VARCHAR(100);
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS ruta_archivo VARCHAR(500);
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS tamaño INTEGER;

-- Crear directorio de uploads (esto se hace desde el código)

