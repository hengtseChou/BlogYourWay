"""
This module includes a create comment function, and a comment utility class.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import requests
from flask import Request
from flask_login import current_user

from blogyourway.config import ENV, RECAPTCHA_SECRET
from blogyourway.helpers.common import FormValidator, MyDataClass, UIDGenerator, get_today
from blogyourway.services.mongo import Database, mongodb

###################################################################

# new comment setup

###################################################################


@dataclass
class Comment(MyDataClass):
    name: str
    email: str
    profile_link: str = field(init=False)
    profile_img_url: str = field(init=False)
    article_uid: str
    comment_uid: str
    comment: str
    created_at: datetime = field(default=get_today(env=ENV))

    def __post_init__(self):
        self.profile_link = f"/@{self.name}/about"
        self.profile_img_url = f"/@{self.name}/get-profile-img"


@dataclass
class AnonymousComment(MyDataClass):
    name: str
    email: str
    profile_link: str = field(default="", init=False)
    article_uid: str
    comment_uid: str
    comment: str
    profile_img_url: str = "/static/img/visitor.png"
    created_at: datetime = field(default=get_today(env=ENV))

    def __post_init__(self):
        if self.email != "":
            self.profile_link = f"mailto:{self.email}"


class NewCommentSetup:
    """Setup a new instance for uploading a new comment.

    Args:
    - request_ (Request): the https request received.
    - article_uid (str): the post uid which the comment is associated with.
    - comment_uid_generator (UIDGenerator): the dependent uid generator.
    - db_handler (MyDatabase): database.
    - commenter_name (str): pass the plain text commenter name.

    Procedure:
    1. Validate the request form.
    2. Validate the Recaptcha response.
    3. Process the form into comment dict, based on if the user is authenticated.
    4. Upload via the database handler.
    """

    def __init__(self, comment_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._db_handler = db_handler
        self._comment_uid = comment_uid_generator.generate_comment_uid()

    def _form_validated(self, request: Request, validator: FormValidator) -> bool:
        return True

    def _recaptcha_verified(self, request: Request) -> bool:
        token = request.form.get("g-recaptcha-response")
        payload = {"secret": RECAPTCHA_SECRET, "response": token}
        resp = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)
        resp = resp.json()

        if resp["success"]:
            return True
        return False

    def create_comment(self, article_uid: str, request: Request) -> None:
        validator = FormValidator()
        if not self._form_validated(request, validator):
            return
        if not self._recaptcha_verified(request):
            return

        if current_user.is_authenticated:
            new_comment = Comment(
                name=current_user.username,
                email=current_user.email,
                article_uid=article_uid,
                comment_uid=self._comment_uid,
                comment=request.form.get("comment"),
            )
        else:
            new_comment = AnonymousComment(
                name=f'{request.form.get("name")} (Visitor)',
                email=request.form.get("email"),
                article_uid=article_uid,
                comment_uid=self._comment_uid,
                comment=request.form.get("comment"),
            )

        new_comment = new_comment.as_dict()
        self._db_handler.comment.insert_one(new_comment)


def create_comment(article_uid: str, request: Request) -> None:
    """initialize a new comment setup instance, process the request and upload new comment.

    Args:
        article_uid (str): the post uid which the comment is associated with.
        request (Request): the request with form sent.
    """

    uid_generator = UIDGenerator(db_handler=mongodb)

    comment_setup = NewCommentSetup(comment_uid_generator=uid_generator, db_handler=mongodb)
    comment_setup.create_comment(article_uid=article_uid, request=request)


###################################################################

# comment utilities

###################################################################


class CommentUtils:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def find_comments_by_article_uid(self, article_uid: str) -> List[Dict]:
        result = (
            self._db_handler.comment.find({"article_uid": article_uid})
            .sort("created_at", 1)
            .as_list()
        )
        return result


comment_utils = CommentUtils(db_handler=mongodb)
