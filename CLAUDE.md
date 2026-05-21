# Miami Preview Lab — Contexto técnico

## Estado de implementación (actualizado 2026-05-21)

| Bloque | Título | Estado |
|--------|--------|--------|
| 0 | Setup inicial y CLAUDE.md | ✅ Completo |
| 1 | SSH hardening A (users + keys) | ⏭ Salteado (root por ahora) |
| 2 | SSH hardening B (lockdown) | ⏭ Salteado (root por ahora) |
| 3 | API non-root + main.py hardening | ✅ Completo (sin cambio de user) |
| 4 | Git repo + DB backups | ✅ Completo |
| 5 | Schema nuevo (prospects, runs, touchpoints, metrics) | ✅ Completo |
| 6 | API endpoints de prospects | ✅ Completo |
| 7 | Admin UI — vista de Prospects | 🔲 Pendiente — **PRÓXIMO** |
| 8 | Scaffold del agente + budget guard | 🔲 Pendiente |
| 9–17 | Skills, scoring, orchestrator, UI dashboard... | 🔲 Pendiente |

### Para retomar: decile a Claude Code "leé CLAUDE.md y continuamos con el Bloque 7"

Estás trabajando en el VPS de Miami Preview Lab (MPL), una agencia digital part-time que vende web+IA a pequeños negocios del sur de Florida. Idioma de operación: **español**.

## Stack actual (Ubuntu 24.04, IP 74.208.247.168)

- **Caddy** en 80/443 (reverse proxy, TLS automático).
  - `miamipreviewlab.com` y `www.` → estático en `/opt/miamipreviewlab/app/landing/`
  - `admin.miamipreviewlab.com` → reverse proxy a `127.0.0.1:9000`
  - `*.miamipreviewlab.com` → demos en `/opt/miamipreviewlab/demos/{slug}/`, auto-generadas en `/etc/caddy/demos.conf` (importado por Caddyfile)
- **FastAPI/uvicorn** corriendo como `mpl-api.service` en `127.0.0.1:9000`.
- **SQLite** en `/opt/miamipreviewlab/data/mpl.db`.
- **Auth:** JWT HS256, secret persistente en `/opt/miamipreviewlab/data/.jwt_secret`.
- **Admin panel:** archivo único `/opt/miamipreviewlab/app/admin.html` servido desde la raíz `/` por la API.

## Archivos clave

- `/opt/miamipreviewlab/app/main.py` — FastAPI app
- `/opt/miamipreviewlab/app/admin.html` — panel UI single-page
- `/opt/miamipreviewlab/app/mpl-gen-caddy.sh` — regenera demos.conf
- `/opt/miamipreviewlab/app/mpl.sh` — utilidades CLI
- `/opt/miamipreviewlab/.venv/` — venv Python
- `/opt/miamipreviewlab/data/mpl.db` — DB SQLite
- `/opt/miamipreviewlab/data/.jwt_secret`
- `/opt/miamipreviewlab/demos/{slug}/index.html` — demos publicadas
- `/opt/miamipreviewlab/archived/{slug}/` — demos archivadas
- `/opt/miamipreviewlab/backups/{slug}-YYYYMMDD-HHMM/` — backups de demos
- `/etc/systemd/system/mpl-api.service`
- `/etc/caddy/Caddyfile` + `/etc/caddy/demos.conf`

## Modelo de datos actual (DB)

Tabla `demos` (slug PK, business_name, category, status, subdomain, notes, contact_email, contacted_at, followup_at, response, created_at, updated_at).
Tabla `users` (username, password_hash bcrypt).

## Reglas de operación

- **Backups antes de modificar:** `cp X X.bak.$(date +%Y%m%d-%H%M%S)`.
- **Después de tocar systemd:** `systemctl daemon-reload && systemctl restart <service>`.
- **Después de tocar `main.py`:** `systemctl restart mpl-api && journalctl -u mpl-api -n 20 --no-pager`.
- **Después de tocar Caddyfile:** `caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy`.
- **Ante duda, parar y preguntar.** No asumas.
- **No expongas secrets** en logs o en respuestas.

## Convenciones de código

- Python 3.12 (venv en `.venv/`). FastAPI, Pydantic v2, SQLite, `httpx`, `bcrypt`, `PyJWT`.
- Tipado estricto donde sea posible.
- Logging con módulo `logging` (no `print`).
- Subprocess con `subprocess.run` (no `os.system`).
- Slugs validados con regex `^[a-z0-9](-?[a-z0-9])*$`.
