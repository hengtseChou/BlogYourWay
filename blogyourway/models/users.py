from dataclasses import dataclass, field
from datetime import datetime, timezone

from flask_login import UserMixin


@dataclass
class UserInfo(UserMixin):
    username: str
    email: str
    blogname: str
    cover_url: str = ""
    profile_img_url: str = ""
    short_bio: str = ""
    created_at: datetime = None
    social_links: list[dict[str, str]] = field(default_factory=list)
    changelog_enabled: bool = False
    gallery_enabled: bool = False
    total_views: int = 0
    tags: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
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
