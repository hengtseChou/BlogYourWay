from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ProjectInfo:
    project_uid: str
    author: str
    title: str
    short_description: str
    tags: list[str]
    custom_slug: str
    images: list[tuple[str, str]]
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
    views: int = 0
    reads: int = 0


@dataclass
class ProjectContent:
    project_uid: str
    author: str
    content: str
