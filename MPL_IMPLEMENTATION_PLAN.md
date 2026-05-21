# Plan de Implementación — Miami Preview Lab (MPL)

> **Versión:** 1.0 — mayo 2026
> **Audiencia:** sesiones de Claude Code ejecutadas en el VPS (74.208.247.168, Ubuntu 24.04).
> **Objetivo del documento:** dejar a un agente de research diario funcionando, integrado al panel admin existente, entregando "kits de contexto" descargables para que el dueño los use para generar demos localmente.

---

## Cómo usar este documento

1. Conectate al VPS por SSH y abrí Claude Code (`claude`) en el directorio `/opt/miamipreviewlab`.
2. Los bloques son **secuenciales**. No saltes ninguno — cada uno asume que los anteriores se completaron.
3. Para cada bloque:
   - Leé la sección **Pre-requisitos** y **Objetivo**.
   - Copiá el contenido de la sección **🟦 PROMPT PARA CLAUDE CODE** (todo lo que está entre las líneas `===PROMPT START===` y `===PROMPT END===`).
   - Pegalo en una sesión nueva de Claude Code.
   - Esperá a que termine y corré los comandos de **Validación**.
   - Si la validación pasa, marcá el bloque como hecho y seguí con el siguiente.
4. Si una validación falla, NO sigas adelante. Resolvé el problema (puede ser que pidas a Claude Code que diagnostique) antes de pasar al siguiente bloque.
5. Cada bloque está pensado para ~2–3h de trabajo part-time.

---

## ⚠️ Reglas globales (aplican a TODOS los bloques)

- **Idioma:** todo en español.
- **Backups antes de tocar:** antes de modificar `main.py`, systemd units, Caddyfile o la DB → `cp ARCHIVO ARCHIVO.bak.$(date +%Y%m%d-%H%M%S)`.
- **Después de cambiar systemd:** `systemctl daemon-reload && systemctl restart <service>`.
- **Después de cambiar `main.py`:** `systemctl restart mpl-api && systemctl status mpl-api`.
- **Después de cambiar Caddyfile:** `caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy`.
- **Verificar antes de continuar:** cada bloque define `Validación`. No la saltes.
- **Ante duda, parar:** si Claude Code no está seguro de algo crítico (paths, permisos, schema), debe parar y preguntarle al usuario antes de ejecutar.

---

## 🟩 PROMPT BASE — pegar como CLAUDE.md en `/opt/miamipreviewlab/CLAUDE.md`

Antes de empezar con los bloques, creá este archivo en el VPS. Claude Code lo leerá automáticamente en cada sesión y tendrá el contexto del proyecto siempre disponible.

===PROMPT BASE START===

# Miami Preview Lab — Contexto técnico

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

===PROMPT BASE END===

---

# Índice de bloques

| # | Título | Tiempo | Riesgo |
|---|---|---|---|
| 0 | Setup inicial y CLAUDE.md | 30min | Bajo |
| 1 | SSH hardening A (users + keys) | 1h | **Alto** ⚠️ |
| 2 | SSH hardening B (lockdown) | 30min | **Alto** ⚠️ |
| 3 | API non-root + main.py hardening | 2h | Medio |
| 4 | Git repo + DB backups | 1h | Bajo |
| 5 | Schema nuevo (prospects, runs, touchpoints) | 1.5h | Bajo |
| 6 | API endpoints de prospects | 2h | Bajo |
| 7 | Admin UI — vista de Prospects | 2.5h | Bajo |
| 8 | Scaffold del agente + budget guard | 1.5h | Bajo |
| 9 | Discovery skills (gmaps + yelp + Apify) | 2.5h | Medio |
| 10 | Enrichment nivel 1 | 2.5h | Medio |
| 11 | Enrichment nivel 2 — sitio web | 2h | Medio |
| 12 | Enrichment nivel 2 — Instagram (Apify) | 1.5h | Bajo |
| 13 | Scoring con YAML + Haiku | 2h | Medio |
| 14 | Briefing.json + README.md (Haiku) | 1.5h | Bajo |
| 15 | Orchestrator + systemd timer | 2h | Medio |
| 16 | Zip endpoints + Admin UI Dashboard | 2.5h | Bajo |
| 17 | Tests E2E + Handbook + 2do vertical | 2h | Bajo |

---

# Bloque 0 — Setup inicial y creación de CLAUDE.md

**Pre-requisitos:** ninguno. Sesión inicial.
**Objetivo:** dejar `CLAUDE.md` instalado, verificar que el ambiente está sano, snapshotear el estado actual.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Sos asistente técnico en el VPS de Miami Preview Lab. Te paso un plan de implementación en bloques; éste es el Bloque 0 (setup inicial).

**Antes que nada:**
1. Verificá el directorio actual con `pwd`. Si no estás en `/opt/miamipreviewlab`, hacé `cd /opt/miamipreviewlab`.
2. Verificá que tenés acceso de escritura ahí.

**Tareas:**

1. **Crear `/opt/miamipreviewlab/CLAUDE.md`** con el contenido exacto del "PROMPT BASE" del plan (te lo voy a pasar yo, copiá el bloque entre `===PROMPT BASE START===` y `===PROMPT BASE END===`). Si te falta el contenido, pedímelo.

2. **Snapshot del estado actual.** Creá `/opt/miamipreviewlab/PRE_AGENT_SNAPSHOT.md` con:
   - Output de `systemctl status mpl-api --no-pager | head -20`
   - Output de `systemctl status caddy --no-pager | head -20`
   - Output de `ss -tlnp | head -20`
   - Output de `df -h /`
   - Output de `du -sh /opt/miamipreviewlab/*`
   - Output de `sqlite3 /opt/miamipreviewlab/data/mpl.db ".schema"`
   - Output de `sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT slug, business_name, category, status FROM demos"`
   - Output de `cat /etc/caddy/Caddyfile`
   - Output de `cat /etc/caddy/demos.conf`
   - Output de `cat /etc/systemd/system/mpl-api.service`
   - Output de `ls -la /opt/miamipreviewlab/`
   - Listado de archivos: `find /opt/miamipreviewlab -maxdepth 3 -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/__pycache__/*"`

3. **Crear estructura de directorios reservada para el agente** (vacía por ahora, se va a poblar en bloques futuros):
   ```
   /opt/miamipreviewlab/agent/
   /opt/miamipreviewlab/agent/skills/
   /opt/miamipreviewlab/agent/scoring/
   /opt/miamipreviewlab/agent/config/
   /opt/miamipreviewlab/data/context/
   /opt/miamipreviewlab/data/backups/
   /var/log/mpl/
   ```

4. **No instales nada todavía.** No toques systemd, sshd, ni la DB. Solo lectura + crear carpetas vacías + archivos `CLAUDE.md` y `PRE_AGENT_SNAPSHOT.md`.

5. **Reportá:** un resumen de 5–10 líneas con lo que encontraste, y si hay algo inesperado (ej: archivos que no esperabas, servicios caídos, disco lleno).

===PROMPT END===

### Validación post-bloque

```bash
ls -la /opt/miamipreviewlab/CLAUDE.md /opt/miamipreviewlab/PRE_AGENT_SNAPSHOT.md
ls -la /opt/miamipreviewlab/agent/
ls -la /opt/miamipreviewlab/data/context /opt/miamipreviewlab/data/backups /var/log/mpl
```

Debe haber: `CLAUDE.md` (no vacío), `PRE_AGENT_SNAPSHOT.md` (con todos los outputs), 4 carpetas vacías bajo `agent/`, `data/context/` y `data/backups/`, y `/var/log/mpl`.

---

# Bloque 1 — SSH hardening Parte A (usuarios + llaves)

**Pre-requisitos:** Bloque 0.
**Objetivo:** crear usuario `mpl` con sudo, copiar llaves SSH desde tu máquina local, verificar que el login por llave funciona. **No** desactivar todavía el login por contraseña — eso es Bloque 2.

⚠️ **MANTENÉ DOS SESIONES SSH ABIERTAS** durante este bloque. Una como `root` (la que ya funciona, no la cierres). La segunda la usás para verificar que `mpl` puede entrar. Solo cuando confirmes, podés cerrar root.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 1: SSH hardening parte A (preparar usuario y llaves, sin desactivar contraseña todavía).

**Antes de empezar, confirmame:**
- ¿Tenés ya generada una llave SSH en tu máquina local (WSL)? Si no, te paso comando para generarla.
- ¿Necesitamos sumar también la llave pública de un segundo usuario (tu amigo)? Si sí, pedímela también.

**Tareas en el VPS:**

1. **Crear usuario `mpl`:**
   ```bash
   adduser --disabled-password --gecos "" mpl
   usermod -aG sudo mpl
   echo "mpl ALL=(ALL) NOPASSWD: /bin/systemctl restart mpl-api, /bin/systemctl reload caddy, /usr/bin/caddy reload --config /etc/caddy/Caddyfile" > /etc/sudoers.d/mpl
   chmod 440 /etc/sudoers.d/mpl
   visudo -c -f /etc/sudoers.d/mpl  # validar
   ```

2. **Preparar `.ssh`:**
   ```bash
   sudo -u mpl mkdir -p /home/mpl/.ssh
   sudo -u mpl touch /home/mpl/.ssh/authorized_keys
   chmod 700 /home/mpl/.ssh
   chmod 600 /home/mpl/.ssh/authorized_keys
   chown -R mpl:mpl /home/mpl/.ssh
   ```

3. **Sumar la llave pública del usuario** al archivo `/home/mpl/.ssh/authorized_keys`. El usuario te la va a pegar como string. Validá que tenga formato `ssh-ed25519 AAAA... comentario` o `ssh-rsa AAAA... comentario`. Si tiene caracteres extraños, parate y preguntale.

4. **Verificación local (desde el VPS, sin tocar SSH config):**
   ```bash
   sudo -u mpl bash -c 'cat /home/mpl/.ssh/authorized_keys'
   ls -la /home/mpl/.ssh/
   id mpl
   sudo -l -U mpl
   ```

5. **Decile al usuario que abra OTRA terminal en su máquina local** y pruebe:
   ```
   ssh mpl@74.208.247.168
   ```
   Debería entrar **sin pedir contraseña** (usando la llave). Si pide contraseña, la llave no está bien — pará, no sigas con el Bloque 2.

6. **Una vez confirmado**, NO hagas cambios a `sshd_config`. Eso es Bloque 2.

7. **Cambios de ownership de archivos del proyecto:** todavía no. Lo dejamos para el Bloque 3 que es cuando convertimos la API a non-root. Por ahora `/opt/miamipreviewlab` sigue siendo de root.

**No olvides:**
- Si el usuario ya tiene una llave SSH en `~/.ssh/id_ed25519`, no la sobreescribas. Solo agregar la pública al `authorized_keys` del VPS.
- Si el usuario tiene `ssh-copy-id` en su WSL, también puede usar eso desde su máquina:
  `ssh-copy-id mpl@74.208.247.168` (le va a pedir la contraseña de `mpl`, que no tiene → mejor pegamos la llave manual).

**Reportá:** confirmación de que `mpl` existe, sudo limitado configurado, llave instalada, y output de `sudo -u mpl whoami` + `sudo -l -U mpl`.

===PROMPT END===

### Validación post-bloque

**Desde tu máquina local (WSL), en una terminal NUEVA:**

```bash
ssh mpl@74.208.247.168
# Debería entrar sin contraseña
whoami        # → mpl
sudo -l       # debe listar systemctl y caddy
exit
```

**No cierres la sesión root.** Hasta acá la sesión vieja sigue activa por seguridad.

---

# Bloque 2 — SSH hardening Parte B (lockdown)

**Pre-requisitos:** Bloque 1 completo y validado. Llave SSH funcionando para `mpl`.
**Objetivo:** desactivar login root por SSH y desactivar autenticación por contraseña. Solo llaves de aquí en adelante.

