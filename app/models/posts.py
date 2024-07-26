from dataclasses import dataclass
from datetime import datetime, timezone
from typing import list


@dataclass
class PostInfo:
    """Class to represent information about a post.

    Attributes:
        post_uid (str): Unique identifier for the post.
        title (str): Title of the post.
        subtitle (str): Subtitle of the post.
        author (str): Author of the post.
        tags (list[str]): List of tags associated with the post.
        cover_url (str): URL of the cover image for the post.
        custom_slug (str): Custom URL slug for the post.
        created_at (datetime): Timestamp when the post was created. Defaults to the current UTC time.
        last_updated (datetime): Timestamp when the post was last updated. Defaults to the current UTC time.
        archived (bool): Flag indicating if the post is archived. Defaults to False.
        featured (bool): Flag indicating if the post is featured. Defaults to False.
        views (int): Number of views the post has received. Defaults to 0.
        reads (int): Number of reads the post has received. Defaults to 0.
    """

    post_uid: str
    title: str
    subtitle: str
    author: str
    tags: list[str]
    cover_url: str
    custom_slug: str
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
    featured: bool = False
    views: int = 0
    reads: int = 0


@dataclass
class PostContent:
    """Class to represent the content of a post.

    Attributes:
        post_uid (str): Unique identifier for the post.
        author (str): Author of the post.
        content (str): Content of the post.
    """

    post_uid: str
    author: str
    content: str
