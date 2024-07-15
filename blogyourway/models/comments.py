from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Comment:
    name: str
    email: str
    profile_link: str = field(init=False)
    profile_img_url: str = field(init=False)
    post_uid: str
    comment_uid: str
    comment: str
    created_at: datetime = field(init=False)

    def __post_init__(self):
        self.profile_link = f"/@{self.name}/about"
        self.profile_img_url = f"/@{self.name}/get-profile-img"
        self.created_at = datetime.now(timezone.utc)


@dataclass
class AnonymousComment:
    name: str
    email: str
    profile_link: str = field(default="", init=False)
    post_uid: str
    comment_uid: str
    comment: str
    profile_img_url: str = "/static/img/visitor.png"
    created_at: datetime = field(init=False)

    def __post_init__(self):
        if self.email != "":
            self.profile_link = f"mailto:{self.email}"
        self.created_at = datetime.now(timezone.utc)