⚠️ **ANTES DE EMPEZAR:** confirmá una última vez desde una terminal nueva que `ssh mpl@74.208.247.168` funciona sin contraseña. Si falla, **no ejecutes este bloque** — volvé al Bloque 1.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 2: lockdown de SSH. Desactivar root login y password auth.

**Pre-check obligatorio:**
- ¿Confirmaste que `ssh mpl@74.208.247.168` funciona con llave desde la máquina local del usuario? **SÍ es obligatorio antes de seguir.** Si no fue verificado, pará y pedile al usuario que lo verifique.
- ¿El usuario tiene otra sesión SSH abierta como root en paralelo? **Idealmente sí**, como red de seguridad.

**Tareas:**

1. **Backup del sshd_config:**
   ```bash
   cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d-%H%M%S)
   ```

2. **Crear archivo drop-in** en `/etc/ssh/sshd_config.d/00-mpl-hardening.conf` con:
   ```
   PermitRootLogin no
   PasswordAuthentication no
   PubkeyAuthentication yes
   ChallengeResponseAuthentication no
   KbdInteractiveAuthentication no
   UsePAM yes
   X11Forwarding no
   AllowUsers mpl
   ClientAliveInterval 300
   ClientAliveCountMax 2
   MaxAuthTries 3
   LoginGraceTime 30
   ```

3. **Validar la config antes de aplicar:**
   ```bash
   sshd -t
   ```
   Si da error, **NO** reinicies SSH. Revisá el error y corregí.

4. **Reiniciar SSH:**
   ```bash
   systemctl restart ssh
   systemctl status ssh --no-pager
   ```

5. **Decile al usuario** que abra una TERCERA terminal y pruebe:
   ```
   ssh mpl@74.208.247.168
   ```
   Debe entrar. Luego:
   ```
   ssh root@74.208.247.168
   ```
   Debe FALLAR con "Permission denied (publickey)". Eso es lo correcto.

6. Si todo OK, decile al usuario que ya puede cerrar la sesión root vieja. Si la verificación falla, decile que use la sesión root vieja para hacer rollback:
   ```bash
   rm /etc/ssh/sshd_config.d/00-mpl-hardening.conf
   systemctl restart ssh
   ```

7. **fail2ban** (opcional pero recomendado):
   ```bash
   apt-get update && apt-get install -y fail2ban
   systemctl enable --now fail2ban
   ```
   Con eso, IPs que fallan auth repetidamente quedan baneadas 10min por default.

**Reportá:** output de `sshd -t`, `systemctl status ssh`, y confirmación de que login root falla (mostrale al usuario el error).

===PROMPT END===

### Validación post-bloque

**Desde tu local WSL:**

```bash
ssh mpl@74.208.247.168  # debe entrar
exit

ssh root@74.208.247.168 2>&1 | grep "Permission denied"
# Debe imprimir: root@74.208.247.168: Permission denied (publickey).
```

**Importante:** a partir de este punto, **olvidate de la contraseña root**. Solo entrás como `mpl` con llave. Para tareas que necesiten root, `sudo` desde `mpl`.

---

# Bloque 3 — API non-root + main.py hardening

**Pre-requisitos:** Bloques 0-2.
**Objetivo:** API corriendo como usuario `mpl` (no root), secrets fuera del systemd unit, slug validado, subprocess en vez de os.system, logging en vez de print, rate limit en login.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 3: hardening de la API. Pasarla a usuario `mpl`, mover secrets a EnvironmentFile, fijar bugs de seguridad en `main.py`.

**Lee `/opt/miamipreviewlab/CLAUDE.md` y `/opt/miamipreviewlab/app/main.py` antes de cambiar nada.**

### Tareas

#### 1. Cambiar ownership

```bash
chown -R mpl:mpl /opt/miamipreviewlab
ls -la /opt/miamipreviewlab/
```

#### 2. Mover secrets a EnvironmentFile

Crear `/opt/miamipreviewlab/data/.env` con:
```
MPL_ADMIN_USER=rey
MPL_ADMIN_PASS=<el usuario te dirá una contraseña fuerte nueva — pedísela>
ANTHROPIC_API_KEY=<placeholder por ahora, se completa en bloque 13>
GOOGLE_PLACES_KEY=<placeholder>
YELP_API_KEY=<placeholder>
APIFY_TOKEN=<placeholder>
MPL_DAILY_BUDGET_USD=1.0
```

```bash
chmod 600 /opt/miamipreviewlab/data/.env
chown mpl:mpl /opt/miamipreviewlab/data/.env
```

#### 3. Editar `/etc/systemd/system/mpl-api.service`

Backup primero. El contenido nuevo:

```ini
[Unit]
Description=MiamiPreviewLab Admin API
After=network.target

[Service]
Type=simple
User=mpl
Group=mpl
WorkingDirectory=/opt/miamipreviewlab
EnvironmentFile=/opt/miamipreviewlab/data/.env
Environment="PATH=/opt/miamipreviewlab/.venv/bin:/usr/bin:/bin"
ExecStart=/opt/miamipreviewlab/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 9000
Restart=always
RestartSec=5

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/miamipreviewlab /var/log/mpl /etc/caddy/demos.conf
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

⚠️ Notá `ReadWritePaths` incluye `/etc/caddy/demos.conf` porque la API lo regenera. Asegurate que ese archivo existe y que `mpl` puede escribirlo:
```bash
touch /etc/caddy/demos.conf
chown mpl:mpl /etc/caddy/demos.conf
chmod 644 /etc/caddy/demos.conf
```

#### 4. Cambiar el reload de Caddy a la API de admin

En `main.py`, función `_regen_caddy()`. Hoy hace `os.system("caddy reload ...")` que no funcionará para `mpl` no-root. Reemplazá por:

```python
import subprocess
def _regen_caddy():
    # ... genera el archivo demos.conf como ya hace ...
    # Para recargar, usá la API local de admin de Caddy (puerto 2019, solo localhost):
    try:
        subprocess.run(
            ["curl", "-sS", "-X", "POST", "http://127.0.0.1:2019/load",
             "-H", "Content-Type: application/json",
             "--data-binary", "@/etc/caddy/json-config.json"],
            check=False, timeout=5,
        )
    except Exception as e:
        logging.warning(f"Caddy reload via admin API failed: {e}")
    # Fallback: pedirle a systemd (mpl tiene sudo NOPASSWD para esto, ver bloque 1)
    subprocess.run(["sudo", "/bin/systemctl", "reload", "caddy"], check=False, timeout=10)
```

**Más simple:** dado que el sudo NOPASSWD ya está, mantenelo solo así:
```python
def _regen_caddy():
    # ... genera demos.conf ...
    subprocess.run(["sudo", "/bin/systemctl", "reload", "caddy"], check=False, timeout=10)
```

#### 5. Otros fixes en `main.py`

- **Slug validation**: en `create_demo` reemplazar la normalización por:
  ```python
  import re
  SLUG_RE = re.compile(r"^[a-z0-9](-?[a-z0-9])*$")
  slug = data.slug.strip().lower().replace(" ", "-")
  if not SLUG_RE.match(slug) or len(slug) > 63:
      raise HTTPException(400, detail="Invalid slug (use a-z, 0-9, hyphen)")
  ```
  Aplicar la misma validación a todos los endpoints que reciben `{slug}` en el path (`get_demo`, `update_demo`, `publish_demo`, `archive_demo`, `restore_demo`, `delete_demo`, `add_note`, `mark_contacted`, `mark_responded`). Hacelo con un dependency reutilizable:
  ```python
  def valid_slug(slug: str) -> str:
      if not SLUG_RE.match(slug) or len(slug) > 63:
          raise HTTPException(400, "Invalid slug")
      return slug
  ```
  Y usalo: `async def get_demo(slug: str = Depends(valid_slug), ...)`.

- **Logging**: agregar al inicio de `main.py`:
  ```python
  import logging
  logging.basicConfig(
      level=os.environ.get("LOG_LEVEL", "INFO"),
      format="%(asctime)s %(levelname)s %(name)s | %(message)s",
      handlers=[
          logging.StreamHandler(),
          logging.FileHandler("/var/log/mpl/api.log"),
      ],
  )
  log = logging.getLogger("mpl.api")
  ```
  Reemplazá los `print()` por `log.info()`.

- **Schema migration (columna `outcome`)**: en `init_db()`, después del `CREATE TABLE IF NOT EXISTS demos`, agregar:
  ```python
  cur = db.execute("PRAGMA table_info(demos)")
  cols = {row[1] for row in cur.fetchall()}
  if "outcome" not in cols:
      db.execute("ALTER TABLE demos ADD COLUMN outcome TEXT")
  ```

- **Rate limit en login**: instalá `slowapi`:
  ```bash
  /opt/miamipreviewlab/.venv/bin/pip install slowapi
  ```
  En `main.py`:
  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from slowapi.errors import RateLimitExceeded
  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
  
  @app.post("/api/auth/login")
  @limiter.limit("10/minute")
  async def login(request: Request, username: str = Form(...), password: str = Form(...)):
      ...
  ```

- **CORS**: como el panel HTML se sirve desde el mismo origin (`admin.miamipreviewlab.com`), no agregues CORS abierto. Si lo querés cerrado, no toques nada.

- **`SECRET` fix**: hoy se genera siempre con `secrets.token_hex(32)` y después se sobrescribe si existe `.jwt_secret`. Reorganizar para que **primero** se intente leer del archivo y solo si no existe se genere:
  ```python
  SECRET_FILE = BASE / "data" / ".jwt_secret"
  if SECRET_FILE.exists():
      SECRET = SECRET_FILE.read_text().strip()
  else:
      SECRET = secrets.token_hex(32)
      SECRET_FILE.write_text(SECRET)
      os.chmod(SECRET_FILE, 0o600)
  ```

#### 6. Aplicar y verificar

```bash
systemctl daemon-reload
systemctl restart mpl-api
sleep 2
systemctl status mpl-api --no-pager
journalctl -u mpl-api -n 30 --no-pager
ss -tlnp | grep 9000
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9000/
# Debe imprimir 200
```

#### 7. Probar login con la contraseña nueva

```bash
curl -sS -X POST http://127.0.0.1:9000/api/auth/login \
  -d "username=rey" -d "password=<NUEVA_PASSWORD>"
# Debe devolver {"access_token": "...", "token_type": "bearer"}
```

#### 8. Probar el rate limit

Mandá 12 logins inválidos seguidos. A partir del 11 debería responder 429.

**Reportá:** confirmación de que el service corre como `mpl` (`ps aux | grep uvicorn`), que el endpoint responde, login funciona, rate limit activo, y mostrale al usuario los warnings que hayas tenido.

===PROMPT END===

### Validación post-bloque

```bash
# El proceso uvicorn corre como mpl
ps -o user,cmd -C uvicorn

# La API responde
curl -sS http://127.0.0.1:9000/ | head -c 200

# El panel admin abre desde el browser
# https://admin.miamipreviewlab.com → muestra el login

# Login con nueva password funciona y devuelve JWT
```

---

# Bloque 4 — Git repo + DB backups

**Pre-requisitos:** Bloques 0-3.
**Objetivo:** versionar el código en Git (push a GitHub privado), backups diarios automáticos de la DB con rotación.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 4: Git + backups.

### Tareas

#### 1. Git init

```bash
cd /opt/miamipreviewlab
git init
```

Crear `.gitignore`:
```
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.DS_Store
data/*.db
data/*.db-journal
data/.jwt_secret
data/.env
data/backups/
data/context/
data/evidence/
archived/
backups/
demos/*/
!demos/.gitkeep
/var/log/mpl/
*.bak.*
*.log
```

```bash
mkdir -p demos && touch demos/.gitkeep
git add .gitignore
git config user.email "ops@miamipreviewlab.com"
git config user.name "MPL Ops"
git add -A
git status
```

