def up(db):
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
    cols = {r[1] for r in db.execute("PRAGMA table_info(demos)").fetchall()}
    if "outcome" not in cols:
        db.execute("ALTER TABLE demos ADD COLUMN outcome TEXT")
