#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="/opt/miamipreviewlab/data/backups"
DB="/opt/miamipreviewlab/data/mpl.db"
TS=$(date +%Y-%m-%d_%H-%M)
mkdir -p "$BACKUP_DIR"
sqlite3 "$DB" ".backup '$BACKUP_DIR/mpl-$TS.db'"
gzip "$BACKUP_DIR/mpl-$TS.db"
# Rotación: mantener últimos 14
ls -1t "$BACKUP_DIR"/mpl-*.db.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "[$(date)] Backup OK: mpl-$TS.db.gz" >> /var/log/mpl/backup.log
