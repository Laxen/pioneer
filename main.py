import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from fetchers.reddit_fetcher import RedditFetcher
from llm.openai_filter import OpenAIFilter
from outputs.telegram_sender import send_results

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — edit these to match your setup
# ---------------------------------------------------------------------------

PROMPT = os.environ.get("PROMPT", "")

_subreddits_env = os.environ.get("SUBREDDITS", "")
SUBREDDITS = [s.strip() for s in _subreddits_env.split(",") if s.strip()] or []

INTERVAL_HOURS = 1

# ---------------------------------------------------------------------------


def build_fetchers() -> list[RedditFetcher]:
    return [RedditFetcher(sub, max_age_hours=INTERVAL_HOURS) for sub in SUBREDDITS]


def run_job(fetchers: list[RedditFetcher], llm: OpenAIFilter) -> None:
    all_posts: list[dict] = []
    for fetcher in fetchers:
        try:
            posts = fetcher.fetch()
            log.info("Fetched %d posts from r/%s", len(posts), fetcher.subreddit)
            all_posts.extend(posts)
        except Exception:
            log.exception("Failed to fetch r/%s", fetcher.subreddit)

    if not all_posts:
        log.info("No posts fetched, skipping LLM filter")
        return

    results = llm.filter_posts(all_posts)

    if not results:
        log.info("No relevant posts found this cycle")
    else:
        log.info("Found %d relevant posts:", len(results))
        for post in results:
            print(f"\n--- r/{post['subreddit']} ---")
            print(f"  Title: {post['title']}")
            print(f"  URL:   {post['url']}")
            print(f"  Why:   {post['reasoning']}")

    if llm.last_usage is not None:
        try:
            send_results(llm.last_usage, results, all_posts)
            log.info("Results sent to Telegram")
        except Exception:
            log.exception("Failed to send Telegram message")


def main() -> None:
    fetchers = build_fetchers()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = OpenAIFilter(user_prompt=PROMPT, model=model)

    log.info("Running initial job...")
    run_job(fetchers, llm)

    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, "interval", hours=INTERVAL_HOURS, args=[fetchers, llm])
    log.info("Scheduler started — running every hour. Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
