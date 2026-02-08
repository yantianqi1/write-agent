#!/bin/bash
#
# Database Restore Script
#
# This script restores a Write-Agent database from a backup.
#
# Usage:
#   ./restore.sh <backup_file> [output_path]
#
# Example:
#   ./restore.sh backups/write_agent_backup_20240101_020000.db.gz

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file> [output_path]"
    echo ""
    echo "Examples:"
    echo "  $0 backups/write_agent_backup_20240101_020000.db.gz"
    echo "  $0 backups/write_agent_backup_20240101_020000.db.gz /custom/path/db.db"
    echo ""
    echo "Available backups:"
    ls -lh "$PROJECT_ROOT"/backups/write_agent_backup_*.db.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
OUTPUT_PATH="${2:-$PROJECT_ROOT/data/write_agent.db}"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT_PATH")
mkdir -p "$OUTPUT_DIR"

# Create temporary file for extraction
TEMP_FILE=$(mktemp --suffix=.db)
trap "rm -f '$TEMP_FILE'" EXIT

echo "Restoring database..."
echo "Backup: $BACKUP_FILE"
echo "Output: $OUTPUT_PATH"

# Decompress and restore
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
else
    cp "$BACKUP_FILE" "$TEMP_FILE"
fi

# Verify the database integrity
echo "Verifying database integrity..."
if command -v sqlite3 &> /dev/null; then
    if ! sqlite3 "$TEMP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        echo "Error: Database integrity check failed!"
        exit 1
    fi
    echo "Database integrity check passed."

    # Get database info
    TABLES=$(sqlite3 "$TEMP_FILE" ".tables")
    echo "Tables found: $TABLES"
fi

# Stop any running services that might be using the database
# (Uncomment if needed for your setup)
# systemctl stop write-agent

# Backup existing database if it exists
if [ -f "$OUTPUT_PATH" ]; then
    RESTORE_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    echo "Backing up existing database to: ${OUTPUT_PATH}.pre_restore_${RESTORE_TIMESTAMP}"
    cp "$OUTPUT_PATH" "${OUTPUT_PATH}.pre_restore_${RESTORE_TIMESTAMP}"
fi

# Copy restored database to output path
cp "$TEMP_FILE" "$OUTPUT_PATH"

# Set appropriate permissions
chmod 644 "$OUTPUT_PATH"

echo "Restore completed successfully!"
echo "Restored database: $OUTPUT_PATH"
