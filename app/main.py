import os, json, sqlite3, secrets, shutil, re, logging, subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

import jwt
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import bcrypt as _bcrypt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Config ────────────────────────────────────────────
BASE = Path("/opt/miamipreviewlab")
DB_PATH = BASE / "data" / "mpl.db"
DEMOS = BASE / "demos"
ARCHIVED = BASE / "archived"
BACKUPS = BASE / "backups"
JWT_ALG = "HS256"
JWT_EXP_HOURS = 24
SLUG_RE = re.compile(r"^[a-z0-9](-?[a-z0-9])*$")

# Logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/mpl/api.log"),
    ],
)
log = logging.getLogger("mpl.api")

# Secret (read first, generate if missing)
SECRET_FILE = BASE / "data" / ".jwt_secret"
if SECRET_FILE.exists():
    SECRET = SECRET_FILE.read_text().strip()
else:
    SECRET = secrets.token_hex(32)
    SECRET_FILE.write_text(SECRET)
    os.chmod(SECRET_FILE, 0o600)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="MiamiPreviewLab Admin", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
security = HTTPBearer(auto_error=False)

# ── DB Helpers ─────────────────────────────────────────
@contextmanager
def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.migrations.runner import run_all
    run_all(str(DB_PATH))

# ── Auth ───────────────────────────────────────────────
def create_user(username: str, password: str):
    with get_db() as db:
        pw = password.encode("utf-8")[:72]
        h = _bcrypt.hashpw(pw, _bcrypt.gensalt()).decode()
        db.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", (username, h))
        db.commit()

def verify_user(username: str, password: str) -> bool:
    with get_db() as db:
        row = db.execute("SELECT password_hash FROM users WHERE username=?", (username,)).fetchone()
        if not row:
            return False
        pw = password.encode("utf-8")[:72]
        return _bcrypt.checkpw(pw, row["password_hash"].encode())

def create_token(username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS)
    return jwt.encode({"sub": username, "exp": exp}, SECRET, algorithm=JWT_ALG)

def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not creds:
        raise HTTPException(401, detail="Token required")
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=[JWT_ALG])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, detail="Invalid token")

def valid_slug(slug: str) -> str:
    if not SLUG_RE.match(slug) or len(slug) > 63:
        raise HTTPException(400, "Invalid slug")
    return slug

# ── Pydantic Models ────────────────────────────────────
class DemoCreate(BaseModel):
    slug: str
    business_name: str
    category: Optional[str] = ""

class DemoUpdate(BaseModel):
    business_name: Optional[str] = None
    category: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None

class NoteAdd(BaseModel):
    note: str

# ── Auth Endpoints ─────────────────────────────────────
@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not verify_user(username, password):
        raise HTTPException(401, detail="Invalid credentials")
    token = create_token(username)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def me(user: str = Depends(get_current_user)):
    return {"username": user}