Verificá que `data/.env`, `data/.jwt_secret`, `data/mpl.db` NO aparezcan en el staging.

```bash
git commit -m "Initial commit: MPL stack baseline"
```

#### 2. Configurar remoto en GitHub (el usuario debe haber creado el repo privado)

Preguntale al usuario por la URL del repo (formato `git@github.com:USERNAME/miamipreviewlab.git` o `https://github.com/USERNAME/miamipreviewlab.git`).

Si usa HTTPS, va a pedir token. Mejor SSH: el usuario debe generar una llave en el VPS y agregarla como deploy key en GitHub:
```bash
sudo -u mpl ssh-keygen -t ed25519 -f /home/mpl/.ssh/github_deploy -N ""
cat /home/mpl/.ssh/github_deploy.pub
```
El usuario pega esa pública en GitHub → Settings del repo → Deploy keys → Add (con write access).

Configurar SSH para que use esa llave:
```bash
sudo -u mpl tee -a /home/mpl/.ssh/config > /dev/null <<EOF
Host github.com
  HostName github.com
  User git
  IdentityFile /home/mpl/.ssh/github_deploy
  IdentitiesOnly yes
EOF
chmod 600 /home/mpl/.ssh/config
chown mpl:mpl /home/mpl/.ssh/config
```

Probar:
```bash
sudo -u mpl ssh -T git@github.com
# Debe decir: "Hi USERNAME/miamipreviewlab! You've successfully authenticated..."
```

Agregar remoto y push:
```bash
git remote add origin git@github.com:USERNAME/miamipreviewlab.git
git branch -M main
sudo -u mpl git push -u origin main
```

#### 3. Backup automático de la DB

Crear `/opt/miamipreviewlab/scripts/backup_db.sh`:
```bash
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
```

```bash
chmod +x /opt/miamipreviewlab/scripts/backup_db.sh
chown mpl:mpl /opt/miamipreviewlab/scripts/backup_db.sh
mkdir -p /var/log/mpl && chown mpl:mpl /var/log/mpl
```

Probar manual:
```bash
sudo -u mpl /opt/miamipreviewlab/scripts/backup_db.sh
ls -la /opt/miamipreviewlab/data/backups/
```

Crontab para `mpl`:
```bash
sudo -u mpl crontab -l 2>/dev/null > /tmp/mpl_cron || true
echo "30 3 * * * /opt/miamipreviewlab/scripts/backup_db.sh" >> /tmp/mpl_cron
sudo -u mpl crontab /tmp/mpl_cron
sudo -u mpl crontab -l
```

#### 4. Documentar deploy/rollback

Crear `/opt/miamipreviewlab/DEPLOY.md` con:
- Cómo bajar cambios: `cd /opt/miamipreviewlab && sudo -u mpl git pull && sudo systemctl restart mpl-api`
- Cómo restaurar DB: parar API, copiar `.db.gz` deseado, `gunzip`, reemplazar `mpl.db`, arrancar API
- Cómo hacer rollback de código: `git log`, `git reset --hard <commit>`, restart

**Reportá:** confirmación de push exitoso a GitHub, backup manual creado correctamente, crontab listado.

===PROMPT END===

### Validación

```bash
cd /opt/miamipreviewlab && git log --oneline
ls -la data/backups/
sudo -u mpl crontab -l
cat DEPLOY.md
```

---

# Bloque 5 — Schema nuevo (prospects, research_runs, touchpoints, metrics_daily)

**Pre-requisitos:** Bloques 0-4.
**Objetivo:** crear las tablas que el agente necesita. Migración idempotente (puede correr 2 veces sin romper).

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 5: schema upgrade. Sumar tablas `prospects`, `research_runs`, `touchpoints`, `metrics_daily`. Vincular `demos` con `prospects` via FK.

**Lee CLAUDE.md y `main.py` antes.**

### Tareas

#### 1. Crear sistema de migraciones simple

Estructura:
```
/opt/miamipreviewlab/app/migrations/
├── __init__.py
├── runner.py       # corre todas las migraciones en orden
├── 001_init.py     # idempotente — refleja schema existente
└── 002_agent.py    # tablas nuevas
```

`runner.py`:
```python
import sqlite3, importlib, pkgutil
from pathlib import Path

def run_all(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')))")
    applied = {r[0] for r in db.execute("SELECT name FROM schema_migrations").fetchall()}
    mig_pkg = "app.migrations"
    pkg = importlib.import_module(mig_pkg)
    for _, name, _ in sorted(pkgutil.iter_modules(pkg.__path__)):
        if name in ("runner",):
            continue
        if name in applied:
            continue
        mod = importlib.import_module(f"{mig_pkg}.{name}")
        print(f"[migrations] Applying {name}")
        mod.up(db)
        db.execute("INSERT INTO schema_migrations(name) VALUES (?)", (name,))
        db.commit()
    db.close()
```

`001_init.py`:
```python
def up(db):
    # Idempotente: refleja schema existente (no falla si ya está)
    db.execute("""CREATE TABLE IF NOT EXISTS demos (
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
        outcome TEXT,
        created_at TEXT,
        updated_at TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    # Agregar columna outcome si no está
    cols = {r[1] for r in db.execute("PRAGMA table_info(demos)").fetchall()}
    if "outcome" not in cols:
        db.execute("ALTER TABLE demos ADD COLUMN outcome TEXT")
```

`002_agent.py`:
```python
def up(db):
    db.execute("""CREATE TABLE IF NOT EXISTS prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
        source TEXT NOT NULL,
        source_external_id TEXT,
        business_name TEXT NOT NULL,
        vertical TEXT NOT NULL,
        category_detail TEXT,
        address TEXT,
        city TEXT,
        zip TEXT,
        lat REAL,
        lng REAL,
        phone TEXT,
        email TEXT,
        website_url TEXT,
        instagram_handle TEXT,
        facebook_url TEXT,
        google_maps_url TEXT,
        google_rating REAL,
        google_review_count INTEGER,
        yelp_rating REAL,
        yelp_review_count INTEGER,
        has_website INTEGER,
        website_quality_score INTEGER,
        has_online_booking INTEGER,
        has_whatsapp INTEGER,
        mobile_friendly INTEGER,
        https INTEGER,
        last_post_at TEXT,
        evidence_json TEXT,
        opportunity_score INTEGER,
        score_breakdown_json TEXT,
        proposed_value TEXT,
        status TEXT DEFAULT 'discovered',
        notes TEXT,
        assigned_to TEXT,
        context_path TEXT,
        context_level INTEGER DEFAULT 0,
        context_collected_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(source, source_external_id)
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_prospects_score ON prospects(opportunity_score DESC)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_prospects_vertical_score ON prospects(vertical, opportunity_score DESC)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_prospects_discovered ON prospects(discovered_at)")
    
    db.execute("""CREATE TABLE IF NOT EXISTS research_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        vertical TEXT NOT NULL,
        geo TEXT NOT NULL,
        candidates_seen INTEGER DEFAULT 0,
        candidates_kept INTEGER DEFAULT 0,
        new_prospects INTEGER DEFAULT 0,
        updated_prospects INTEGER DEFAULT 0,
        api_cost_usd REAL DEFAULT 0,
        tokens_in INTEGER DEFAULT 0,
        tokens_out INTEGER DEFAULT 0,
        errors_json TEXT,
        status TEXT,
        log_path TEXT
    )""")
    
    db.execute("""CREATE TABLE IF NOT EXISTS touchpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prospect_id INTEGER NOT NULL,
        occurred_at TEXT NOT NULL,
        channel TEXT NOT NULL,
        direction TEXT NOT NULL,
        summary TEXT,
        outcome TEXT,
        next_action TEXT,
        next_action_at TEXT,
        actor TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(prospect_id) REFERENCES prospects(id)
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_touchpoints_prospect ON touchpoints(prospect_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_touchpoints_next ON touchpoints(next_action_at) WHERE next_action_at IS NOT NULL")
    
    db.execute("""CREATE TABLE IF NOT EXISTS metrics_daily (
        day TEXT PRIMARY KEY,
        prospects_new INTEGER DEFAULT 0,
        prospects_shortlisted INTEGER DEFAULT 0,
        demos_built INTEGER DEFAULT 0,
        demos_shown INTEGER DEFAULT 0,
        closes INTEGER DEFAULT 0,
        revenue_usd REAL DEFAULT 0,
        api_spend_usd REAL DEFAULT 0
    )""")
    
    # Link demos → prospects
    cols = {r[1] for r in db.execute("PRAGMA table_info(demos)").fetchall()}
    if "prospect_id" not in cols:
        db.execute("ALTER TABLE demos ADD COLUMN prospect_id INTEGER REFERENCES prospects(id)")
```

#### 2. Llamar al runner desde `main.py`

Cambiar `init_db()` para que use el runner:
```python
def init_db():
    from app.migrations.runner import run_all
    run_all(str(DB_PATH))
```

#### 3. Aplicar

```bash
sudo -u mpl systemctl restart mpl-api
sleep 2
sqlite3 /opt/miamipreviewlab/data/mpl.db ".tables"
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT * FROM schema_migrations"
sqlite3 /opt/miamipreviewlab/data/mpl.db ".schema prospects"
```

Debe haber 6 tablas (`demos`, `users`, `prospects`, `research_runs`, `touchpoints`, `metrics_daily`, `schema_migrations`), y `schema_migrations` debe listar `001_init` y `002_agent`.

#### 4. Probar idempotencia

Reiniciar la API otra vez:
```bash
sudo -u mpl systemctl restart mpl-api
```
No debe haber errores en `journalctl -u mpl-api -n 30 --no-pager` ni filas duplicadas en `schema_migrations`.

#### 5. Commit

```bash
sudo -u mpl git add app/migrations/
sudo -u mpl git commit -m "Add migration runner + agent schema (prospects, runs, touchpoints, metrics)"
sudo -u mpl git push
```

**Reportá:** tablas creadas, contenidos de `schema_migrations`, y confirmación que el segundo restart no aplicó nada nuevo.

===PROMPT END===

### Validación

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db ".tables"
# Esperado: demos metrics_daily prospects research_runs schema_migrations sqlite_sequence touchpoints users

sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT name, applied_at FROM schema_migrations"
# Dos filas: 001_init y 002_agent
```

---

# Bloque 6 — API endpoints de prospects

**Pre-requisitos:** Bloques 0-5.
**Objetivo:** endpoints CRUD + filtros para `prospects`, `research_runs`, `touchpoints`.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 6: API endpoints para los datos del agente.

**Lee `main.py` y revisá los Pydantic models existentes.**

### Tareas

#### 1. Crear módulo `app/api_prospects.py`

Definir router `APIRouter(prefix="/api/prospects", tags=["prospects"])`. Modelos Pydantic:

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProspectOut(BaseModel):
    id: int
    business_name: str
    vertical: str
    category_detail: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    instagram_handle: Optional[str] = None
    opportunity_score: Optional[int] = None
    status: str
    context_level: int = 0
    context_path: Optional[str] = None
    discovered_at: str
    updated_at: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

class ProspectDetail(ProspectOut):
    address: Optional[str] = None
    zip: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    email: Optional[str] = None
    facebook_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    yelp_rating: Optional[float] = None
    yelp_review_count: Optional[int] = None
    has_website: Optional[bool] = None
    website_quality_score: Optional[int] = None
    has_online_booking: Optional[bool] = None
    has_whatsapp: Optional[bool] = None
    mobile_friendly: Optional[bool] = None
    https: Optional[bool] = None
    last_post_at: Optional[str] = None
    score_breakdown_json: Optional[str] = None
    proposed_value: Optional[str] = None

class ProspectPatch(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class TouchpointCreate(BaseModel):
    channel: str  # walk_in | whatsapp | instagram_dm | email | call
    direction: str  # outbound | inbound
    summary: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None
    actor: Optional[str] = None
```

