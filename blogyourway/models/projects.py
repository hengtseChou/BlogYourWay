from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProjectInfo:
    project_uid: str
    custom_slug: str
    title: str
    short_description: str
    author: str
    tags: list[str]
    images: list[dict[str, str]]
    created_at: datetime = field(init=False)
    last_updated: datetime = field(init=False)
    archived: bool = False
    views: int = 0
    reads: int = 0

    def __post_init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class ProjectContent:
    project_uid: str
    author: str
    content: str
