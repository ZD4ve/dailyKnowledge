# dailyKnowledge

A self-hosted news aggregator that scrapes articles from configurable sources, scores their relevance using an LLM, and presents them in a clean web dashboard — sorted by what matters most to you.

**Stack:** FastAPI · React/TypeScript · PostgreSQL · Newspaper4k · OpenAI-compatible LLM · Docker Compose

---

## How It Works

1. The backend periodically scrapes configured news sources (via RSS or crawling).
2. Each article is sent to an LLM that scores its relevance (0–9) based on per-source preference prompts you define.
3. The React frontend displays articles grouped by category, sorted by relevance score.

---

## Configuration — `backend/sources.yaml`

This is the single file that controls what gets scraped, how it's filtered, and how relevance is judged. It has the following structure:

```yaml
categories:
  - name: "Category Name"
    sources:
      - name: "Source Name"
        url: "example.com"
        rss:
          - "https://example.com/feed.xml"
        preference: "Natural-language prompt describing what articles matter to you from this source."
        language: "English"
        filter:
          - "keyword"
```

### Top-level

| Key          | Description                                             |
| ------------ | ------------------------------------------------------- |
| `categories` | List of category objects. Each category groups sources that appear together in the frontend. |

### Category object

| Key       | Required | Description                                      |
| --------- | -------- | ------------------------------------------------ |
| `name`    | yes      | Display name shown as a tab in the frontend.     |
| `sources` | yes      | List of source objects belonging to this category.|

### Source object

| Key          | Required | Description |
| ------------ | -------- | ----------- |
| `name`       | yes      | Unique identifier for the source (used internally and in the DB). |
| `url`        | yes      | Base domain of the site (without `https://`). Used for crawling when no RSS is provided, and as a default URL filter. |
| `rss`        | no       | List of RSS feed URLs. When provided, these feeds are used instead of crawling the site. RSS sources are polled every 10 minutes; crawled sources every 60 minutes. |
| `preference` | no       | A natural-language prompt sent to the LLM alongside each article. Describes what kind of content is high/low priority for you from this source. The more specific, the better the scoring. |
| `language`   | no       | Language the LLM should use when writing the article summary (defaults to `"English"`). |
| `filter`     | no       | List of keywords. An article URL must contain at least one of these keywords **and** the base `url` to be kept. Useful for sources where you only want articles from specific sections (e.g., `"belfold"` for domestic news). |

### Example source

```yaml
- name: "Financial Times"
  url: "ft.com"
  rss:
    - "https://www.ft.com/rss/home/international"
  preference: >
    High Priority: EU regulatory changes, defense sector funding,
    tech sector earnings, central bank rate decisions.
    Low Priority: Lifestyle, arts, opinion pieces by non-economists.
  language: "English"
```

### Writing good `preference` prompts

The `preference` field is the core of the relevance engine. Tips:

- **Be explicit about priority tiers** — state what is high, medium, and low priority.
- **Name specific topics** — "EU antitrust rulings" is better than "important news".
- **State what to ignore** — explicitly listing low-value content (e.g., celebrity news, weather) helps the model avoid false positives.
- **Set exceptions** — e.g., "Ignore crime stories *unless* they reveal systemic corruption."

---

## Environment Variables

Set these in a `.env` file at the project root or pass them to Docker Compose:

| Variable           | Required | Default                  | Description |
| ------------------ | -------- | ------------------------ | ----------- |
| `POSTGRES_USER`    | no       | `dailyknowledge`         | PostgreSQL username. |
| `POSTGRES_PASSWORD`| **yes**  | —                        | PostgreSQL password. |
| `POSTGRES_DB`      | no       | `dailyknowledge`         | Database name. |
| `OPENAI_API_BASE`  | **yes**  | —                        | Base URL of the OpenAI-compatible API. |
| `OPENAI_MODEL`     | **yes**  | —                        | Model name to use for scoring. |
| `OPENAI_API_KEY`   | **yes**  | —                        | API key for the LLM provider. |
| `OPENAI_RATE_LIMIT`| no       | `10`                     | Max LLM requests per minute. |
| `CORS_ORIGINS`     | no       | `http://localhost`       | Comma-separated allowed origins. |
| `VITE_API_URL`     | no       | `http://localhost:5764`  | Backend URL the frontend uses in the browser. |

## Running

```bash
docker compose up -d
```

The frontend is served at `http://localhost:5763` and the API at `http://localhost:5764`.

---

## Roadmap

- **Daily category digest** — An LLM-generated summary for each category, produced once a day, that synthesizes the key developments across all articles scraped that day into a concise briefing. Gives you the big picture without reading every article.
- **Top 5 picks per category** — At the end of each day, have the LLM select the five most important articles per category based on the category's preference prompt and which articles the user has already read on the days prior, surfacing what you shouldn't miss.