#### 2. Endpoints

```
GET    /api/prospects?vertical=&status=&score_min=&city=&assigned_to=&limit=50&offset=0&order_by=score_desc
GET    /api/prospects/{id}
PATCH  /api/prospects/{id}
POST   /api/prospects/{id}/blacklist
POST   /api/prospects/{id}/touchpoints
GET    /api/prospects/{id}/touchpoints
GET    /api/research_runs?limit=20
GET    /api/research_runs/{id}
GET    /api/metrics/daily?from=YYYY-MM-DD&to=YYYY-MM-DD
GET    /api/metrics/funnel              # cuenta por status
```

**Notas:**
- Todos requieren JWT (depender de `get_current_user`).
- `GET /api/prospects` con filtros opcionales. `order_by` acepta: `score_desc`, `score_asc`, `discovered_desc`, `updated_desc`.
- `PATCH /api/prospects/{id}` solo permite cambiar `status`, `assigned_to`, `notes`. Validar transiciones de status:
  - `discovered → reviewed | shortlisted | blacklisted`
  - `shortlisted → demo_built | rejected | blacklisted`
  - `demo_built → contacted`
  - `contacted → responded | no_response`
  - `responded → won | lost`
- `POST /api/prospects/{id}/blacklist` → status='blacklisted', registra en notas el motivo (recibí `{"reason": "..."}`).
- `GET /api/metrics/funnel` devuelve `{discovered: N, reviewed: N, shortlisted: N, ...}`.

#### 3. Registrar el router en `main.py`

```python
from app.api_prospects import router as prospects_router
app.include_router(prospects_router)
```

#### 4. Inyección de demo data para testing (opcional pero útil)

Crear script `/opt/miamipreviewlab/scripts/seed_prospects.py` que inserte 5 prospects de prueba (datos fake pero realistas en Hialeah/Miami). Documentá que se corre solo en dev:
```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python /opt/miamipreviewlab/scripts/seed_prospects.py
```

#### 5. Verificar

```bash
sudo -u mpl systemctl restart mpl-api
TOKEN=$(curl -sS -X POST http://127.0.0.1:9000/api/auth/login -d "username=rey" -d "password=<PASS>" | jq -r .access_token)
curl -sS -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:9000/api/prospects?limit=5"
curl -sS -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:9000/api/metrics/funnel"
```

#### 6. Commit

```bash
sudo -u mpl git add -A && sudo -u mpl git commit -m "API endpoints for prospects, runs, touchpoints, metrics"
sudo -u mpl git push
```

**Reportá:** lista de endpoints disponibles, output del seed, y un GET de ejemplo funcionando.

===PROMPT END===

### Validación

Después del seed, `curl /api/prospects` debe devolver una lista no vacía. `/api/metrics/funnel` devuelve un objeto con counts.

---

# Bloque 7 — Admin UI: vista de Prospects

**Pre-requisitos:** Bloques 0-6.
**Objetivo:** agregar una vista al `admin.html` actual con tabla de prospects, filtros, detalle.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 7: UI de prospects en el admin panel.

**Lee `app/admin.html` para entender el estilo actual (single-page, sin framework por lo que se entiende). Mantené coherencia.**

### Tareas

#### 1. Estructura

El `admin.html` actual probablemente tiene secciones para demos. Agregá tabs/navegación (si no existe):

```
[Demos] [Prospects] [Runs] [Métricas]
```

Cada uno muestra una sección distinta. Si ya tiene un sistema de tabs, usalo. Si no, implementá con divs `data-tab` y JS minimal.

#### 2. Vista "Prospects"

Componentes:
- **Filtros** (top bar): select Vertical, select Status, slider/input Score min, input Ciudad, select Asignado a.
- **Tabla**: columnas `Negocio`, `Vertical`, `Ciudad`, `Rating ★`, `Score`, `Status`, `Última actualización`, `Acciones`.
- **Acciones** por fila:
  - `Ver` (abre modal con detalle)
  - `Asignar` (dropdown rey/amigo)
  - `Cambiar status` (dropdown con transiciones válidas)
  - `Descargar kit` (solo si `context_level >= 1`) — placeholder por ahora, se conecta en bloque 16
- **Empty state**: si no hay prospects, mostrar mensaje claro: "El agente todavía no descubrió ningún prospect. Corré una sesión manual o esperá al cron de las 7 AM."

#### 3. Modal de detalle

Al click en "Ver", abrir modal con:
- Info principal (nombre, vertical, dirección, contacto)
- Métricas (rating, reviews, has_website, mobile_friendly, etc.)
- Score con breakdown (parsear `score_breakdown_json`)
- Propuesta de valor (`proposed_value`)
- Lista de touchpoints (cronológica, más reciente primero)
- Botones: agregar touchpoint, cambiar status, blacklist
- Si tiene `context_path`, link "Ver carpeta" (placeholder por ahora)

#### 4. Estilos

Mantenelo limpio, sin frameworks pesados. Solo CSS vanilla o lo que ya tenga el archivo. Colores y tipografía: copiar del existente.

Tema oscuro o claro, según lo que tenga ya. Detectalo del archivo y mantenelo coherente.

#### 5. JavaScript

- Llamadas a la API con `fetch` + `Authorization: Bearer ${jwt}`.
- Token guardado en `localStorage.mpl_jwt` (debería ya estar implementado, reutilizá).
- Si la respuesta da 401, redirigir al login (ya implementado, reutilizá).
- Refresco automático cada 30 segundos cuando estás viendo la lista (opcional).

#### 6. Verificar

Abrir `https://admin.miamipreviewlab.com` en el browser local del usuario. Decile que pruebe:
- Login funciona
- Tab "Prospects" muestra los 5 del seed
- Filtros funcionan (filtrar por vertical, por status)
- Click en una fila abre el modal con detalle
- Asignar a "amigo" persiste (recargar y debe seguir asignado)

#### 7. Commit

```bash
sudo -u mpl git add app/admin.html
sudo -u mpl git commit -m "Admin UI: prospects list, filters, detail modal"
sudo -u mpl git push
```

**Reportá:** screenshot textual de la vista nueva (estructura HTML resumida) y confirmación que todos los filtros funcionan.

===PROMPT END===

### Validación

Manual: el usuario abre la URL y prueba los filtros/modal con los 5 prospects del seed.

---

# Bloque 8 — Scaffold del agente + budget guard

**Pre-requisitos:** Bloques 0-7.
**Objetivo:** dejar el esqueleto del agente listo: estructura de carpetas, config, budget guard, logging propio, sin lógica de skills todavía.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 8: scaffold del agente de research.

### Tareas

#### 1. Estructura

```
/opt/miamipreviewlab/agent/
├── __init__.py
├── orchestrator.py       # entrypoint (vacío con stub)
├── config.py             # carga .env + defaults
├── db.py                 # conexión a SQLite + helpers
├── budget_guard.py       # control de gasto
├── logger.py             # logging compartido
├── skills/
│   ├── __init__.py
│   ├── base.py           # clase base de Skill
│   └── (skills se agregan en bloques 9-14)
├── scoring/
│   ├── belleza.yaml      # vacío con placeholder
│   └── hogar.yaml        # vacío con placeholder
└── config/
    ├── verticals.yaml    # definición de verticales y geos
    └── sources.yaml      # config de Google Places, Yelp, Apify
```

#### 2. Dependencias

Agregar al venv:
```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/pip install \
    httpx pyyaml pillow tenacity python-slugify trafilatura \
    anthropic apify-client playwright
sudo -u mpl /opt/miamipreviewlab/.venv/bin/playwright install --with-deps chromium
```

Si `playwright install` requiere root para `--with-deps` (suele ser así), correlo con sudo. Ojo: instala muchas deps de sistema.

#### 3. `config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path("/opt/miamipreviewlab")
load_dotenv(BASE / "data" / ".env")

DB_PATH = BASE / "data" / "mpl.db"
CONTEXT_DIR = BASE / "data" / "context"
LOG_DIR = Path("/var/log/mpl")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
YELP_API_KEY = os.getenv("YELP_API_KEY", "")
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
DAILY_BUDGET_USD = float(os.getenv("MPL_DAILY_BUDGET_USD", "1.0"))

HAIKU_MODEL = "claude-haiku-4-5"  # o el modelo Haiku actual
USER_AGENT = "MiamiPreviewLabBot/0.1 (+https://miamipreviewlab.com/bot)"
```

Instalá `python-dotenv` si no está:
```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/pip install python-dotenv
```

#### 4. `logger.py`

```python
import logging
from pathlib import Path
from agent.config import LOG_DIR
from datetime import datetime

def get_logger(name: str = "mpl.agent") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_DIR / f"agent-{datetime.now():%Y-%m-%d}.log")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    log.addHandler(fh); log.addHandler(sh)
    return log
```

#### 5. `db.py`

```python
import sqlite3
from contextlib import contextmanager
from agent.config import DB_PATH

@contextmanager
def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()
```

#### 6. `budget_guard.py`

```python
from datetime import date
from agent.db import get_db
from agent.config import DAILY_BUDGET_USD

class BudgetExceeded(Exception): pass

def spent_today() -> float:
    today = date.today().isoformat()
    with get_db() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(api_cost_usd), 0) FROM research_runs WHERE date(started_at)=?",
            (today,)
        ).fetchone()
        return float(row[0])

def check_can_spend(usd: float):
    if spent_today() + usd > DAILY_BUDGET_USD:
        raise BudgetExceeded(f"Would exceed daily budget {DAILY_BUDGET_USD}")
```

#### 7. `skills/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any
from agent.logger import get_logger

class Skill(ABC):
    name: str = "skill"
    cost_per_call_usd: float = 0.0
    
    def __init__(self):
        self.log = get_logger(f"mpl.agent.{self.name}")
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        ...
```

#### 8. `orchestrator.py` (stub)

```python
import argparse
from agent.logger import get_logger
from agent.budget_guard import spent_today, check_can_spend, BudgetExceeded
from agent.config import DAILY_BUDGET_USD

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vertical", default="belleza")
    parser.add_argument("--geo", default="hialeah")
    args = parser.parse_args()
    
    log = get_logger("mpl.agent.orchestrator")
    log.info(f"=== MPL Agent run start | vertical={args.vertical} geo={args.geo} dry_run={args.dry_run} ===")
    log.info(f"Budget today: spent={spent_today():.4f} USD / limit={DAILY_BUDGET_USD:.2f} USD")
    
    if args.dry_run:
        log.info("Dry run: stopping here.")
        return
    
    log.info("(skills not implemented yet — coming in next blocks)")

if __name__ == "__main__":
    main()
```

#### 9. `config/verticals.yaml`

```yaml
verticals:
  belleza:
    aliases: [barberia, salon, salon_unas, spa, estetica]
    gmaps_types: [hair_care, beauty_salon]
    gmaps_keywords: [barberia, barber shop, salon de uñas, nail salon, hair salon]
  hogar:
    aliases: [plomero, electricista, ac, handyman, jardineria]
    gmaps_types: [plumber, electrician, general_contractor]
    gmaps_keywords: [plumber, AC repair, handyman, jardinero, lawn care]

geos:
  hialeah:
    center: { lat: 25.8576, lng: -80.2781 }
    radius_m: 8000
  pembroke_pines:
    center: { lat: 26.0078, lng: -80.2962 }
    radius_m: 8000
  miramar:
    center: { lat: 25.9870, lng: -80.3323 }
    radius_m: 8000
  hallandale:
    center: { lat: 25.9812, lng: -80.1484 }
    radius_m: 5000
