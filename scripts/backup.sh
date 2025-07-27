#!/bin/bash

# Digital Store Bot - Backup Script
# Usage: ./scripts/backup.sh [--retention-days=7]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days=*)
            RETENTION_DAYS="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--retention-days=7]"
            exit 1
            ;;
    esac
done

echo "💾 Creating backup..."

cd "$PROJECT_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
if [ -f data/store.db ]; then
    echo "🗄️  Backing up database..."
    
    # Use SQLite backup command for consistency
    if command -v sqlite3 &> /dev/null; then
        sqlite3 data/store.db ".backup $BACKUP_DIR/store_backup_$TIMESTAMP.db"
    else
        cp data/store.db "$BACKUP_DIR/store_backup_$TIMESTAMP.db"
    fi
    
    echo "✅ Database backed up: store_backup_$TIMESTAMP.db"
else
    echo "⚠️  Database file not found: data/store.db"
fi

# Backup configuration files
echo "⚙️  Backing up configuration..."

if [ -f .env ]; then
    # Remove sensitive data from backup
    grep -v -E "(TOKEN|KEY|SECRET)" .env > "$BACKUP_DIR/.env_backup_$TIMESTAMP" || true
    echo "✅ Configuration backed up (without secrets)"
fi

if [ -f data/products.json ]; then
    cp data/products.json "$BACKUP_DIR/products_backup_$TIMESTAMP.json"
    echo "✅ Products configuration backed up"
fi

# Create compressed archive
echo "📦 Creating compressed archive..."
tar -czf "$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz" \
    -C "$BACKUP_DIR" \
    --exclude="*.tar.gz" \
    . 2>/dev/null || true

# Calculate backup size
if [ -f "$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
fi

# Clean up old backups
echo "🧹 Cleaning up old backups (keeping last $RETENTION_DAYS days)..."

# Remove old database backups
find "$BACKUP_DIR" -name "store_backup_*.db" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Remove old config backups  
find "$BACKUP_DIR" -name ".env_backup_*" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "products_backup_*.json" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Remove old compressed backups
find "$BACKUP_DIR" -name "full_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Show remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*backup_*" -type f | wc -l)
echo "📁 Total backups remaining: $BACKUP_COUNT"

echo "✅ Backup completed successfully!"
echo "📂 Backup location: $BACKUP_DIR"
echo "🕒 Timestamp: $TIMESTAMP"