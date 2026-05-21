#!/bin/bash
# MiamiPreviewLab CLI v0.4
DB="/opt/miamipreviewlab/data/mpl.db"
DEMOS="/opt/miamipreviewlab/demos"
ARCHIVED="/opt/miamipreviewlab/archived"
BACKUPS="/opt/miamipreviewlab/backups"
CONF="/etc/caddy/demos.conf"

init_db() {
  sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS demos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    business_name TEXT,
    category TEXT,
    status TEXT DEFAULT 'draft',
    subdomain TEXT,
    notes TEXT,
    contact_email TEXT,
    contacted_at TEXT,
    followup_at TEXT,
    response TEXT,
    created_at TEXT,
    updated_at TEXT
  );"
}

ts_now() { date -u '+%Y-%m-%d %H:%M:%S'; }

regen_caddy() {
  :> "$CONF"
  local _d _s
  for _d in "$DEMOS"/*/; do
    _s=$(basename "$_d")
    [ ! -f "$_d/index.html" ] && continue
    cat >> "$CONF" << BLOCK
${_s}.miamipreviewlab.com {
    tls internal
    root * /opt/miamipreviewlab/demos/${_s}
    file_server
    encode gzip
}

BLOCK
  done
  caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || systemctl reload caddy
  local _count; _count=$(grep -c 'miamipreviewlab.com' "$CONF" 2>/dev/null || echo 0)
  echo "🔧 Caddy reloaded (${_count} demos)"
}

cmd_create() {
  local _slug="$1" _name="$2" _category="${3:-}"
  [ -z "$_slug" ] || [ -z "$_name" ] && { echo "Uso: mpl create <slug> <nombre> [cat]"; return 1; }
  mkdir -p "$DEMOS/$_slug"
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "INSERT INTO demos (slug, business_name, category, subdomain, created_at, updated_at) VALUES ('$_slug', '$_name', '$_category', '$_slug.miamipreviewlab.com', '$_ts', '$_ts');"
  echo "✅ Demo '$_slug' creada"
  echo "   https://$_slug.miamipreviewlab.com"
}

cmd_publish() {
  local _slug="$1"
  [ ! -d "$DEMOS/$_slug" ] && { echo "❌ Demo '$_slug' no existe"; return 1; }
  [ ! -f "$DEMOS/$_slug/index.html" ] && { echo "❌ No hay index.html"; return 1; }
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET status='published', updated_at='$_ts' WHERE slug='$_slug';"
  regen_caddy
}

cmd_archive() {
  local _slug="$1"
  [ ! -d "$DEMOS/$_slug" ] && { echo "❌ Demo '$_slug' no existe"; return 1; }
  mkdir -p "$BACKUPS/$_slug-$(date +%Y%m%d-%H%M)"
  cp -r "$DEMOS/$_slug/"* "$BACKUPS/$_slug-$(date +%Y%m%d-%H%M)/" 2>/dev/null
  mv "$DEMOS/$_slug" "$ARCHIVED/$_slug"
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET status='archived', updated_at='$_ts' WHERE slug='$_slug';"
  regen_caddy
  echo "📦 '$_slug' archivada"
}

cmd_restore() {
  local _slug="$1"
  [ ! -d "$ARCHIVED/$_slug" ] && { echo "❌ '$_slug' no está archivada"; return 1; }
  mv "$ARCHIVED/$_slug" "$DEMOS/$_slug"
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET status='draft', updated_at='$_ts' WHERE slug='$_slug';"
  regen_caddy
  echo "🔄 '$_slug' restaurada"
}

cmd_list() {
  init_db
  echo "🌴 MiamiPreviewLab Demos"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  sqlite3 -column -header "$DB" "SELECT id, slug, business_name, status, category FROM demos ORDER BY updated_at DESC;" 2>/dev/null
  echo ""
  echo "📂 Active: $(ls -1 "$DEMOS" 2>/dev/null | wc -l)  📦 Archived: $(ls -1 "$ARCHIVED" 2>/dev/null | wc -l)"
}

cmd_note() {
  local _slug="$1"; shift; local _note="$*"
  [ -z "$_slug" ] && { echo "Uso: mpl note <slug> <texto>"; return 1; }
  init_db
  local _existing; _existing=$(sqlite3 "$DB" "SELECT notes FROM demos WHERE slug='$_slug';")
  local _newnote="${_existing:+$_existing
}$(date +%Y-%m-%d): $_note"
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET notes='$_newnote', updated_at='$_ts' WHERE slug='$_slug';"
  echo "📝 Nota agregada a '$_slug'"
}

cmd_contacted() {
  local _slug="$1"
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET status='contacted', contacted_at='$_ts', updated_at='$_ts' WHERE slug='$_slug';"
  echo "📧 '$_slug' contactado"
}

cmd_responded() {
  local _slug="$1" _response="$2"
  init_db
  local _ts; _ts=$(ts_now)
  sqlite3 "$DB" "UPDATE demos SET status='responded', response='$_response', updated_at='$_ts' WHERE slug='$_slug';"
  echo "✅ '$_slug' respondido: $_response"
}

cmd_delete() {
  local _slug="$1"
  [ -z "$_slug" ] && { echo "Uso: mpl delete <slug>"; return 1; }
  rm -rf "$DEMOS/$_slug" "$ARCHIVED/$_slug"
  init_db
  sqlite3 "$DB" "DELETE FROM demos WHERE slug='$_slug';"
  regen_caddy
  echo "🗑️ '$_slug' eliminada"
}

cmd_info() {
  local _slug="$1"
  init_db
  sqlite3 -column -header "$DB" "SELECT * FROM demos WHERE slug='$_slug';"
  echo "📁 Files: $(ls -1 "$DEMOS/$_slug" 2>/dev/null | wc -l)"
}

case "${1:-}" in
  create)   shift; cmd_create "$@" ;;
  publish)  cmd_publish "$2" ;;
  archive)  cmd_archive "$2" ;;
  restore)  cmd_restore "$2" ;;
  list|ls)  cmd_list ;;
  note)     shift; cmd_note "$@" ;;
  contacted) cmd_contacted "$2" ;;
  responded) cmd_responded "$2" "$3" ;;
  delete)   cmd_delete "$2" ;;
  info)     cmd_info "$2" ;;
  reload)   regen_caddy ;;
  *)
    echo "🌴 MiamiPreviewLab CLI v0.4"
    echo "  create <slug> <nombre> [cat]  - Crear demo"
    echo "  publish <slug>                - Publicar demo"
    echo "  archive <slug>                - Archivar demo"
    echo "  restore <slug>                - Restaurar demo"
    echo "  list                          - Listar todas"
    echo "  info <slug>                   - Detalles"
    echo "  note <slug> <texto>           - Agregar nota"
    echo "  contacted <slug>              - Marcar contactado"
    echo "  responded <slug> <resp>       - Registrar respuesta"
    echo "  delete <slug>                 - Eliminar demo"
    echo "  reload                        - Regenerar config Caddy"
    ;;
esac