```

#### 10. Probar

```bash
cd /opt/miamipreviewlab
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --dry-run
```

Debe imprimir el log inicial y "Dry run: stopping here."

#### 11. Commit

```bash
sudo -u mpl git add -A && sudo -u mpl git commit -m "Agent scaffold: config, db, logger, budget_guard, skill base"
sudo -u mpl git push
```

**Reportá:** estructura creada, dependencias instaladas (versión de cada una), dry-run exitoso.

===PROMPT END===

### Validación

```bash
ls /opt/miamipreviewlab/agent/
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --dry-run
ls /var/log/mpl/
```

---

# Bloque 9 — Discovery skills (Google Places + Yelp + Apify Instagram)

**Pre-requisitos:** Bloques 0-8. **API keys** disponibles: Google Places, Yelp Fusion, Apify token.
**Objetivo:** descubrir candidatos en las 3 fuentes y persistirlos en `prospects` con dedupe.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 9: discovery skills.

**Asegurate que `/opt/miamipreviewlab/data/.env` tiene `GOOGLE_PLACES_KEY`, `YELP_API_KEY`, `APIFY_TOKEN`. Si falta alguna, pedísela al usuario.**

### Tareas

#### 1. `agent/skills/gmaps_search.py`

```python
from agent.skills.base import Skill
from agent.config import GOOGLE_PLACES_KEY, USER_AGENT
import httpx
from typing import List, Dict

class GMapsSearch(Skill):
    name = "gmaps_search"
    PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"
    
    def run(self, vertical_config: dict, center: dict, radius_m: int) -> List[Dict]:
        """vertical_config tiene 'gmaps_types' y 'gmaps_keywords'."""
        results = []
        types = vertical_config.get("gmaps_types", [])
        # Places API New: searchNearby con includedTypes
        headers = {
            "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.googleMapsUri",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        body = {
            "includedTypes": types,
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": center["lat"], "longitude": center["lng"]},
                    "radius": float(radius_m),
                }
            },
        }
        with httpx.Client(timeout=15) as client:
            r = client.post(self.PLACES_URL, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            for p in data.get("places", []):
                results.append({
                    "source": "gmaps",
                    "source_external_id": p["id"],
                    "business_name": p["displayName"]["text"],
                    "address": p.get("formattedAddress"),
                    "lat": p["location"]["latitude"],
                    "lng": p["location"]["longitude"],
                    "category_detail": (p.get("types") or [None])[0],
                    "google_rating": p.get("rating"),
                    "google_review_count": p.get("userRatingCount"),
                    "website_url": p.get("websiteUri"),
                    "phone": p.get("nationalPhoneNumber"),
                    "google_maps_url": p.get("googleMapsUri"),
                    "has_website": bool(p.get("websiteUri")),
                })
        self.log.info(f"gmaps_search returned {len(results)} candidates")
        return results
```

#### 2. `agent/skills/yelp_search.py`

```python
from agent.skills.base import Skill
from agent.config import YELP_API_KEY
import httpx

class YelpSearch(Skill):
    name = "yelp_search"
    URL = "https://api.yelp.com/v3/businesses/search"
    
    CATEGORY_MAP = {
        "belleza": ["barbers", "hair", "nailsalons", "spas"],
        "hogar": ["plumbing", "electricians", "handyman", "hvac"],
    }
    
    def run(self, vertical: str, center: dict, radius_m: int):
        cats = ",".join(self.CATEGORY_MAP.get(vertical, []))
        headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
        params = {
            "categories": cats,
            "latitude": center["lat"],
            "longitude": center["lng"],
            "radius": min(radius_m, 40000),
            "limit": 50,
        }
        with httpx.Client(timeout=15) as client:
            r = client.get(self.URL, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        results = []
        for b in data.get("businesses", []):
            results.append({
                "source": "yelp",
                "source_external_id": b["id"],
                "business_name": b["name"],
                "address": ", ".join(b["location"].get("display_address", [])),
                "city": b["location"].get("city"),
                "zip": b["location"].get("zip_code"),
                "lat": b["coordinates"]["latitude"],
                "lng": b["coordinates"]["longitude"],
                "phone": b.get("display_phone"),
                "yelp_rating": b.get("rating"),
                "yelp_review_count": b.get("review_count"),
            })
        self.log.info(f"yelp_search returned {len(results)} candidates")
        return results
```

#### 3. `agent/skills/ig_apify.py`

```python
from agent.skills.base import Skill
from agent.config import APIFY_TOKEN
from apify_client import ApifyClient

class IgApifySearch(Skill):
    name = "ig_apify_search"
    ACTOR = "apify/instagram-scraper"
    
    def search_by_hashtag(self, hashtag: str, results_limit: int = 30):
        client = ApifyClient(APIFY_TOKEN)
        run_input = {
            "search": hashtag,
            "searchType": "hashtag",
            "resultsLimit": results_limit,
            "resultsType": "posts",
        }
        run = client.actor(self.ACTOR).call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        # Cada item tiene ownerUsername, caption, location...
        # Agrupamos por owner
        owners = {}
        for it in items:
            u = it.get("ownerUsername")
            if not u:
                continue
            owners.setdefault(u, []).append(it)
        results = []
        for username, posts in owners.items():
            results.append({
                "source": "instagram",
                "source_external_id": username,
                "business_name": username,
                "instagram_handle": username,
                "category_detail": None,
                "evidence_json": {"posts_sampled": len(posts)},
            })
        self.log.info(f"ig_apify_search({hashtag}) → {len(results)} owners")
        return results
```

#### 4. `agent/skills/dedupe.py`

```python
from agent.db import get_db
from python_slugify import slugify
import json

def _norm_name(name: str) -> str:
    return slugify(name).lower()

def find_existing(candidate: dict):
    """Busca match por (source, source_external_id) o por (norm_name + city) o por phone."""
    with get_db() as db:
        # 1) exact source match
        if candidate.get("source") and candidate.get("source_external_id"):
            row = db.execute(
                "SELECT id, source FROM prospects WHERE source=? AND source_external_id=?",
                (candidate["source"], candidate["source_external_id"])
            ).fetchone()
            if row: return dict(row)
        # 2) name + city
        if candidate.get("business_name") and candidate.get("city"):
            row = db.execute(
                "SELECT id FROM prospects WHERE lower(business_name)=lower(?) AND lower(city)=lower(?)",
                (candidate["business_name"], candidate["city"])
            ).fetchone()
            if row: return dict(row)
        # 3) phone
        if candidate.get("phone"):
            row = db.execute(
                "SELECT id FROM prospects WHERE phone=?",
                (candidate["phone"],)
            ).fetchone()
            if row: return dict(row)
    return None

def upsert_prospect(candidate: dict, vertical: str) -> tuple[int, bool]:
    """Devuelve (prospect_id, created_bool)."""
    candidate["vertical"] = vertical
    existing = find_existing(candidate)
    with get_db() as db:
        if existing:
            # Enriquecer columnas que estén vacías
            cols_to_fill = []
            vals = []
            for k, v in candidate.items():
                if v is None or k in ("source", "source_external_id"):
                    continue
                # Solo seteamos si la columna existe y está vacía
                if k in ("evidence_json",):
                    v = json.dumps(v) if isinstance(v, (dict, list)) else v
                cols_to_fill.append(f"{k}=COALESCE({k}, ?)")
                vals.append(v)
            if cols_to_fill:
                vals.append(existing["id"])
                db.execute(f"UPDATE prospects SET {', '.join(cols_to_fill)}, updated_at=datetime('now') WHERE id=?", vals)
                db.commit()
            return existing["id"], False
        else:
            cols = list(candidate.keys())
            placeholders = ", ".join("?" for _ in cols)
            vals = []
            for c in cols:
                v = candidate[c]
                if isinstance(v, (dict, list)):
                    v = json.dumps(v)
                vals.append(v)
            cur = db.execute(
                f"INSERT INTO prospects ({', '.join(cols)}) VALUES ({placeholders})",
                vals
            )
            db.commit()
            return cur.lastrowid, True
```

#### 5. Integrar en orchestrator

Actualizar `orchestrator.py` para que con `--phase=discovery` corra estas 3 skills, dedupere y registre en `prospects` + `research_runs`.

```python
def discovery_phase(vertical: str, geo: str, log) -> dict:
    import yaml, json
    from datetime import datetime
    from agent.db import get_db
    from agent.skills.gmaps_search import GMapsSearch
    from agent.skills.yelp_search import YelpSearch
    from agent.skills.ig_apify import IgApifySearch
    from agent.skills.dedupe import upsert_prospect
    
    cfg = yaml.safe_load(open("/opt/miamipreviewlab/agent/config/verticals.yaml"))
    vcfg = cfg["verticals"][vertical]
    geo_cfg = cfg["geos"][geo]
    
    # Registrar run
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO research_runs (started_at, vertical, geo, status) VALUES (?, ?, ?, 'running')",
            (datetime.utcnow().isoformat(), vertical, geo)
        )
        run_id = cur.lastrowid
        db.commit()
    
    candidates_seen = 0
    new_count = 0
    updated_count = 0
    
    try:
        # GMaps
        gmaps = GMapsSearch().run(vcfg, geo_cfg["center"], geo_cfg["radius_m"])
        candidates_seen += len(gmaps)
        for c in gmaps:
            c["city"] = geo  # placeholder, refinar después con reverse geocode
            _, created = upsert_prospect(c, vertical)
            new_count += int(created); updated_count += int(not created)
        
        # Yelp
        yelp = YelpSearch().run(vertical, geo_cfg["center"], geo_cfg["radius_m"])
        candidates_seen += len(yelp)
        for c in yelp:
            _, created = upsert_prospect(c, vertical)
            new_count += int(created); updated_count += int(not created)
        
        # IG via Apify — solo si está APIFY_TOKEN
        from agent.config import APIFY_TOKEN
        if APIFY_TOKEN:
            # Pick una keyword del vertical para hashtag
            hashtag = vcfg.get("ig_hashtag") or f"{vertical}{geo}"  # ej: belleza hialeah
            ig = IgApifySearch().search_by_hashtag(hashtag, results_limit=30)
            candidates_seen += len(ig)
            for c in ig:
                _, created = upsert_prospect(c, vertical)
                new_count += int(created); updated_count += int(not created)
        
        with get_db() as db:
            db.execute(
                "UPDATE research_runs SET finished_at=?, candidates_seen=?, new_prospects=?, updated_prospects=?, status='success' WHERE id=?",
                (datetime.utcnow().isoformat(), candidates_seen, new_count, updated_count, run_id)
            )
            db.commit()
    except Exception as e:
        log.exception("Discovery failed")
        with get_db() as db:
            db.execute(
                "UPDATE research_runs SET finished_at=?, status='failed', errors_json=? WHERE id=?",
                (datetime.utcnow().isoformat(), json.dumps({"error": str(e)}), run_id)
            )
            db.commit()
        raise
    
    return {"run_id": run_id, "seen": candidates_seen, "new": new_count, "updated": updated_count}
```

#### 6. Probar manualmente

```bash
cd /opt/miamipreviewlab
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --vertical belleza --geo hialeah
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT COUNT(*) FROM prospects WHERE vertical='belleza'"
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT * FROM research_runs ORDER BY id DESC LIMIT 1"
```

#### 7. Rate limiting + robots.txt

Asegurate que las llamadas tienen `User-Agent` MPL. Para Yelp y Google ya está. Para Apify no aplica.

#### 8. Commit

```bash
sudo -u mpl git add -A && sudo -u mpl git commit -m "Discovery skills: gmaps, yelp, apify-ig, dedupe, orchestrator phase"
sudo -u mpl git push
```

**Reportá:** cantidad de prospects creados, run_id de la corrida, y muestra de 3 prospects insertados.

===PROMPT END===

### Validación

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT vertical, source, COUNT(*) FROM prospects GROUP BY 1,2"
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT id, status, candidates_seen, new_prospects FROM research_runs ORDER BY id DESC LIMIT 3"
```

Debe haber `prospects` con sources `gmaps`, `yelp`, e `instagram`. Y al menos un `research_runs` con `status='success'`.

---

# Bloque 10 — Enrichment Nivel 1 (place details, photos, screenshot, logo)

**Pre-requisitos:** Bloques 0-9.
**Objetivo:** para cada prospect nuevo, descargar fotos de Google Places, screenshot del sitio actual, logo, todo a la carpeta de contexto.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 10: enrichment nivel 1.

### Tareas

#### 1. Estructura de carpeta de contexto

Cada prospect tiene `context_path = /opt/miamipreviewlab/data/context/{slug}/`. El slug se deriva de `business_name + city` (slugify).

```
data/context/{slug}/
├── raw/
├── images/
│   ├── gmaps/
│   ├── instagram/
│   └── ...
└── text/
```

#### 2. `agent/skills/fetch_place_details.py`

Google Places API "Place Details (New)" da photos URLs.

```python
class FetchPlaceDetails(Skill):
    name = "fetch_place_details"
    URL = "https://places.googleapis.com/v1/places/{place_id}"
    PHOTO_URL = "https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=1200&key={key}"
    
    def run(self, place_id: str) -> dict:
        # Devuelve dict con: photos (lista de URLs), websiteUri, regularOpeningHours, etc.
        ...
```

Campos a pedir: `id,displayName,formattedAddress,websiteUri,nationalPhoneNumber,internationalPhoneNumber,regularOpeningHours,photos,rating,userRatingCount,reviews,types,businessStatus`.

Persiste en `prospect.evidence_json["gmaps_details"] = {...}` y guarda raw en `context/{slug}/raw/gmaps_place.json`.

#### 3. `agent/skills/download_images.py`

```python
class DownloadImages(Skill):
    name = "download_images"
    
    def gmaps_photos(self, photo_names: list[str], dest: Path, max_count=10):
        # Para cada photo_name (ej: "places/.../photos/..."), llamar al endpoint media y guardar
        ...
    
    def compress_to_webp(self, src: Path, dest: Path, quality=72, max_dim=1600):
        from PIL import Image
        img = Image.open(src).convert("RGB")
        img.thumbnail((max_dim, max_dim))
        img.save(dest, "WEBP", quality=quality, method=6)
```

#### 4. `agent/skills/screenshot_site.py`

```python
class ScreenshotSite(Skill):
    name = "screenshot_site"
    
    def run(self, url: str, out_path: Path):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1366, "height": 900})
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.screenshot(path=str(out_path), full_page=False)
            finally:
                browser.close()
```

Manejá excepciones: si el sitio no carga, registralo en `evidence_json["website_load_error"] = "..."` y `has_website = false` o `website_quality_score = 0`.

#### 5. `agent/skills/extract_logo.py`

Heurística:
1. Buscar `<link rel="icon">`, `<link rel="apple-touch-icon">`.
2. Buscar `<meta property="og:image">`.
3. Buscar imágenes con clase/id que contenga "logo".
4. Como fallback: `https://{domain}/favicon.ico`.
5. Descargar la mejor (más grande, no SVG-icono).

#### 6. `agent/skills/analyze_website_quality.py` (heurístico, sin LLM)

```python
def score_website(html: str, page_status: int, load_time_ms: int) -> tuple[int, dict]:
    """Devuelve (score 0-100, breakdown)."""
    breakdown = {}
    score = 50  # baseline
    if page_status >= 400 or page_status == 0:
        return 0, {"reason": "unreachable", "status": page_status}
    breakdown["loads"] = True
    if load_time_ms > 5000: score -= 10; breakdown["slow"] = True
    has_viewport = '<meta name="viewport"' in html.lower()
    if has_viewport: score += 10
    else: breakdown["no_viewport"] = True; score -= 10
    if "<html" in html and len(html) < 2000: score -= 20; breakdown["too_short"] = True
    # Detección de plantillas obsoletas (heurísticas suaves)
    if "wix.com" in html.lower(): breakdown["wix"] = True
    if "godaddy" in html.lower(): breakdown["godaddy"] = True; score -= 5
    # SSL?
    # Detectar año de copyright
    import re
    m = re.search(r"©\s*(\d{4})", html)
    if m:
        year = int(m.group(1))
        breakdown["copyright_year"] = year
        if year < 2024: score -= 10
    return max(0, min(100, score)), breakdown
```

#### 7. `agent/skills/detect_booking.py`

Patrones a buscar en HTML:
- `booksy.com`, `vagaro.com`, `fresha.com`, `squareup.com/appointments`, `calendly.com`, `setmore.com`
- Iframes a estos dominios
- Texto literal: "book now", "reservar", "agendar cita"

#### 8. Orquestación nivel 1

Agregar fase al orchestrator:

```python
def enrichment_level1(prospect_id: int, log):
    # 1. Si tiene source gmaps con external_id, fetch_place_details
    # 2. Crear carpeta data/context/{slug}/
    # 3. Descargar photos a images/gmaps/, comprimir a webp
    # 4. Si tiene website_url, screenshot + extract_logo + analyze_website_quality + detect_booking
    # 5. Update prospect: context_path, context_level=1, context_collected_at, has_*, website_quality_score
```

#### 9. Probar

```bash
cd /opt/miamipreviewlab
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -c "
from agent.orchestrator import enrichment_level1
from agent.logger import get_logger
log = get_logger('test')
enrichment_level1(1, log)
"
ls /opt/miamipreviewlab/data/context/
```

Validar visualmente:
```bash
ls -la /opt/miamipreviewlab/data/context/<slug>/images/gmaps/
ls -la /opt/miamipreviewlab/data/context/<slug>/images/current_site.png
```

#### 10. Commit + reportá número de prospects enriquecidos a nivel 1.

===PROMPT END===

### Validación

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT COUNT(*) FROM prospects WHERE context_level >= 1"
find /opt/miamipreviewlab/data/context -name "*.webp" | head -5
```

---

# Bloque 11 — Enrichment Nivel 2: Website crawl

**Pre-requisitos:** Bloques 0-10.
**Objetivo:** para prospects con score ≥70 (shortlisted), crawl el sitio, extraer servicios/horarios/about/reviews, guardar en `text/`.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 11: enrichment nivel 2 — sitio web.

### Tareas

#### 1. `agent/skills/crawl_website.py`

- Max 10 páginas por sitio.
- Respetar `robots.txt` (lib `urllib.robotparser`).
- 1 req/2s al mismo dominio.
- User-Agent identificable.
- Follow solo links del mismo dominio.
- Priorizar páginas con keywords en URL: `services`, `servicios`, `about`, `nosotros`, `contact`, `contacto`, `precios`, `prices`, `menu`.

```python
class CrawlWebsite(Skill):
    name = "crawl_website"
    
    def run(self, root_url: str, max_pages=10) -> list[dict]:
        # Devuelve lista de {url, status, html, fetched_at}
        # Guardar todo a context/{slug}/raw/website_pages/
        ...
```

#### 2. `agent/skills/extract_text.py`

Usar `trafilatura` para extraer texto principal de cada página. Persistir:
- `text/about.md` — junta el texto de about/nosotros + index.
- `text/services.json` — lista normalizada (intentar primero heurísticas).

```python
import trafilatura

def extract_main_text(html: str) -> str:
    return trafilatura.extract(html) or ""
```

#### 3. `agent/skills/extract_services_heuristic.py`

Buscar:
- `<ul>` o `<ol>` después de `<h*>Services</h*>` o `Servicios`
- Listas con precios `$XX`
- Tablas con dos columnas (nombre, precio)

Output: `[{"name": "...", "price_usd": null|float, "duration_min": null|int, "description": null|str}]`

#### 4. `agent/skills/extract_hours.py`

Si ya tenemos `regularOpeningHours` de Google Places → usalo (es lo más confiable).
Si no, heurística sobre el HTML del about/contact:
- Buscar patrones "Mon-Fri 9-5", "Lunes a Viernes 9:00-17:00", etc.

Output `text/hours.json`:
```json
{"mon": "09:00-19:00", "tue": "09:00-19:00", ..., "sun": "closed"}
```

#### 5. `agent/skills/extract_contact.py`

Buscar en HTML + Google Places:
- Email: regex
- Teléfono: regex US (`\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}`)
- WhatsApp: links `wa.me/...` o `api.whatsapp.com/send?phone=...`
- IG: links a `instagram.com/...`
- FB: links a `facebook.com/...`

Output `text/contact.json`.

#### 6. `agent/skills/extract_top_reviews.py`

De `gmaps_details["reviews"]` (si lo tenemos):
- Filtrar rating ≥4
- Ordenar por largo del texto (más útil para testimonios)
- Top 10
- Output `text/reviews_top.md` (markdown legible).

#### 7. Orquestación nivel 2 web

```python
def enrichment_level2_web(prospect_id: int, log):
    # Asume context_level >= 1
    # 1. Si has_website y website_url, crawl
    # 2. Extraer text/about.md, services.json, hours.json, contact.json
    # 3. Extract top reviews
    # 4. Update prospect.context_level = 2 (si IG aún no, dejar 2 igual)
