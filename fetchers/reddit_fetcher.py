import subprocess
import time
from abc import ABC, abstractmethod
from calendar import timegm

import feedparser


class Fetcher(ABC):
    """Base class for all fetchers. Subclass this to add new data sources."""

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return a list of posts, each a dict with keys: title, url, description."""
        ...


class RedditFetcher(Fetcher):
    def __init__(self, subreddit: str, max_age_hours: float = 1, max_posts: int = 25):
        self.subreddit = subreddit
        self.max_age_hours = max_age_hours
        self.max_posts = max_posts
        self.feed_url = f"https://www.reddit.com/r/{subreddit}/new.rss"

    def fetch(self) -> list[dict]:
        result = subprocess.run(
            [
                "curl", "-s", "-f", "--max-time", "30",
                "-A", "Mozilla/5.0 (compatible; pioneer/1.0; +https://github.com)",
                self.feed_url,
            ],
            capture_output=True,
            timeout=35,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"curl failed ({result.returncode}): {result.stderr.decode(errors='replace')}"
            )
        feed = feedparser.parse(result.stdout)
        cutoff = time.time() - self.max_age_hours * 3600
        posts = []
        for entry in feed.entries[: self.max_posts]:
            published = entry.get("published_parsed")
            if published and timegm(published) < cutoff:
                continue
            posts.append(
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "description": entry.get("summary", ""),
                    "subreddit": self.subreddit,
                }
            )
        return posts
