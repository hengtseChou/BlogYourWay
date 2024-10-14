import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import url_for
from flask_login import UserMixin


def select_profile_img() -> str:
    """Selects a random profile image URL.

    Returns:
        str: URL to the selected profile image.
    """
    idx = random.choice(range(5))
    return url_for("static", filename=f"img/profile{idx}.png")


@dataclass
class UserInfo(UserMixin):
    """Class to represent user information.

    Attributes:
        username (str): Username of the user.
        email (str): Email address of the user.
        blogname (str): Blog name of the user.
        profile_img_url (str): URL to the user's profile image. Defaults to an empty string.
        cover_url (str): URL to the user's cover image. Defaults to an empty string.
        created_at (datetime): Timestamp when the user was created. Defaults to the current UTC time if None.
        short_bio (str): Short biography of the user. Defaults to an empty string.
        social_links (list[Tuple[str, str]]): list of social media links as tuples (name, URL). Defaults to five empty tuples.
        changelog_enabled (bool): Flag indicating if the changelog feature is enabled. Defaults to False.
        gallery_enabled (bool): Flag indicating if the gallery feature is enabled. Defaults to False.
        total_views (int): Total number of views. Defaults to 0.
        tags (dict[str, int]): Dictionary of tags and their associated counts. Defaults to an empty dictionary.
    """

    username: str
    email: str
    blogname: str
    profile_img_url: str = ""
    cover_url: str = ""
    created_at: Optional[datetime] = None
    short_bio: str = ""
    social_links: list[Tuple[str, str]] = None
    changelog_enabled: bool = False
    gallery_enabled: bool = False
    total_views: int = 0
    tags: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.profile_img_url:
            self.profile_img_url = select_profile_img()
        if not self.cover_url:
            self.cover_url = url_for("static", filename="img/default-cover.jpg")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.social_links is None:
            self.social_links = [[]] * 5

    def get_id(self) -> str:
        """Overrides the get_id method from UserMixin to return the username.

        Returns:
            str: Username of the user.
        """
        return self.username


@dataclass
class UserCreds:
    """Class to represent user credentials.

    Attributes:
        username (str): Username of the user.
        email (str): Email address of the user.
        password (str): Password for the user account.
    """

    username: str
    email: str
    password: str


@dataclass
class UserAbout:
    """Class to represent additional information about a user.

    Attributes:
        username (str): Username of the user.
        about (str): Additional information or bio about the user. Defaults to an empty string.
    """

    username: str
    about: str = ""
