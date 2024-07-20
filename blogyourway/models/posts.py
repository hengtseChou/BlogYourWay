from dataclasses import dataclass
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
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
    featured: bool = False
    views: int = 0
    reads: int = 0


@dataclass
class PostContent:
    post_uid: str
    author: str
    content: str
