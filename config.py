import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "sources.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_all_urls() -> list[str]:
    """Return a flat list of all source URLs from every category."""
    config = _load_config()
    return [
        source["url"]
        for category in config.get("categories", [])
        for source in category.get("sources", [])
    ]


def get_preference(url: str) -> str | None:
    """Return the preference string for the source matching the given URL, or None."""
    config = _load_config()
    for category in config.get("categories", []):
        for source in category.get("sources", []):
            if source["url"] == url:
                return source.get("preference")
    return None
