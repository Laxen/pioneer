import json
import logging

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a post relevance filter. Given a user's prompt and a list of posts, \
return only the posts that are STRICTLY relevant to the user's prompt. If \
a post's relevance is questionable, don't return it.

Respond with a JSON array of objects for relevant posts only. Each object must have:
- "index": the 0-based index of the post
- "reasoning": a one-sentence explanation of why this post is relevant

Respond ONLY with the JSON array, no markdown fences or extra text."""


class OpenAIFilter:
    def __init__(self, user_prompt: str, model: str = "gpt-4o-mini"):
        self.user_prompt = user_prompt
        self.model = model
        self.client = OpenAI()  # uses OPENAI_API_KEY env var
        self.last_usage = None

    def filter_posts(self, posts: list[dict]) -> list[dict]:
        if not posts:
            return []

        post_list = "\n".join(
            f"[{i}] {p['title']}" for i, p in enumerate(posts)
        )
        user_msg = (
            f"User prompt:\n{self.user_prompt}\n\n"
            f"Posts:\n{post_list}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = response.choices[0].message.content.strip()
            assessments = json.loads(raw)
            usage = response.usage
            self.last_usage = usage
            print(
                f"Tokens — input: {usage.prompt_tokens}, "
                f"output: {usage.completion_tokens}, "
                f"total: {usage.total_tokens}"
            )
        except Exception:
            log.exception("LLM filtering failed")
            return []

        results = []
        for a in assessments:
            idx = a["index"]
            if 0 <= idx < len(posts):
                post = posts[idx].copy()
                post["reasoning"] = a["reasoning"]
                results.append(post)
        return results
