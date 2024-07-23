from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple


@dataclass
class ProjectInfo:
    """Class to represent information about a project.

    Attributes:
        project_uid (str): Unique identifier for the project.
        author (str): Author of the project.
        title (str): Title of the project.
        short_description (str): Brief description of the project.
        tags (List[str]): List of tags associated with the project.
        custom_slug (str): Custom URL slug for the project.
        images (List[Tuple[str, str]]): List of image URLs and descriptions as tuples.
        created_at (datetime): Timestamp when the project was created. Defaults to the current UTC time.
        last_updated (datetime): Timestamp when the project was last updated. Defaults to the current UTC time.
        archived (bool): Flag indicating if the project is archived. Defaults to False.
        views (int): Number of views the project has received. Defaults to 0.
        reads (int): Number of reads the project has received. Defaults to 0.
    """

    project_uid: str
    author: str
    title: str
    short_description: str
    tags: List[str]
    custom_slug: str
    images: List[Tuple[str, str]]
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
    views: int = 0
    reads: int = 0


@dataclass
class ProjectContent:
    """Class to represent the content of a project.

    Attributes:
        project_uid (str): Unique identifier for the project.
        author (str): Author of the project.
        content (str): Content of the project.
    """

    project_uid: str
    author: str
    content: str
