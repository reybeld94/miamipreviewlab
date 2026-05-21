# PRE_AGENT_SNAPSHOT — Miami Preview Lab
> Generado el 2026-05-21 al inicio del Bloque 0.

---

## systemctl status mpl-api

```
● mpl-api.service - MiamiPreviewLab Admin API
     Loaded: loaded (/etc/systemd/system/mpl-api.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-05-20 03:37:29 UTC; 1 day 15h ago
   Main PID: 11340 (uvicorn)
      Tasks: 2 (limit: 4569)
     Memory: 32.1M (peak: 32.6M)
        CPU: 6min 24.192s
     CGroup: /system.slice/mpl-api.service
             └─11340 /opt/miamipreviewlab/.venv/bin/python3 ... uvicorn app.main:app --host 127.0.0.1 --port 9000
```

---

## systemctl status caddy

```
● caddy.service - Caddy
     Loaded: loaded (/usr/lib/systemd/system/caddy.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-05-20 03:27:38 UTC; 1 day 15h ago
   Main PID: 10444 (caddy)
      Tasks: 10 (limit: 4569)
     Memory: 12.0M (peak: 17.8M)
     CGroup: /system.slice/caddy.service
             └─10444 /usr/bin/caddy run --environ --config /etc/caddy/Caddyfile
```

---

## ss -tlnp

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      2048       127.0.0.1:9000      0.0.0.0:*    uvicorn (pid=11340)
LISTEN 0      4096      127.0.0.54:53        0.0.0.0:*    systemd-resolve (pid=507)
LISTEN 0      4096       127.0.0.1:2019      0.0.0.0:*    caddy (pid=10444)
LISTEN 0      5          127.0.0.1:9999      0.0.0.0:*    python3 (pid=7134)
LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*    sshd
LISTEN 0      4096   127.0.0.53%lo:53        0.0.0.0:*    systemd-resolve (pid=507)
LISTEN 0      4096            [::]:22           [::]:*    sshd
LISTEN 0      4096               *:80              *:*    caddy
LISTEN 0      4096               *:443             *:*    caddy
```

**Nota:** proceso `python3` (pid=7134) escuchando en 127.0.0.1:9999 — no identificado, investigar en próximas sesiones.

---

## df -h /

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1       116G  2.8G  113G   3% /
```

---

## du -sh /opt/miamipreviewlab/*

```
96K   MPL_IMPLEMENTATION_PLAN.md
104K  app
4.0K  archived
20K   backups
32K   data
28K   demos
```

---

## sqlite3 .schema

```sql
CREATE TABLE demos (
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
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## sqlite3 SELECT demos

```
slug               | business_name          | category   | status
hialeahbarber      | Hialeah Barber Shop    | barberia   | contacted
miamiautodetailing | Miami Auto Detailing   | auto       | draft
brickelllawfirm    | Brickell Law Firm      | legal      | draft
brickellcafe       | Brickell Cafe          | restaurante| published
```

---

## /etc/caddy/Caddyfile

```
miamipreviewlab.com, www.miamipreviewlab.com {
    root * /opt/miamipreviewlab/app/landing
    file_server
    encode gzip
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
    }
}

admin.miamipreviewlab.com {
    reverse_proxy 127.0.0.1:9000
}

# Demo blocks - auto-generated
import /etc/caddy/demos.conf
```

---

## /etc/caddy/demos.conf

```
brickellcafe.miamipreviewlab.com {
    tls internal
    root * /opt/miamipreviewlab/demos/brickellcafe
    file_server
    encode gzip
}

hialeahbarber.miamipreviewlab.com {
    tls internal
    root * /opt/miamipreviewlab/demos/hialeahbarber
    file_server
    encode gzip
}
```

---

## /etc/systemd/system/mpl-api.service

```ini
[Unit]
Description=MiamiPreviewLab Admin API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/miamipreviewlab
Environment="PATH=/opt/miamipreviewlab/.venv/bin:/usr/bin:/bin"
Environment="MPL_ADMIN_USER=rey"
Environment="MPL_ADMIN_PASS=<REDACTED>"
ExecStart=/opt/miamipreviewlab/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 9000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Nota:** credenciales hardcodeadas en el unit y servicio corriendo como `root`. Ambos se corrigen en Bloque 3.

---

## ls -la /opt/miamipreviewlab/

```
drwxr-xr-x 8 root root  4096  app/
drwxr-xr-x   root root        .venv/
drwxr-xr-x 2 root root  4096  archived/
drwxr-xr-x 4 root root 20480  backups/
drwxr-xr-x 2 root root  4096  data/
drwxr-xr-x 6 root root  4096  demos/
-rw-r--r-- 1 root root 97717  MPL_IMPLEMENTATION_PLAN.md
```

---

## find (maxdepth 3, sin .venv/__pycache__)

```
/opt/miamipreviewlab/
/opt/miamipreviewlab/.claude/settings.local.json
/opt/miamipreviewlab/MPL_IMPLEMENTATION_PLAN.md
/opt/miamipreviewlab/app/admin.html
/opt/miamipreviewlab/app/admin/index.html
/opt/miamipreviewlab/app/landing/index.html
/opt/miamipreviewlab/app/main.py
/opt/miamipreviewlab/app/mpl-gen-caddy.sh
/opt/miamipreviewlab/app/mpl.sh
/opt/miamipreviewlab/app/notfound/index.html
/opt/miamipreviewlab/app/tls-checker.py
/opt/miamipreviewlab/archived/
/opt/miamipreviewlab/backups/brickellcafe-20260520-0303/index.html
/opt/miamipreviewlab/backups/hialeahbarber-20260520-0243/index.html
/opt/miamipreviewlab/data/.jwt_secret
/opt/miamipreviewlab/data/mpl.db
/opt/miamipreviewlab/demos/brickellcafe/index.html
/opt/miamipreviewlab/demos/brickelllawfirm/
/opt/miamipreviewlab/demos/hialeahbarber/index.html
/opt/miamipreviewlab/demos/miamiautodetailing/
```
