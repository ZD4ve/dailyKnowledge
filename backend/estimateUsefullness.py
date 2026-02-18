import os
import math
import asyncio
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

from config import get_preference, get_language




load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

#model should support response_format
MODEL = "arcee-ai/trinity-large-preview:free"


class RelevanceScore(BaseModel):
    summary: str = Field(description="2-3 sentence summary adding information not already in the title")
    score: int = Field(ge=0, le=9, description="Relevance score from 0 to 9")


def estimate(article: dict) -> tuple[int, str] | None:
    """Send an article to the AI and return a (score, summary) tuple or None."""
    messages, preference = _build_messages(article)
    if not messages:
        return None

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "relevance_score",
                "strict": True,
                "schema": RelevanceScore.model_json_schema(),
            },
        },
    )

    try:
        raw = response.choices[0].message.content
        if not raw:
            return None
        parsed = json.loads(raw)
        return int(parsed["score"]), parsed["summary"]
    except (KeyError, json.JSONDecodeError, TypeError):
        return None


def _build_messages(article: dict) -> tuple[list[ChatCompletionMessageParam], str | None]:
    """Build the messages list for the API call. Returns (messages, preference) or ([], None) if skipped."""
    preference = get_preference(article.get("site_name", ""))
    if preference is None:
        return [], None

    language = get_language(article.get("site_name", "")) or "English"

    system_msg = (
        "You are a strict relevance scorer and summarizer. "
        "You will receive the reader's interests and an article. "
        f"CRITICAL RULE: The summary MUST be written entirely in {language}. "
        f"Every word of the summary must be in {language} — no exceptions, no English unless the article is in English. "
        "Write a short summary (2-3 sentences) that captures the most important information in the article. "
        "Focus on details NOT already obvious from the title. Do not repeat the title. "
        "Then rate how useful this article is to the reader from 0 to 9.\n\n"
        "Scoring guide — most articles should score between 1 and 5:\n"
        "0 = no connection at all to the reader's interests\n"
        "1 = tangentially related topic, but not what the reader is looking for\n"
        "2 = loosely related, shares a broad category but lacks focus\n"
        "3 = related topic, but generic or surface-level coverage\n"
        "4 = relevant topic with some useful detail\n"
        "5 = clearly relevant, provides meaningful information the reader would appreciate\n"
        "6 = highly relevant with substantial, specific insight\n"
        "7 = very strong match, directly addresses the reader's core interests with depth\n"
        "8 = exceptional match, must-read for someone with these interests\n"
        "9 = perfect match, reserved for rare articles that are exactly what the reader wants\n\n"
        "Important: a score of 5 already means 'good match'. "
        "Scores above 6 should be uncommon. Reserve 8-9 for outstanding articles.\n\n"
        "Examples:\n"
        "Interest: 'Global economy, stock markets'\n"
        "Title: 'S&P 500 hits record high amid tech rally'\n"
        "Score: 6\n\n"
        "Interest: 'Global economy, stock markets'\n"
        "Title: 'Central bank raises rates, economists debate recession risk'\n"
        "Score: 7\n\n"
        "Interest: 'Global economy, stock markets'\n"
        "Title: 'Oil prices rise slightly on supply concerns'\n"
        "Score: 3\n\n"
        "Interest: 'Local politics, national news'\n"
        "Title: 'Parliament passes new education reform'\n"
        "Score: 5\n\n"
        "Interest: 'Local politics, national news'\n"
        "Title: 'Celebrity chef opens new restaurant in capital'\n"
        "Score: 1"
    )

    user_msg = (
        f"Reader interest: '{preference}'\n\n"
        f"Title: {article.get('title', '')}\n\n"
        f"Text: {article.get('text', '')}"
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    return messages, preference


class AsyncRateLimiter:
    """Enforces a minimum delay between requests using an async lock. (requests per minute)"""

    def __init__(self, rate_limit: int):
        self._delay = 60.0 / rate_limit
        self._lock = asyncio.Lock()
        self._last_request: float = 0

    async def acquire(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait = self._delay - (now - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = asyncio.get_event_loop().time()


async def async_estimate(
    article: dict,
    rate_limiter: AsyncRateLimiter,
) -> tuple[int, str] | None:
    """Async version of estimate(). Respects rate limiting via the shared rate_limiter."""
    messages, preference = _build_messages(article)
    if not messages:
        return None

    await rate_limiter.acquire()

    response = await async_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "relevance_score",
                "strict": True,
                "schema": RelevanceScore.model_json_schema(),
            },
        },
    )

    try:
        raw = response.choices[0].message.content
        if not raw:
            return None
        parsed = json.loads(raw)
        return int(parsed["score"]), parsed["summary"]
    except (KeyError, json.JSONDecodeError, TypeError):
        return None

# --- Logprobs-based implementation (commented out) ---
# def estimate(article: dict) -> float | None:
#     """Send an article to the AI and return the weighted average of the three most probable digits."""
#
#     #retrive preference for the article's source URL
#     preference = get_preference(extract_site_from(article.get("url", "")))
#
#     system_msg = (
#         "You are a relevance scorer. The reader has specific interests. "
#         "You will receive their interests and an article. "
#         "Rate how useful this article is to the reader from 0 to 9. "
#         "0 = completely irrelevant. 9 = exactly what they want. "
#         "Reply with ONLY a single digit, nothing else.\n\n"
#         "Examples:\n"
#         "Interest: 'Global economy, stock markets'\n"
#         "Title: 'S&P 500 hits record high amid tech rally'\n"
#         "Score: 8\n\n"
#         "Interest: 'Global economy, stock markets'\n"
#         "Title: 'New cat breed wins pet show'\n"
#         "Score: 0\n\n"
#         "Interest: 'Local politics, national news'\n"
#         "Title: 'Parliament passes new education reform'\n"
#         "Score: 7"
#     )
#
#     user_msg = (
#         f"Reader interest: '{preference or 'general news'}'\n\n"
#         f"Title: {article.get('title', '')}\n\n"
#         f"Text: {article.get('text', '')}"
#     )
#
#     response = client.chat.completions.create(
#         model="arcee-ai/trinity-large-preview:free",
#         messages=[
#             {"role": "system", "content": system_msg},
#             {"role": "user", "content": user_msg},
#         ],
#         max_tokens=1,
#         logprobs=True,
#         top_logprobs=50,
#     )
#
#     top_logprobs = response.choices[0].logprobs.content[0].top_logprobs
#
#     # Keep only single-digit tokens, sorted by probability descending
#     digits = sorted(
#         [lp for lp in top_logprobs if lp.token.strip() in set("0123456789")],
#         key=lambda lp: lp.logprob,
#         reverse=True,
#     )
#     if not digits:
#         return None
#
#     # Take top 3 (or fewer if not enough digits found)
#     top3 = digits[:3]
#     probs = [math.exp(lp.logprob) for lp in top3]
#     values = [int(lp.token.strip()) for lp in top3]
#     total = sum(probs)
#
#     return sum(v * p for v, p in zip(values, probs)) / total
