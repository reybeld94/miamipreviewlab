import sqlite3, json, logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ── Constants (no circular import — read after main.py sets up the secret file) ──
BASE = Path("/opt/miamipreviewlab")
DB_PATH = BASE / "data" / "mpl.db"
_SECRET_FILE = BASE / "data" / ".jwt_secret"
_JWT_ALG = "HS256"

_security = HTTPBearer(auto_error=False)
log = logging.getLogger("mpl.api.prospects")


@contextmanager
def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_security),
):
    if not creds:
        raise HTTPException(401, "Token required")
    secret = _SECRET_FILE.read_text().strip() if _SECRET_FILE.exists() else ""
    try:
        payload = jwt.decode(creds.credentials, secret, algorithms=[_JWT_ALG])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ── Status transition rules ────────────────────────────────────────────────────
VALID_TRANSITIONS: dict[str, set[str]] = {
    "discovered":  {"reviewed", "shortlisted", "blacklisted"},
    "reviewed":    {"shortlisted", "rejected", "blacklisted"},
    "shortlisted": {"demo_built", "rejected", "blacklisted"},
    "demo_built":  {"contacted"},
    "contacted":   {"responded", "no_response"},
    "responded":   {"won", "lost"},
}


# ── Pydantic models ────────────────────────────────────────────────────────────
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
    source: str
    source_external_id: Optional[str] = None
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
    evidence_json: Optional[str] = None
    score_breakdown_json: Optional[str] = None
    proposed_value: Optional[str] = None
    context_collected_at: Optional[str] = None
    created_at: Optional[str] = None


