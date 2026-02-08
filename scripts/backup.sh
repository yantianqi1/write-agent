#!/bin/bash
#
# Database Backup Script
#
# This script creates automated backups of the Write-Agent database.
# Backups are retained for 7 days by default.
#
# Usage:
#   ./backup.sh [database_path]
#
# Cron example (daily at 2 AM):
#   0 2 * * * /path/to/scripts/backup.sh /path/to/data/write_agent.db

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
RETENTION_DAYS=${RETENTION_DAYS:-7}
DB_PATH="${1:-$PROJECT_ROOT/data/write_agent.db}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/write_agent_backup_$TIMESTAMP.db"
COMPRESSED_FILE="$BACKUP_FILE.gz"

echo "Starting backup at $(date)"
echo "Database: $DB_PATH"
echo "Backup file: $COMPRESSED_FILE"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

# Create backup using SQLite backup command
if command -v sqlite3 &> /dev/null; then
    echo "Using sqlite3 for backup..."
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
else
    echo "sqlite3 not found, using cp..."
    cp "$DB_PATH" "$BACKUP_FILE"
fi

# Compress the backup
echo "Compressing backup..."
gzip -f "$BACKUP_FILE"

# Get backup size
BACKUP_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
echo "Backup completed: $COMPRESSED_FILE ($BACKUP_SIZE)"

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "write_agent_backup_*.db.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/write_agent_backup_*.db.gz 2>/dev/null || echo "No backups found"

echo "Backup finished at $(date)"
