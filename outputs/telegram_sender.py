import asyncio
import os
from html import escape

from telegram import Bot
from telegram.constants import ParseMode


def _format_message(usage, relevant_posts: list[dict], all_posts: list[dict]) -> str:
    lines = []

    # Token consumption
    lines.append(
        f"<code>input: {usage.prompt_tokens}  output: {usage.completion_tokens}  total: {usage.total_tokens}</code>"
    )
    lines.append("")

    # LLM response (relevant posts)
    if relevant_posts:
        for post in relevant_posts:
            lines.append(f"<b>r/{escape(post['subreddit'])}</b>")
            lines.append(f'<a href="{escape(post["url"])}">{escape(post["title"])}</a>')
            lines.append(f"💬 <i>{escape(post['reasoning'])}</i>")
            lines.append("")
    else:
        lines.append("<i>No relevant posts found this cycle.</i>")
        lines.append("")

    lines.append("—————————————————")
    lines.append("<b>All posts sent to LLM</b>")
    lines.append("")

    # All titles + links sent to the LLM, grouped by subreddit
    grouped: dict[str, list[dict]] = {}
    for post in all_posts:
        grouped.setdefault(post["subreddit"], []).append(post)
    for subreddit, posts in grouped.items():
        lines.append(f"<b>r/{escape(subreddit)}</b>")
        for post in posts:
            lines.append(f'• <a href="{escape(post["url"])}">{escape(post["title"])}</a>')
        lines.append("")

    return "\n".join(lines)


async def _send(token: str, chat_id: str, text: str) -> None:
    bot = Bot(token=token)
    async with bot:
        # Telegram caps messages at 4096 chars
        for chunk_start in range(0, len(text), 4096):
            await bot.send_message(
                chat_id=chat_id,
                text=text[chunk_start:chunk_start + 4096],
                parse_mode=ParseMode.HTML,
            )


def send_results(usage, relevant_posts: list[dict], all_posts: list[dict]) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    message = _format_message(usage, relevant_posts, all_posts)
    asyncio.run(_send(token, chat_id, message))
