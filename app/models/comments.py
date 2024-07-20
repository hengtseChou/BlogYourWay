from dataclasses import dataclass
from datetime import datetime, timezone

from .users import select_profile_img


@dataclass
class Comment:
    name: str
    email: str
    post_uid: str
    comment_uid: str
    comment: str
    profile_link: str = ""
    profile_img_url: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if not self.profile_link:
            self.profile_link = f"/@{self.name}/about"
        if not self.profile_img_url:
            self.profile_img_url = f"/@{self.name}/get-profile-img"
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class AnonymousComment:
    name: str
    email: str
    post_uid: str
    comment_uid: str
    comment: str
    profile_link: str = ""
    profile_img_url: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if not self.profile_link:
            self.profile_link = f"mailto:{self.email}"
        if not self.profile_img_url:
            self.profile_img_url = select_profile_img()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
