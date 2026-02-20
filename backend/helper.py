from datetime import datetime
from urllib.parse import urlparse
from dataclasses import dataclass

def extract_site_from(url: str) -> str:
    """
    Extract the TLD and main domain part (e.g., 'example.com' from 'subdomain.example.com')
    """
    # Remove protocol if present
    if '://' in url:
        url = urlparse(url).netloc
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Split by dots and get the last two parts (domain + TLD)
    parts = url.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return url


@dataclass
class dataArticle:
    id: int
    site_name: str
    url: str
    title: str
    text: str
    authors: str | None
    publish_date: datetime
    score: int
    summary: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: dict) -> "dataArticle":
        return cls(**row)
