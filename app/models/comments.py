from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.users import select_profile_img


@dataclass
class Comment:
    """Class to represent a comment on a post.

    Attributes:
        name (str): Name of the commenter.
        email (str): Email of the commenter.
        post_uid (str): Unique identifier of the post being commented on.
        comment_uid (str): Unique identifier for the comment.
        comment (str): Content of the comment.
        profile_link (str): URL to the commenter's profile. Defaults to an empty string.
        profile_img_url (str): URL to the commenter's profile image. Defaults to an empty string.
        created_at (datetime): Timestamp when the comment was created. Defaults to the current UTC time.
    """

    name: str
    email: str
    post_uid: str
    comment_uid: str
    comment: str
    profile_link: str = field(default="")
    profile_img_url: str = field(default="")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.profile_link:
            self.profile_link = f"/@{self.name}/about"
        if not self.profile_img_url:
            self.profile_img_url = f"/@{self.name}/get-profile-img"


@dataclass
class AnonymousComment:
    """Class to represent an anonymous comment on a post.

    Attributes:
        name (str): Name used for the comment.
        email (str): Email of the commenter.
        post_uid (str): Unique identifier of the post being commented on.
        comment_uid (str): Unique identifier for the comment.
        comment (str): Content of the comment.
        profile_link (str): URL to the commenter's profile. Defaults to an empty string.
        profile_img_url (str): URL to the commenter's profile image. Defaults to an empty string.
        created_at (datetime): Timestamp when the comment was created. Defaults to the current UTC time.
    """

    name: str
    email: str
    post_uid: str
    comment_uid: str
    comment: str
    profile_link: str = field(default="")
    profile_img_url: str = field(default="")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.profile_link:
            self.profile_link = f"mailto:{self.email}"
        if not self.profile_img_url:
            self.profile_img_url = select_profile_img()