# ── Demo Endpoints ─────────────────────────────────────
@app.get("/api/demos")
async def list_demos(status: Optional[str] = None, user: str = Depends(get_current_user)):
    with get_db() as db:
        if status:
            rows = db.execute("SELECT * FROM demos WHERE status=? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM demos ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

@app.get("/api/demos/{slug}")
async def get_demo(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute("SELECT * FROM demos WHERE slug=?", (slug,)).fetchone()
        if not row:
            raise HTTPException(404, detail="Demo not found")
        demo = dict(row)
        demo_path = DEMOS / slug
        demo["files"] = [f.name for f in demo_path.iterdir()] if demo_path.exists() else []
        demo["is_archived"] = (ARCHIVED / slug).exists()
        return demo

@app.post("/api/demos")
async def create_demo(data: DemoCreate, user: str = Depends(get_current_user)):
    slug = data.slug.strip().lower().replace(" ", "-")
    if not SLUG_RE.match(slug) or len(slug) > 63:
        raise HTTPException(400, detail="Invalid slug (use a-z, 0-9, hyphen)")
    demo_path = DEMOS / slug
    demo_path.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        try:
            db.execute(
                "INSERT INTO demos (slug, business_name, category, subdomain, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (slug, data.business_name, data.category, f"{slug}.miamipreviewlab.com", now, now)
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, detail="Demo slug already exists")
    _regen_caddy()
    return {"status": "created", "slug": slug, "url": f"https://{slug}.miamipreviewlab.com"}

@app.put("/api/demos/{slug}")
async def update_demo(data: DemoUpdate, slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, detail="Nothing to update")
    updates["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [slug]
    with get_db() as db:
        db.execute(f"UPDATE demos SET {set_clause} WHERE slug=?", values)
        db.commit()
    return {"status": "updated"}

@app.post("/api/demos/{slug}/publish")
async def publish_demo(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    demo_path = DEMOS / slug
    if not demo_path.exists():
        raise HTTPException(404, detail="Demo folder not found")
    if not (demo_path / "index.html").exists():
        raise HTTPException(400, detail="No index.html in demo")
    _regen_caddy()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        db.execute("UPDATE demos SET status='published', updated_at=? WHERE slug=?", (now, slug))
        db.commit()
    return {"status": "published", "url": f"https://{slug}.miamipreviewlab.com"}

@app.post("/api/demos/{slug}/archive")
async def archive_demo(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    src = DEMOS / slug
    if not src.exists():
        raise HTTPException(404, detail="Demo not found")
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    backup_path = BACKUPS / f"{slug}-{ts}"
    backup_path.mkdir(parents=True, exist_ok=True)
    if (src / "index.html").exists():
        shutil.copytree(str(src), str(backup_path), dirs_exist_ok=True)
    shutil.move(str(src), str(ARCHIVED / slug))
    _regen_caddy()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        db.execute("UPDATE demos SET status='archived', updated_at=? WHERE slug=?", (now, slug))
        db.commit()
    return {"status": "archived"}

@app.post("/api/demos/{slug}/restore")
async def restore_demo(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    src = ARCHIVED / slug
    if not src.exists():
        raise HTTPException(400, detail="Demo not in archive")
    shutil.move(str(src), str(DEMOS / slug))
    _regen_caddy()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        db.execute("UPDATE demos SET status='draft', updated_at=? WHERE slug=?", (now, slug))
        db.commit()
    return {"status": "restored"}

@app.delete("/api/demos/{slug}")
async def delete_demo(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    for p in [DEMOS / slug, ARCHIVED / slug]:
        if p.exists():
            shutil.rmtree(str(p))
    _regen_caddy()
    with get_db() as db:
        db.execute("DELETE FROM demos WHERE slug=?", (slug,))
        db.commit()
    return {"status": "deleted"}

@app.post("/api/demos/{slug}/notes")
async def add_note(data: NoteAdd, slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    note_line = f"{datetime.utcnow().strftime('%Y-%m-%d')}: {data.note}"
    with get_db() as db:
        row = db.execute("SELECT notes FROM demos WHERE slug=?", (slug,)).fetchone()
        if not row:
            raise HTTPException(404, detail="Demo not found")
        existing = row["notes"] or ""
        new_notes = f"{existing}\n{note_line}" if existing else note_line
        db.execute("UPDATE demos SET notes=?, updated_at=? WHERE slug=?", (new_notes, now, slug))
        db.commit()
    return {"status": "noted"}

@app.post("/api/demos/{slug}/contacted")
async def mark_contacted(slug: str = Depends(valid_slug), user: str = Depends(get_current_user)):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        db.execute("UPDATE demos SET status='contacted', contacted_at=?, updated_at=? WHERE slug=?",
                   (now, now, slug))
        db.commit()
    return {"status": "contacted"}

@app.post("/api/demos/{slug}/responded")
async def mark_responded(slug: str = Depends(valid_slug), response: str = Form(...), user: str = Depends(get_current_user)):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        db.execute("UPDATE demos SET status='responded', response=?, updated_at=? WHERE slug=?",
                   (response, now, slug))
        db.commit()
    return {"status": "responded"}

# ── Caddy Config Generator ────────────────────────────
def _regen_caddy():
    conf = ""
    for d in sorted(DEMOS.iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            slug = d.name
            conf += f"""{slug}.miamipreviewlab.com {{
    tls internal
    root * /opt/miamipreviewlab/demos/{slug}
    file_server
    encode gzip
}}

"""
    dest = Path("/etc/caddy/demos.conf")
    dest.write_text(conf)
    result = subprocess.run(
        ["systemctl", "reload", "caddy"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        log.warning(f"caddy reload failed: {result.stderr.strip()}")

# ── Admin Panel HTML ──────────────────────────────────
ADMIN_HTML_PATH = BASE / "app" / "admin.html"

@app.get("/", response_class=HTMLResponse)
async def admin_panel():
    if ADMIN_HTML_PATH.exists():
        return HTMLResponse(ADMIN_HTML_PATH.read_text())
    return HTMLResponse("<h1>Admin not found</h1>")

init_db()
USERNAME = os.environ.get("MPL_ADMIN_USER", "rey")
PASSWORD = os.environ.get("MPL_ADMIN_PASS", "")
create_user(USERNAME, PASSWORD)
log.info(f"Admin user ready: {USERNAME}")
