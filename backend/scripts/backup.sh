#!/usr/bin/env bash
# Automated PostgreSQL backup. Run via cron: 0 3 * * * /opt/dropify/backend/scripts/backup.sh
set -euo pipefail

BACKUP_DIR="/var/backups/dropify"
DB_CONTAINER="dropify-db-1"
DB_NAME="dropify"
KEEP_DAYS=14

mkdir -p "$BACKUP_DIR"

FILENAME="dropify_$(date +%Y%m%d_%H%M%S).sql.gz"
docker exec "$DB_CONTAINER" pg_dump -U dropify "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"

# Rotate old backups
find "$BACKUP_DIR" -name "dropify_*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "Backup saved: $BACKUP_DIR/$FILENAME"
