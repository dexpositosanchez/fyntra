#!/bin/bash

# Script de backup automático de PostgreSQL
# Este script debe ejecutarse periódicamente mediante cron o tarea programada

set -e

# Configuración
DB_NAME="${POSTGRES_DB:-fyntra}"
DB_USER="${POSTGRES_USER:-fyntra_user}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Generar nombre del archivo de backup con timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/fyntra_backup_$TIMESTAMP.sql.gz"

# Variable de entorno para la contraseña (debe estar configurada)
export PGPASSWORD="${POSTGRES_PASSWORD:-fyntra_password}"

echo "Iniciando backup de la base de datos $DB_NAME..."
echo "Fecha: $(date)"

# Realizar backup comprimido
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --create | gzip > "$BACKUP_FILE"

# Verificar que el backup se creó correctamente
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup completado exitosamente: $BACKUP_FILE"
    echo "  Tamaño: $BACKUP_SIZE"
else
    echo "✗ Error: El archivo de backup no se creó correctamente"
    exit 1
fi

# Eliminar backups antiguos (más de RETENTION_DAYS días)
echo "Eliminando backups antiguos (más de $RETENTION_DAYS días)..."
find "$BACKUP_DIR" -name "fyntra_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "Limpieza completada"

# Listar backups actuales
echo ""
echo "Backups disponibles:"
ls -lh "$BACKUP_DIR"/fyntra_backup_*.sql.gz 2>/dev/null | tail -5 || echo "No hay backups disponibles"

echo ""
echo "Backup finalizado: $(date)"
