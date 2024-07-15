from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PostInfo:
    post_uid: str
    custom_slug: str
    title: str
    subtitle: str
    author: str
    tags: list[str]
    cover_url: str
    created_at: datetime = field(init=False)
    last_updated: datetime = field(init=False)
    archived: bool = False
    featured: bool = False
    views: int = 0
    reads: int = 0

    def __post_init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class PostContent:
    post_uid: str
    author: str
    content: str
