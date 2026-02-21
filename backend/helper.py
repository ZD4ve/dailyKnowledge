from datetime import datetime
from dataclasses import dataclass

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
