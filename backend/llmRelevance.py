import os
import asyncio
import json
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from config import get_preference, get_language
from helper import dataArticle

# region SETUP
load_dotenv()
BASE_URL: str = os.getenv("OPENAI_API_BASE") # pyright: ignore[reportAssignmentType]
MODEL: str = os.getenv("OPENAI_MODEL") # pyright: ignore[reportAssignmentType]
API_KEY: str = os.getenv("OPENAI_API_KEY")# pyright: ignore[reportAssignmentType]
RATE_LIMIT: int = int(os.getenv("OPENAI_RATE_LIMIT", "10")) # pyright: ignore[reportAssignmentType]

if BASE_URL is None or MODEL is None or API_KEY is None:
    raise ValueError("Missing required environment variables (OPENAI_API_BASE, OPENAI_MODEL, OPENAI_API_KEY). Please check your .env file or environment configuration.")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
async_client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)


#region COMMON
class RelevanceScore(BaseModel):
    summary: str = Field(description="2-3 sentence summary adding information not already in the title")
    score: int = Field(ge=0, le=9, description="Relevance score from 0 to 9")

def _build_messages(article: dataArticle) -> tuple[list[ChatCompletionMessageParam], str | None]:
    """Build the messages list for the API call. Returns (messages, preference) or ([], None) if skipped."""
    preference = get_preference(article.site_name)
    if preference is None:
        return [], None

    language = get_language(article.site_name) or "English"

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
        f"Title: {article.title}\n\n"
        f"Text: {article.text}"
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    return messages, preference

# region ASYNC
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
_default_rate_limiter = AsyncRateLimiter(RATE_LIMIT)

async def async_estimate(
    article: dataArticle,
    rate_limiter: AsyncRateLimiter = _default_rate_limiter,
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
    