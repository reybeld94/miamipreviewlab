from datetime import date
from agent.db import get_db
from agent.config import DAILY_BUDGET_USD


class BudgetExceeded(Exception):
    pass


def spent_today() -> float:
    today = date.today().isoformat()
    with get_db() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(api_cost_usd), 0) FROM research_runs WHERE date(started_at) = ?",
            (today,),
        ).fetchone()
        return float(row[0])


def remaining_today() -> float:
    return max(0.0, DAILY_BUDGET_USD - spent_today())


def check_can_spend(usd: float) -> None:
    total = spent_today() + usd
    if total > DAILY_BUDGET_USD:
        raise BudgetExceeded(
            f"Spend ${usd:.4f} would exceed daily budget "
            f"(spent=${spent_today():.4f}, limit=${DAILY_BUDGET_USD:.2f})"
        )


def record_spend(run_id: int, usd: float, tokens_in: int = 0, tokens_out: int = 0) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE research_runs SET api_cost_usd = COALESCE(api_cost_usd,0) + ?, "
            "tokens_in = COALESCE(tokens_in,0) + ?, tokens_out = COALESCE(tokens_out,0) + ? "
            "WHERE id = ?",
            (usd, tokens_in, tokens_out, run_id),
        )
        db.commit()
