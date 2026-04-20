#!/usr/bin/env bash
# =================================================================
# PostgreSQL migration: team1 → team2
# Requires: pg_dump, pg_restore (PostgreSQL 16 client tools)
#
# Install on Ubuntu/Debian:
#   sudo apt install postgresql-client-16
# Install on macOS:
#   brew install postgresql@16
# =================================================================

set -euo pipefail

# --- Source (team1) ---
SRC_HOST="talentika-prod-postgres-do-user-34164274-0.l.db.ondigitalocean.com"
SRC_PORT="25060"
SRC_USER="doadmin"
SRC_DB="defaultdb"
SRC_PASSWORD="AVNS_aWSXsGzTAjrb43tsFRn"

# --- Destination (team2) ---
DST_HOST="talentika-t2-prod-postgres-do-user-36159466-0.h.db.ondigitalocean.com"
DST_PORT="25060"
DST_USER="doadmin"
DST_DB="defaultdb"
DST_PASSWORD="AVNS_4x2KgvawX0e0KFileOW"

DUMP_FILE="/tmp/talentika-migration-$(date +%Y%m%d-%H%M%S).dump"

echo "==> Dumping source database..."
PGPASSWORD="$SRC_PASSWORD" pg_dump \
  --host="$SRC_HOST" \
  --port="$SRC_PORT" \
  --username="$SRC_USER" \
  --dbname="$SRC_DB" \
  --format=custom \
  --no-owner \
  --no-acl \
  --file="$DUMP_FILE"

echo "==> Dump complete: $DUMP_FILE"
echo "==> Restoring to destination database..."

PGPASSWORD="$DST_PASSWORD" pg_restore \
  --host="$DST_HOST" \
  --port="$DST_PORT" \
  --username="$DST_USER" \
  --dbname="$DST_DB" \
  --no-owner \
  --no-acl \
  --clean \
  --if-exists \
  "$DUMP_FILE"

echo "==> Migration complete."
echo "==> Dump file kept at: $DUMP_FILE"
echo "    Remove with: rm $DUMP_FILE"
