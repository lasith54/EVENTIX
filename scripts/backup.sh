#!/bin/bash
# scripts/backup.sh
# Database backup script

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="eventix_backup_$TIMESTAMP.sql"

echo "💾 Creating EVENTIX database backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create database backup
docker exec eventix-db pg_dump -U eventix_user -d eventix > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE.gz"

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "eventix_backup_*.sql.gz" -mtime +7 -delete

echo "🧹 Old backups cleaned up"

---