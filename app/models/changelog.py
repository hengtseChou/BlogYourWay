from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Changelog:
    """Represents a changelog entry.

    Attributes:
        changelog_uid (str): Unique identifier for the changelog.
        title (str): Title of the changelog.
        author (str): Author of the changelog.
        date (datetime): Date of the changelog.
        category (str): Category of the changelog.
        content (str): Content of the changelog.
        tags (List[str]): List of tags associated with the changelog.
        link (str, optional): Optional URL link related to the changelog.
        link_description (str, optional): Optional description for the link.
        created_at (datetime, optional): Timestamp when the changelog was created. Defaults to the current UTC time.
        last_updated (datetime, optional): Timestamp of the last update to the changelog. Defaults to the current UTC time.
        archived (bool): Indicates whether the changelog is archived. Defaults to False.
    """

    changelog_uid: str
    author: str
    title: str
    date: datetime
    category: str
    content: str
    tags: list[str]
    link: str = ""
    link_description: str = ""
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