```

#### 8. Probar con un prospect específico

```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -c "
from agent.orchestrator import enrichment_level2_web
from agent.logger import get_logger
enrichment_level2_web(1, get_logger('test'))
"
ls /opt/miamipreviewlab/data/context/<slug>/text/
cat /opt/miamipreviewlab/data/context/<slug>/text/about.md
cat /opt/miamipreviewlab/data/context/<slug>/text/services.json
```

#### 9. Commit y reportá.

===PROMPT END===

### Validación

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT COUNT(*) FROM prospects WHERE context_level >= 2"
ls /opt/miamipreviewlab/data/context/*/text/services.json 2>/dev/null | head
```

---

# Bloque 12 — Enrichment Nivel 2: Instagram (Apify)

**Pre-requisitos:** Bloques 0-11.
**Objetivo:** para prospects con `instagram_handle`, bajar profile + últimas 12 fotos via Apify.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 12: enrichment IG con Apify.

### Tareas

#### 1. `agent/skills/ig_profile_apify.py`

```python
class IgProfileApify(Skill):
    name = "ig_profile_apify"
    ACTOR = "apify/instagram-profile-scraper"  # o el que use scraper de profile
    
    def run(self, username: str) -> dict:
        client = ApifyClient(APIFY_TOKEN)
        run_input = {"usernames": [username], "resultsLimit": 12}
        run = client.actor(self.ACTOR).call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items: return {}
        profile = items[0]
        # Estructura del actor incluye: followersCount, postsCount, biography, latestPosts (lista de URLs)
        return profile
```

#### 2. Descargar fotos del feed

Las URLs de las imágenes vienen en `profile["latestPosts"]` (o el campo que use el actor). Descargá hasta 12, comprimí a WebP, guardá en `context/{slug}/images/instagram/01.webp` ... `12.webp`.

#### 3. Persistir raw

`context/{slug}/raw/ig_profile.json`.

#### 4. Update prospect

- `instagram_handle` (si no lo tiene)
- `last_post_at` (timestamp del último post)
- `evidence_json["ig"] = {"followers": N, "posts": N}`

#### 5. Orquestar

```python
def enrichment_level2_ig(prospect_id: int, log):
    # Si tiene instagram_handle, bajar profile + fotos
    # Si llega a este nivel 2 sin haber pasado por web (porque no tenía website), bumpea a level=2 igual
```

#### 6. Probar y commit.

===PROMPT END===

### Validación

```bash
ls /opt/miamipreviewlab/data/context/*/images/instagram/*.webp 2>/dev/null | head
```

---

# Bloque 13 — Scoring con YAML + Haiku

**Pre-requisitos:** Bloques 0-12. **`ANTHROPIC_API_KEY` configurada** en `.env`.
**Objetivo:** puntuar oportunidades con reglas declarativas + LLM (Haiku) para casos ambiguos.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 13: scoring.

### Tareas

#### 1. Reglas YAML

`agent/scoring/belleza.yaml`:

