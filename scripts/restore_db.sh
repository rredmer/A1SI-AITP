#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DB_FILE="$ROOT_DIR/backend/data/a1si_aitp.db"
BACKUP_DIR="$ROOT_DIR/backend/data/backups"
TEMP_DIR=""

cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

usage() {
    echo "Usage: $0 [BACKUP_FILE]"
    echo ""
    echo "Restore the SQLite database from a backup file."
    echo "If no file is specified, the most recent backup is used."
    echo ""
    echo "Supported formats:"
    echo "  .db.gz      Compressed backup"
    echo "  .db.gz.gpg  Encrypted + compressed backup (requires BACKUP_ENCRYPTION_KEY)"
    exit 1
}

# Determine backup file
BACKUP_FILE="${1:-}"

if [ -n "$BACKUP_FILE" ]; then
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "ERROR: Backup file not found: $BACKUP_FILE"
        exit 1
    fi
else
    # Auto-select newest backup
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "ERROR: Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    # Try encrypted first, then compressed
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/a1si_aitp_*.db.gz.gpg 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        BACKUP_FILE=$(ls -t "$BACKUP_DIR"/a1si_aitp_*.db.gz 2>/dev/null | head -1)
    fi

    if [ -z "$BACKUP_FILE" ]; then
        echo "ERROR: No backup files found in $BACKUP_DIR"
        exit 1
    fi

    echo "Auto-selected newest backup: $BACKUP_FILE"
fi

TEMP_DIR=$(mktemp -d)
WORK_FILE="$TEMP_DIR/restore.db"

echo "Restoring from: $BACKUP_FILE"

# Step 1: Decrypt if encrypted
if [[ "$BACKUP_FILE" == *.gpg ]]; then
    if [ -z "${BACKUP_ENCRYPTION_KEY:-}" ]; then
        echo "ERROR: BACKUP_ENCRYPTION_KEY is required to decrypt .gpg backups"
        exit 1
    fi

    # Verify checksum if available
    CHECKSUM_FILE="${BACKUP_FILE}.sha256"
    if [ -f "$CHECKSUM_FILE" ]; then
        echo "Verifying SHA256 checksum..."
        if ! sha256sum -c "$CHECKSUM_FILE" --quiet 2>/dev/null; then
            echo "ERROR: Checksum verification failed!"
            exit 1
        fi
        echo "Checksum verified."
    fi

    echo "Decrypting..."
    DECRYPTED="$TEMP_DIR/backup.db.gz"
    echo "$BACKUP_ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 \
        --decrypt --output "$DECRYPTED" "$BACKUP_FILE"
    COMPRESSED="$DECRYPTED"
elif [[ "$BACKUP_FILE" == *.gz ]]; then
    COMPRESSED="$BACKUP_FILE"
else
    echo "ERROR: Unsupported file format. Expected .db.gz or .db.gz.gpg"
    exit 1
fi

# Step 2: Decompress
echo "Decompressing..."
gunzip -c "$COMPRESSED" > "$WORK_FILE"

# Step 3: Verify SQLite integrity
echo "Verifying database integrity..."
INTEGRITY=$(sqlite3 "$WORK_FILE" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    echo "ERROR: Database integrity check failed: $INTEGRITY"
    exit 1
fi
echo "Integrity check passed."

# Step 4: Back up current database as safety net
if [ -f "$DB_FILE" ]; then
    PRE_RESTORE="${DB_FILE}.pre-restore"
    echo "Saving current database to $PRE_RESTORE"
    cp "$DB_FILE" "$PRE_RESTORE"
    # Also remove WAL/SHM files if present
    rm -f "${DB_FILE}-wal" "${DB_FILE}-shm"
fi

# Step 5: Restore
echo "Restoring database..."
cp "$WORK_FILE" "$DB_FILE"

echo "Restore complete: $DB_FILE"
echo ""
echo "Next steps:"
echo "  1. Run 'make migrate' to apply any pending migrations"
echo "  2. Verify with 'python backend/manage.py check'"
