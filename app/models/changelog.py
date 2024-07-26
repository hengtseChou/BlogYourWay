from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Changelog:

    changelog_uid: str
    title: str
    author: str
    date: datetime
    category: str
    content: str
    tags: list[str]
    link: str = ""
    link_description: str = ""
    created_at: datetime = None
    last_updated: datetime = None
    archived: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)
