#!/bin/bash
# scripts/restore.sh
# Database restore script

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -la ./backups/eventix_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

echo "⚠️  WARNING: This will replace the current database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

echo "🔄 Restoring database from $BACKUP_FILE..."

# Extract backup file
TEMP_FILE="/tmp/eventix_restore.sql"
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

# Stop services
docker-compose stop user-service event-service booking-service payment-service api-gateway

# Restore database
docker exec -i eventix-db psql -U eventix_user -d eventix < "$TEMP_FILE"

# Clean up
rm "$TEMP_FILE"

# Restart services
docker-compose start user-service event-service booking-service payment-service api-gateway

echo "✅ Database restored successfully!"

---