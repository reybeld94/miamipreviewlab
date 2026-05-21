import argparse
from agent.logger import get_logger
from agent.budget_guard import spent_today, remaining_today, BudgetExceeded
from agent.config import DAILY_BUDGET_USD


def main() -> None:
    parser = argparse.ArgumentParser(description="MPL Research Agent")
    parser.add_argument("--dry-run",  action="store_true", help="Log and exit, no API calls")
    parser.add_argument("--vertical", default="belleza",   help="Vertical to research")
    parser.add_argument("--geo",      default="hialeah",   help="Geo to search")
    parser.add_argument("--phase",    default="all",
                        choices=["all", "discovery", "enrich1", "enrich2", "score", "brief"],
                        help="Run only a specific phase")
    args = parser.parse_args()

    log = get_logger("mpl.agent.orchestrator")
    log.info("=" * 60)
    log.info(f"MPL Agent start | vertical={args.vertical} geo={args.geo} phase={args.phase} dry_run={args.dry_run}")
    log.info(f"Budget today: spent=${spent_today():.4f} | remaining=${remaining_today():.4f} | limit=${DAILY_BUDGET_USD:.2f}")
    log.info("=" * 60)

    if args.dry_run:
        log.info("Dry run — stopping here. No API calls made.")
        return

    log.info("Skills not implemented yet — coming in Bloques 9–14.")


if __name__ == "__main__":
    main()
