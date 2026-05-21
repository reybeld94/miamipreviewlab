import sqlite3
import importlib
import pkgutil


def run_all(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')))"
    )
    applied = {r[0] for r in db.execute("SELECT name FROM schema_migrations").fetchall()}
    import app.migrations as mig_pkg
    for _, name, _ in sorted(pkgutil.iter_modules(mig_pkg.__path__)):
        if name == "runner":
            continue
        if name in applied:
            continue
        mod = importlib.import_module(f"app.migrations.{name}")
        print(f"[migrations] Applying {name}")
        mod.up(db)
        db.execute("INSERT INTO schema_migrations(name) VALUES (?)", (name,))
        db.commit()
    db.close()
