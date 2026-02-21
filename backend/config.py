import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "sources.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



def get_all_urls() -> list[tuple[str, str]]:
    """Return a flat list of (name, url) tuples from every category."""
    config = _load_config()
    return [
        (source["name"], source["url"])
        for category in config.get("categories", [])
        for source in category.get("sources", [])
    ]

def get_preference(name: str) -> str | None:
    """Return the preference string for the source matching the given name (case-insensitive)."""
    config = _load_config()
    for category in config.get("categories", []):
        for source in category.get("sources", []):
            if source["name"].lower() == name.lower():
                return source.get("preference")
    return None

def get_language(name: str) -> str | None:
    """Return the language for the source matching the given name (case-insensitive)."""
    config = _load_config()
    for category in config.get("categories", []):
        for source in category.get("sources", []):
            if source["name"].lower() == name.lower():
                return source.get("language")
    return None

def get_categories() -> list[str]:
    """Return a list of all category names."""
    config = _load_config()
    return [category.get("name") for category in config.get("categories", [])]

def get_sites_by_category(category_name: str) -> list[str]:
    """Return a list of site names for the given category name (case-insensitive)."""
    config = _load_config()
    for category in config.get("categories", []):
        if category.get("name").lower() == category_name.lower():
            return [source["name"] for source in category.get("sources", [])]
    return []

def get_filter(name: str) -> list[str] | None:
    """Return the filter list for the source matching the given name (case-insensitive)."""
    config = _load_config()
    for category in config.get("categories", []):
        for source in category.get("sources", []):
            if source["name"].lower() == name.lower():
                return source.get("filter", [])
    return None