class ProspectPatch(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class BlacklistRequest(BaseModel):
    reason: str = ""


class TouchpointCreate(BaseModel):
    channel: str  # walk_in | whatsapp | instagram_dm | email | call
    direction: str  # outbound | inbound
    summary: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None
    actor: Optional[str] = None


class TouchpointOut(BaseModel):
    id: int
    prospect_id: int
    occurred_at: str
    channel: str
    direction: str
    summary: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None
    actor: Optional[str] = None
    created_at: str


class ResearchRunOut(BaseModel):
    id: int
    started_at: str
    finished_at: Optional[str] = None
    vertical: str
    geo: str
    candidates_seen: int = 0
    candidates_kept: int = 0
    new_prospects: int = 0
    updated_prospects: int = 0
    api_cost_usd: float = 0
    tokens_in: int = 0
    tokens_out: int = 0
    errors_json: Optional[str] = None
    status: Optional[str] = None
    log_path: Optional[str] = None


class MetricsDailyOut(BaseModel):
    day: str
    prospects_new: int = 0
    prospects_shortlisted: int = 0
    demos_built: int = 0
    demos_shown: int = 0
    closes: int = 0
    revenue_usd: float = 0
    api_spend_usd: float = 0


# ── Router ─────────────────────────────────────────────────────────────────────
router = APIRouter(tags=["prospects"])


def _get_prospect_or_404(prospect_id: int) -> dict:
    with get_db() as db:
        row = db.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Prospect not found")
    return dict(row)


# ── Prospects ──────────────────────────────────────────────────────────────────
@router.get("/api/prospects", response_model=list[ProspectOut])
async def list_prospects(
    vertical: Optional[str] = None,
    status: Optional[str] = None,
    score_min: Optional[int] = Query(default=None, ge=0, le=100),
    city: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    order_by: str = Query(default="score_desc", pattern="^(score_desc|score_asc|discovered_desc|updated_desc)$"),
    _user: str = Depends(get_current_user),
):
    conditions, params = [], []
    if vertical:
        conditions.append("vertical = ?"); params.append(vertical)
    if status:
        conditions.append("status = ?"); params.append(status)
    if score_min is not None:
        conditions.append("opportunity_score >= ?"); params.append(score_min)
    if city:
        conditions.append("lower(city) = lower(?)"); params.append(city)
    if assigned_to:
        conditions.append("assigned_to = ?"); params.append(assigned_to)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_map = {
        "score_desc":      "opportunity_score DESC",
        "score_asc":       "opportunity_score ASC",
        "discovered_desc": "discovered_at DESC",
        "updated_desc":    "updated_at DESC",
    }
    order_sql = order_map[order_by]
    sql = f"SELECT * FROM prospects {where} ORDER BY {order_sql} LIMIT ? OFFSET ?"
    params += [limit, offset]

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
    return [ProspectOut.model_validate(dict(r)) for r in rows]


@router.get("/api/prospects/{prospect_id}", response_model=ProspectDetail)
async def get_prospect(
    prospect_id: int,
    _user: str = Depends(get_current_user),
):
    return ProspectDetail.model_validate(_get_prospect_or_404(prospect_id))


@router.patch("/api/prospects/{prospect_id}", response_model=ProspectDetail)
async def patch_prospect(
    prospect_id: int,
    data: ProspectPatch,
    _user: str = Depends(get_current_user),
):
    current = _get_prospect_or_404(prospect_id)

    updates: dict = {}
    if data.status is not None:
        allowed = VALID_TRANSITIONS.get(current["status"], set())
        if data.status not in allowed:
            raise HTTPException(
                400,
                f"Cannot transition '{current['status']}' → '{data.status}'. "
                f"Allowed: {sorted(allowed) or 'none'}",
            )
        updates["status"] = data.status
    if data.assigned_to is not None:
        updates["assigned_to"] = data.assigned_to
    if data.notes is not None:
        updates["notes"] = data.notes

    if not updates:
        return ProspectDetail.model_validate(current)

    updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [prospect_id]
    with get_db() as db:
        db.execute(f"UPDATE prospects SET {set_clause} WHERE id=?", vals)
        db.commit()

    return ProspectDetail.model_validate(_get_prospect_or_404(prospect_id))


@router.post("/api/prospects/{prospect_id}/blacklist")
async def blacklist_prospect(
    prospect_id: int,
    body: BlacklistRequest,
    _user: str = Depends(get_current_user),
):
    current = _get_prospect_or_404(prospect_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    note_line = f"{now[:10]}: Blacklisted. {body.reason}".strip().rstrip(".")  + "."
    existing_notes = current.get("notes") or ""
    new_notes = f"{existing_notes}\n{note_line}".strip()
    with get_db() as db:
        db.execute(
            "UPDATE prospects SET status='blacklisted', notes=?, updated_at=? WHERE id=?",
            (new_notes, now, prospect_id),
        )
        db.commit()
    return {"status": "blacklisted", "id": prospect_id}


# ── Touchpoints ────────────────────────────────────────────────────────────────
@router.post("/api/prospects/{prospect_id}/touchpoints", response_model=TouchpointOut)
async def add_touchpoint(
    prospect_id: int,
    data: TouchpointCreate,
    _user: str = Depends(get_current_user),
):
    _get_prospect_or_404(prospect_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO touchpoints
               (prospect_id, occurred_at, channel, direction, summary, outcome, next_action, next_action_at, actor)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prospect_id, now,
                data.channel, data.direction,
                data.summary, data.outcome,
                data.next_action, data.next_action_at,
                data.actor,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM touchpoints WHERE id=?", (cur.lastrowid,)).fetchone()
    return TouchpointOut.model_validate(dict(row))


@router.get("/api/prospects/{prospect_id}/touchpoints", response_model=list[TouchpointOut])
async def list_touchpoints(
    prospect_id: int,
    _user: str = Depends(get_current_user),
):
    _get_prospect_or_404(prospect_id)
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM touchpoints WHERE prospect_id=? ORDER BY occurred_at DESC",
            (prospect_id,),
        ).fetchall()
    return [TouchpointOut.model_validate(dict(r)) for r in rows]


# ── Research runs ──────────────────────────────────────────────────────────────
@router.get("/api/research_runs", response_model=list[ResearchRunOut])
async def list_research_runs(
    limit: int = Query(default=20, ge=1, le=100),
    _user: str = Depends(get_current_user),
):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM research_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [ResearchRunOut.model_validate(dict(r)) for r in rows]


@router.get("/api/research_runs/{run_id}", response_model=ResearchRunOut)
async def get_research_run(
    run_id: int,
    _user: str = Depends(get_current_user),
):
    with get_db() as db:
        row = db.execute("SELECT * FROM research_runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Run not found")
    return ResearchRunOut.model_validate(dict(row))


# ── Metrics ────────────────────────────────────────────────────────────────────
@router.get("/api/metrics/daily", response_model=list[MetricsDailyOut])
async def metrics_daily(
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date: Optional[str] = Query(default=None, alias="to"),
    _user: str = Depends(get_current_user),
):
    conditions, params = [], []
    if from_date:
        conditions.append("day >= ?"); params.append(from_date)
    if to_date:
        conditions.append("day <= ?"); params.append(to_date)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as db:
        rows = db.execute(f"SELECT * FROM metrics_daily {where} ORDER BY day", params).fetchall()
    return [MetricsDailyOut.model_validate(dict(r)) for r in rows]


@router.get("/api/metrics/funnel")
async def metrics_funnel(_user: str = Depends(get_current_user)):
    statuses = [
        "discovered", "reviewed", "shortlisted", "demo_built",
        "contacted", "responded", "no_response", "won", "lost",
        "rejected", "blacklisted",
    ]
    with get_db() as db:
        rows = db.execute(
            "SELECT status, COUNT(*) as count FROM prospects GROUP BY status"
        ).fetchall()
    counts = {r["status"]: r["count"] for r in rows}
    return {s: counts.get(s, 0) for s in statuses}
