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
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_touchpoints_next ON touchpoints(next_action_at) "
        "WHERE next_action_at IS NOT NULL"
    )

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

    cols = {r[1] for r in db.execute("PRAGMA table_info(demos)").fetchall()}
    if "prospect_id" not in cols:
        db.execute("ALTER TABLE demos ADD COLUMN prospect_id INTEGER REFERENCES prospects(id)")
