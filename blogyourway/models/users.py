import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

from flask import url_for
from flask_login import UserMixin


def select_profile_img() -> str:

    idx = random.choice(range(5))
    return url_for("static", filename=f"img/profile{idx}.png")


@dataclass
class UserInfo(UserMixin):
    username: str
    email: str
    blogname: str
    profile_img_url: str = ""
    cover_url: str = ""
    created_at: datetime = None
    short_bio: str = ""
    social_links: list[dict[str, str]] = field(default_factory=list)
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

    # override the get_id method from UserMixin
    def get_id(self):
        return self.username


@dataclass
class UserCreds:
    username: str
    email: str
    password: str


@dataclass
class UserAbout:
    username: str
    about: str = ""
