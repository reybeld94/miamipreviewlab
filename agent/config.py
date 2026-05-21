import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path("/opt/miamipreviewlab")
load_dotenv(BASE / "data" / ".env")

DB_PATH      = BASE / "data" / "mpl.db"
CONTEXT_DIR  = BASE / "data" / "context"
LOG_DIR      = Path("/var/log/mpl")
SCORING_DIR  = BASE / "agent" / "scoring"
CONFIG_DIR   = BASE / "agent" / "config"

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_PLACES_KEY  = os.getenv("GOOGLE_PLACES_KEY", "")
YELP_API_KEY       = os.getenv("YELP_API_KEY", "")
APIFY_TOKEN        = os.getenv("APIFY_TOKEN", "")
DAILY_BUDGET_USD   = float(os.getenv("MPL_DAILY_BUDGET_USD", "1.0"))

HAIKU_MODEL = "claude-haiku-4-5-20251001"
USER_AGENT  = "MiamiPreviewLabBot/0.1 (+https://miamipreviewlab.com/bot)"