```yaml
vertical: belleza
threshold_shortlist: 75
threshold_skip: 30
weights:
  has_website: -25         # negativo = bueno (oportunidad)
  no_website: 40           # premio si no tiene
  bad_website_quality: 30  # si score web < 50
  good_website_quality: -20  # si score web > 80, restamos (ya está bien)
  has_online_booking: -40  # ya tiene, baja oportunidad
  good_rating_high_volume: 20  # rating>=4.0 y reviews>=30
  low_review_count: -15    # <5 reviews (puede estar dormido)
  ig_active: 15            # post últimos 14 días
hard_skip_rules:
  - field: business_status
    equals: CLOSED_PERMANENTLY
  - field: google_review_count
    less_than: 3
  - field: business_name
    matches_any: ["supercuts", "great clips", "sport clips"]  # cadenas
```

`agent/scoring/hogar.yaml`: análogo con sus propias keywords.

#### 2. `agent/skills/score_opportunity.py`

```python
import yaml, json
from agent.skills.base import Skill
from agent.db import get_db

class ScoreOpportunity(Skill):
    name = "score_opportunity"
    cost_per_call_usd = 0.001
    
    def __init__(self, vertical: str):
        super().__init__()
        self.cfg = yaml.safe_load(open(f"/opt/miamipreviewlab/agent/scoring/{vertical}.yaml"))
    
    def run(self, prospect: dict) -> dict:
        # 1) hard skip rules
        for rule in self.cfg.get("hard_skip_rules", []):
            if self._matches_rule(prospect, rule):
                return {"score": 0, "skip": True, "reason": f"hard_skip: {rule}"}
        # 2) weighted sum
        breakdown = {}
        score = 50
        w = self.cfg["weights"]
        if prospect.get("has_website"):
            score += w["has_website"]; breakdown["has_website"] = w["has_website"]
        else:
            score += w["no_website"]; breakdown["no_website"] = w["no_website"]
        wq = prospect.get("website_quality_score") or 0
        if prospect.get("has_website") and wq < 50:
            score += w["bad_website_quality"]; breakdown["bad_website_quality"] = w["bad_website_quality"]
        if prospect.get("has_website") and wq > 80:
            score += w["good_website_quality"]; breakdown["good_website_quality"] = w["good_website_quality"]
        if prospect.get("has_online_booking"):
            score += w["has_online_booking"]; breakdown["has_online_booking"] = w["has_online_booking"]
        rc = prospect.get("google_review_count") or 0
        rt = prospect.get("google_rating") or 0
        if rt >= 4.0 and rc >= 30:
            score += w["good_rating_high_volume"]; breakdown["good_rating_high_volume"] = w["good_rating_high_volume"]
        if rc < 5:
            score += w["low_review_count"]; breakdown["low_review_count"] = w["low_review_count"]
        # ig_active: chequear last_post_at
        # ...
        score = max(0, min(100, score))
        return {"score": score, "breakdown": breakdown, "skip": False}
    
    def _matches_rule(self, p, rule):
        ...
```

#### 3. (Opcional ahora) Refinamiento con Haiku

Para casos border (50 ≤ score ≤ 70), llamar a Haiku con la ficha completa y pedirle un ajuste explicado. Lo dejamos como tarea TODO para el siguiente bloque — por ahora solo reglas heurísticas.

#### 4. Persistir

```python
def score_and_persist(prospect_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()
        if not row: return
        p = dict(row)
    scorer = ScoreOpportunity(p["vertical"])
    result = scorer.run(p)
    with get_db() as db:
        db.execute(
            "UPDATE prospects SET opportunity_score=?, score_breakdown_json=?, updated_at=datetime('now') WHERE id=?",
            (result["score"], json.dumps(result.get("breakdown", {})), prospect_id)
        )
        if result["score"] >= scorer.cfg["threshold_shortlist"]:
            db.execute("UPDATE prospects SET status=CASE WHEN status='discovered' THEN 'shortlisted' ELSE status END WHERE id=?", (prospect_id,))
        elif result["score"] <= scorer.cfg.get("threshold_skip", 30):
            db.execute("UPDATE prospects SET status=CASE WHEN status='discovered' THEN 'rejected' ELSE status END WHERE id=?", (prospect_id,))
        db.commit()
```

#### 5. Probar con todos los prospects

```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -c "
from agent.skills.score_opportunity import score_and_persist
from agent.db import get_db
with get_db() as db:
    ids = [r[0] for r in db.execute('SELECT id FROM prospects').fetchall()]
for i in ids:
    score_and_persist(i)
"
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT status, COUNT(*), AVG(opportunity_score) FROM prospects GROUP BY status"
```

#### 6. Commit + reportá distribución de scores.

===PROMPT END===

### Validación

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT id, business_name, opportunity_score, status FROM prospects ORDER BY opportunity_score DESC LIMIT 10"
```

---

# Bloque 14 — Briefing.json + README.md (Haiku)

**Pre-requisitos:** Bloques 0-13.
**Objetivo:** para los top 5 con score ≥70, generar `briefing.json` (datos limpios estructurados) y `README.md` (legible humano) usando Claude Haiku.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 14: briefing + README con Haiku.

### Tareas

#### 1. `agent/skills/structure_context.py`

```python
import json
from pathlib import Path
from anthropic import Anthropic
from agent.skills.base import Skill
from agent.config import ANTHROPIC_API_KEY, HAIKU_MODEL
from agent.budget_guard import check_can_spend
from agent.db import get_db

PROMPT_TEMPLATE = """Sos un analista de Miami Preview Lab. Te paso datos crudos de un prospecto y necesito que devuelvas DOS cosas:

1. Un JSON estructurado (`briefing.json`) con esta forma:
```json
{
  "business": {
    "name": "...",
    "tagline": "...",            // genera 1 línea atractiva en español si no hay
    "category": "...",
    "address": "...",
    "phone": "...",
    "whatsapp": "...",
    "hours": {"mon":"...","tue":"...","wed":"...","thu":"...","fri":"...","sat":"...","sun":"..."},
    "summary_es": "..."          // 2-3 frases en español que resumen el negocio
  },
  "services": [
    {"name":"...","duration_min":null,"price_usd":null,"description":"..."}
  ],
  "testimonials": [
    {"author":"...","text":"...","rating":5}
  ],
  "social": {"instagram":"@...","facebook":"...","website":"..."},
  "opportunity": {
    "score": 0-100,
    "why_now": "...",            // 1-2 frases: por qué este es un buen prospecto AHORA
    "proposed_tier": "Starter|Pro|Business",
    "proposed_value_es": "..."   // 3-5 frases sobre qué le venderíamos y por qué
  }
}
```

2. Un README markdown en español, con esta estructura:
```
# {business_name}

**Vertical:** ...
**Score:** ... / 100
**Ubicación:** ...

## Resumen del negocio
...

## Qué le venderíamos
...

## Datos clave
- Teléfono: ...
- Web actual: ...
- IG: ...
- Reviews Google: X.X (N reviews)

## Servicios detectados
- ...

## Por qué este prospecto AHORA
...

## Archivos en este kit
- `images/gmaps/` — N fotos
- `images/instagram/` — N fotos
- `text/services.json`, `text/hours.json`, `text/contact.json`
- `briefing.json` — datos estructurados para el generador de demo
```

DATOS CRUDOS:
{raw_data}

RESPONDÉ con JSON válido del briefing PRIMERO, después con marcador `---README---` y luego el markdown.
"""

class StructureContext(Skill):
    name = "structure_context"
    cost_per_call_usd = 0.02
    
    def __init__(self):
        super().__init__()
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def run(self, prospect: dict, context_dir: Path):
        check_can_spend(self.cost_per_call_usd)
        raw = self._gather_raw(prospect, context_dir)
        prompt = PROMPT_TEMPLATE.format(raw_data=json.dumps(raw, indent=2, ensure_ascii=False))
        
        resp = self.client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=4000,
            messages=[{"role":"user","content":prompt}],
        )
        text = resp.content[0].text
        tokens_in = resp.usage.input_tokens
        tokens_out = resp.usage.output_tokens
        # Haiku 4.5 pricing: $0.80/MTok in, $4/MTok out
        cost = (tokens_in/1e6)*0.80 + (tokens_out/1e6)*4.0
        
        # Split
        if "---README---" in text:
            briefing_text, readme = text.split("---README---", 1)
        else:
            briefing_text, readme = text, ""
        briefing_text = briefing_text.strip().strip("`")
        if briefing_text.startswith("json"):
            briefing_text = briefing_text[4:].strip()
        try:
            briefing = json.loads(briefing_text)
        except json.JSONDecodeError as e:
            self.log.error(f"JSON decode error: {e}")
            briefing = {"_raw_parse_error": str(e), "_raw": briefing_text}
        
        (context_dir / "briefing.json").write_text(json.dumps(briefing, indent=2, ensure_ascii=False))
        (context_dir / "README.md").write_text(readme.strip())
        return {"cost_usd": cost, "tokens_in": tokens_in, "tokens_out": tokens_out}
    
    def _gather_raw(self, prospect: dict, context_dir: Path) -> dict:
        raw = {"prospect_db": prospect}
        for fname in ["gmaps_place.json", "ig_profile.json"]:
            f = context_dir / "raw" / fname
            if f.exists():
                try: raw[fname] = json.loads(f.read_text())
                except: pass
        for fname in ["about.md", "services.json", "hours.json", "contact.json", "reviews_top.md"]:
            f = context_dir / "text" / fname
            if f.exists():
                raw[fname] = f.read_text()
        return raw
```

#### 2. Acumular costo en `research_runs`

Cada llamada incrementa `tokens_in`, `tokens_out`, `api_cost_usd` del run actual.

#### 3. Orquestación nivel 3

```python
def enrichment_level3_top5(run_id: int, vertical: str, log):
    # Top 5 con score ≥70 que aún no tienen briefing.json
    with get_db() as db:
        rows = db.execute("""
            SELECT * FROM prospects 
            WHERE vertical=? AND opportunity_score>=70 AND status='shortlisted'
              AND (context_level < 3 OR context_path IS NULL)
            ORDER BY opportunity_score DESC LIMIT 5
        """, (vertical,)).fetchall()
    
    sc = StructureContext()
    total_cost = 0
    for r in rows:
        p = dict(r)
        ctx = Path(p["context_path"])
        if not ctx.exists():
            log.warning(f"No context dir for {p['business_name']}"); continue
        try:
            result = sc.run(p, ctx)
            total_cost += result["cost_usd"]
            with get_db() as db:
                db.execute("UPDATE prospects SET context_level=3, updated_at=datetime('now') WHERE id=?", (p["id"],))
                db.execute("UPDATE research_runs SET api_cost_usd=api_cost_usd+?, tokens_in=tokens_in+?, tokens_out=tokens_out+? WHERE id=?",
                           (result["cost_usd"], result["tokens_in"], result["tokens_out"], run_id))
                db.commit()
        except Exception as e:
            log.exception(f"structure_context failed for {p['business_name']}")
    log.info(f"Level 3 done. Cost: ${total_cost:.4f}")
