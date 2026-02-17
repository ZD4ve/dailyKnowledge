import os
import math
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

from config import get_preference
from helper import extract_site_from


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


class RelevanceScore(BaseModel):
    score: int = Field(ge=0, le=9, description="Relevance score from 0 to 9")


def estimate(article: dict) -> int | None:
    """Send an article to the AI and return a relevance score (0-9) via structured output."""

    #retrive preference for the article's source URL
    preference = get_preference(extract_site_from(article.get("url", "")))
    if preference is None:
        return None

    system_msg = (
        "You are a relevance scorer. The reader has specific interests. "
        "You will receive their interests and an article. "
        "Rate how useful this article is to the reader from 0 to 9. "
        "0 = completely irrelevant. "
        "1 = mostly irrelevant but has a tiny bit of connection. "
        "3 = somewhat relevant but not a great match. "
        "5 = somewhat relevant and somewhat interesting. "
        "7 = relevant and interesting, but not perfect. "
        "9 = exactly what they want.\n\n"
        "Examples:\n"
        "Interest: 'Global economy, stock markets'\n"
        "Title: 'S&P 500 hits record high amid tech rally'\n"
        "Score: 8\n\n"
        "Interest: 'Global economy, stock markets'\n"
        "Title: 'New cat breed wins pet show'\n"
        "Score: 0\n\n"
        "Interest: 'Local politics, national news'\n"
        "Title: 'Parliament passes new education reform'\n"
        "Score: 7"
    )

    user_msg = (
        f"Reader interest: '{preference or 'general news'}'\n\n"
        f"Title: {article.get('title', '')}\n\n"
        f"Text: {article.get('text', '')}"
    )

    response = client.chat.completions.create(
        model="arcee-ai/trinity-mini:free",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "relevance_score",
                "strict": True,
                "schema": RelevanceScore.model_json_schema(),
            },
        },
        timeout=70,
    )

    try:
        raw = response.choices[0].message.content
        if not raw:
            return None
        parsed = json.loads(raw)
        return int(parsed["score"])
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
