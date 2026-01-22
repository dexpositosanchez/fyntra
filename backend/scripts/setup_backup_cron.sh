#!/bin/bash

# Script para configurar backups automáticos mediante cron
# Ejecuta backups diarios a las 2:00 AM

set -e

CRON_SCHEDULE="0 2 * * *"
SCRIPT_PATH="/app/scripts/backup_postgres.sh"
CRON_LOG="/var/log/backup_cron.log"

# Crear entrada de cron
CRON_JOB="$CRON_SCHEDULE $SCRIPT_PATH >> $CRON_LOG 2>&1"

# Verificar si ya existe la entrada
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "La tarea de backup ya está configurada en cron"
else
    # Agregar la entrada de cron
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✓ Tarea de backup configurada en cron"
    echo "  Horario: $CRON_SCHEDULE (diario a las 2:00 AM)"
    echo "  Log: $CRON_LOG"
fi

# Mostrar el crontab actual
echo ""
echo "Tareas programadas:"
crontab -l