```

#### 4. Probar

```bash
sudo -u mpl /opt/miamipreviewlab/.venv/bin/python -c "
from agent.orchestrator import enrichment_level3_top5
from agent.logger import get_logger
enrichment_level3_top5(run_id=1, vertical='belleza', log=get_logger('test'))
"
ls /opt/miamipreviewlab/data/context/*/briefing.json
cat /opt/miamipreviewlab/data/context/<algun-slug>/README.md
```

#### 5. Commit + reportá costo total de la corrida.

===PROMPT END===

### Validación

```bash
find /opt/miamipreviewlab/data/context -name "briefing.json" | wc -l   # debería ser ~5
find /opt/miamipreviewlab/data/context -name "README.md" | wc -l       # idem
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT api_cost_usd FROM research_runs ORDER BY id DESC LIMIT 1"
```

---

# Bloque 15 — Orchestrator end-to-end + systemd timer

**Pre-requisitos:** Bloques 0-14.
**Objetivo:** un comando que ejecuta todo el pipeline diario; systemd timer que lo dispara a las 7 AM ET.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 15: orchestrator completo + timer.

### Tareas

#### 1. Refactor `orchestrator.py` con fases

```python
def daily_run(vertical: str, geo: str):
    log = get_logger("mpl.agent.daily")
    log.info(f"=== DAILY RUN START | vertical={vertical} geo={geo} ===")
    
    # Phase 1: discovery
    disc = discovery_phase(vertical, geo, log)
    run_id = disc["run_id"]
    log.info(f"Discovery: seen={disc['seen']} new={disc['new']} updated={disc['updated']}")
    
    # Phase 2: enrichment L1 (todos los discovered de este run)
    new_ids = _get_recent_prospect_ids(vertical, since_run_id=run_id)
    log.info(f"Enrichment L1: {len(new_ids)} prospects")
    for pid in new_ids:
        try: enrichment_level1(pid, log)
        except Exception: log.exception(f"L1 failed for {pid}")
    
    # Phase 3: scoring
    log.info(f"Scoring {len(new_ids)} prospects")
    for pid in new_ids:
        try: score_and_persist(pid)
        except Exception: log.exception(f"scoring failed for {pid}")
    
    # Phase 4: enrichment L2 (solo shortlisted del run)
    shortlist = _get_shortlist(vertical, since_run_id=run_id)
    log.info(f"Enrichment L2: {len(shortlist)} prospects")
    for pid in shortlist:
        try:
            enrichment_level2_web(pid, log)
            enrichment_level2_ig(pid, log)
        except Exception: log.exception(f"L2 failed for {pid}")
    
    # Phase 5: briefing (top 5)
    enrichment_level3_top5(run_id, vertical, log)
    
    # Phase 6: metrics
    update_metrics_daily()
    
    log.info("=== DAILY RUN END ===")
    return run_id
```

#### 2. Helpers `_get_recent_prospect_ids`, `_get_shortlist`, `update_metrics_daily`

Implementar consultas SQL correspondientes.

#### 3. CLI

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--vertical", default="belleza")
    parser.add_argument("--geo", default="hialeah")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        # solo log
        ...
    else:
        daily_run(args.vertical, args.geo)
```

#### 4. Systemd service + timer

`/etc/systemd/system/mpl-research.service`:
```ini
[Unit]
Description=MPL Research Agent (one-shot daily)
After=network.target

[Service]
Type=oneshot
User=mpl
Group=mpl
WorkingDirectory=/opt/miamipreviewlab
EnvironmentFile=/opt/miamipreviewlab/data/.env
Environment="PATH=/opt/miamipreviewlab/.venv/bin:/usr/bin:/bin"
ExecStart=/opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --vertical belleza --geo hialeah
StandardOutput=append:/var/log/mpl/research.log
StandardError=append:/var/log/mpl/research.log
```

`/etc/systemd/system/mpl-research.timer`:
```ini
[Unit]
Description=Run MPL Research daily at 7:00 ET

[Timer]
OnCalendar=*-*-* 11:00:00 UTC
# 11:00 UTC = 7:00 EDT / 6:00 EST. Si es invierno, ajustar.
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

Habilitar:
```bash
systemctl daemon-reload
systemctl enable --now mpl-research.timer
systemctl list-timers --no-pager | grep mpl
```

#### 5. Disparar manual para test

```bash
systemctl start mpl-research.service
journalctl -u mpl-research -n 50 --no-pager
```

#### 6. Conmutador para no quemar budget en tests

En `orchestrator.daily_run`, leer `MPL_DRY_BUDGET=1` del env para saltear las llamadas a Haiku.

#### 7. Commit + verificá que el timer está activo y la próxima corrida está agendada.

===PROMPT END===

### Validación

```bash
systemctl list-timers --no-pager | grep mpl-research
journalctl -u mpl-research -n 30 --no-pager
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT * FROM research_runs ORDER BY id DESC LIMIT 1"
```

---

# Bloque 16 — Zip endpoints + Admin UI: Dashboard del Agente

**Pre-requisitos:** Bloques 0-15.
**Objetivo:** descargar kits via zip, y dashboard en el panel con última corrida + top 5 + historial.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 16: zip endpoints + dashboard del agente.

### Tareas

#### 1. Endpoints zip en `app/api_prospects.py` (o módulo nuevo)

```python
import io, zipfile
from fastapi.responses import StreamingResponse
from pathlib import Path

@router.get("/{prospect_id}/context/zip")
async def context_zip(prospect_id: int, user: str = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT business_name, context_path FROM prospects WHERE id=?", (prospect_id,)).fetchone()
    if not row or not row["context_path"]:
        raise HTTPException(404, "No context")
    src = Path(row["context_path"])
    if not src.exists():
        raise HTTPException(404, "Context dir missing on disk")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in src.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(src.parent))
    buf.seek(0)
    slug = src.name
    return StreamingResponse(buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}-kit.zip"'})

@router.get("/top/zip")
async def top_zip(date: str = None, vertical: str = None, user: str = Depends(get_current_user)):
    # Devuelve zip con top 5 del día (date YYYY-MM-DD opcional, default hoy)
    # Más un INDEX.md que lista los 5 con sus scores
    ...
```

Seguridad:
- Validar `prospect_id` numérico (FastAPI ya valida tipo).
- Verificar que `src` está bajo `/opt/miamipreviewlab/data/context/` (no path traversal).

#### 2. UI: Dashboard tab en `admin.html`

Sección "Agente" con:
- **Tarjeta "Última corrida"**: fecha, vertical, status, candidates_seen, new_prospects, api_cost_usd.
- **Tarjeta "Budget hoy"**: gastado / límite (barra de progreso).
- **Tabla "Top 5 del día"**: business_name, vertical, score, status, botones [Ver detalle] [Descargar kit].
- **Botón "Descargar top 5 del día"** (zip con los 5 kits).
- **Tabla "Historial de corridas"**: últimas 20 runs con paginación.
- **Funnel**: counts por status (discovered → reviewed → shortlisted → demo_built → contacted → won/lost).

#### 3. Integrar botón "Descargar kit" en la vista Prospects (del bloque 7)

Ya está como placeholder, ahora conectalo: cuando `context_level >= 1`, mostrar el botón y al click → `GET /api/prospects/{id}/context/zip` con header `Authorization: Bearer ${jwt}`. Usar `fetch` y blob para forzar download.

#### 4. UX

- Cuando un prospect aún no tiene briefing (level<3) pero sí context (level>=1), mostrar el botón pero con tooltip "Kit parcial — sin briefing IA".
- Cuando level=3, mostrar badge "📦 Listo".

#### 5. Probar

- Desde el browser: navegar al dashboard, ver la última corrida.
- Click en "Descargar kit" de un prospect top → baja un .zip que al descomprimir tiene `briefing.json`, `README.md`, `images/`, `text/`.

#### 6. Commit + reportá.

===PROMPT END===

### Validación

```bash
# desde local
TOKEN=...
curl -sS -H "Authorization: Bearer $TOKEN" -o /tmp/kit.zip http://127.0.0.1:9000/api/prospects/1/context/zip
unzip -l /tmp/kit.zip
```

Debe listar `briefing.json`, `README.md`, archivos en `images/` y `text/`.

---

# Bloque 17 — Tests E2E + Handbook + segundo vertical

**Pre-requisitos:** Bloques 0-16.
**Objetivo:** validar el flujo completo, documentar para el partner comercial, agregar el segundo vertical.

### 🟦 PROMPT PARA CLAUDE CODE

===PROMPT START===

Bloque 17: validación end-to-end + handbook + segundo vertical.

### Tareas

#### 1. Test E2E

Correr una semana real: dejar el timer corriendo 7 días y cada mañana revisar:
- ¿La corrida terminó OK?
- ¿Cuántos prospects nuevos?
- ¿Top 5 tiene calidad (revisión manual)?
- ¿Costo bajo budget?

Documentar issues en `/opt/miamipreviewlab/AGENT_TUNING.md`.

#### 2. Tuning de scoring

Basado en revisión humana del top 5 cada día, ajustar los YAML de scoring. Iterar.

#### 3. Segundo vertical: hogar

Completar `agent/scoring/hogar.yaml` con sus weights y hard_skip_rules.
Confirmar que el vertical funciona end-to-end con `--vertical hogar`.

Agregar al timer un segundo trigger o un script wrapper que corra ambos verticales en secuencia:
```bash
# /opt/miamipreviewlab/scripts/run_all_verticals.sh
#!/usr/bin/env bash
set -e
/opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --vertical belleza --geo hialeah
/opt/miamipreviewlab/.venv/bin/python -m agent.orchestrator --vertical hogar --geo hialeah
```
Cambiar el `ExecStart` del service a este script.

#### 4. Handbook para el partner comercial

Crear `/opt/miamipreviewlab/HANDBOOK.md`:

```markdown
# Manual operativo — Miami Preview Lab

## Cómo abrir el panel
1. URL: https://admin.miamipreviewlab.com
2. Usuario: rey
3. Contraseña: pedísela a Rey (no la guardes en texto)

## Flujo diario (todas las mañanas, 15 minutos)
1. Abrí el panel y andá al tab "Agente".
2. Revisá la "Última corrida": debe estar verde y haber traído >0 prospects.
3. Mirá el "Top 5 del día".
4. Para cada uno:
   - Click "Ver detalle"
   - Leé el `README.md` del kit (botón "Ver README")
   - Si la oportunidad te convence: click "Descargar kit"
5. Te llevás los kits a tu carpeta de demos local.

## Cuándo hacer un walk-in
- Demo armada en subdominio (ej: hialeahbarber.miamipreviewlab.com)
- Score >75
- Negocio abierto

## Después del walk-in
1. Volvé al panel → buscá el prospect
2. Click "Agregar touchpoint":
   - Channel: walk_in
   - Direction: outbound
   - Outcome: interested | rejected | meeting_scheduled
   - Summary: 1-2 frases
   - Next action: qué sigue
3. Cambiá status si corresponde (contacted, responded, won, lost)

## Si algo no funciona
- Decile a Rey
- No toques systemd ni la DB
```

#### 5. Commit final del bloque, push.

#### 6. Reportá: status final del sistema, número de prospects por status, runs por vertical, costo acumulado.

===PROMPT END===

### Validación final

```bash
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT vertical, status, COUNT(*) FROM prospects GROUP BY 1, 2"
sqlite3 /opt/miamipreviewlab/data/mpl.db "SELECT date(started_at) AS d, vertical, candidates_seen, new_prospects, api_cost_usd FROM research_runs ORDER BY id DESC LIMIT 14"
ls /opt/miamipreviewlab/HANDBOOK.md
systemctl status mpl-research.timer --no-pager
```

---

# Cierre

Cuando hayas completado los 18 bloques:

- ✅ SSH endurecido, API non-root, secrets fuera del unit.
- ✅ Esquema con prospects + runs + touchpoints + métricas.
- ✅ Panel admin con vista Prospects + Dashboard del agente.
- ✅ Agente corriendo diario, 2 verticales, ~30 prospects/día descubiertos, top 5 con briefing IA.
- ✅ Kits descargables como zip.
- ✅ Handbook para tu amigo.

## Próximas mejoras (no en este plan, futuras iteraciones)

- Notificaciones por Telegram cuando termina la corrida.
- Dashboard de métricas con gráficos (Chart.js).
- Plantilla de propuesta exportable a PDF.
- Soporte multi-tenant (cuando agreguen un tercer socio).
- Backups DB a Backblaze B2 (offsite).
- Migrar SQLite a Postgres cuando pasen de 50k prospects.
- LLC formada → cambiar branding del bot, registros legales, etc.

---

**Fin del plan.** Cualquier duda, parar y preguntar antes de seguir.
