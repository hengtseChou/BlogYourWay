"""
This module includes a create comment function, and a comment utility class.
"""

from dataclasses import asdict

import requests
from flask import Request, request
from flask_login import current_user

from app.config import RECAPTCHA_SECRET
from app.forms.comments import CommentForm
from app.helpers.utils import UIDGenerator
from app.models.comments import AnonymousComment, Comment
from app.mongo import Database, mongodb

##################################################################################################

# new comment setup

##################################################################################################


class NewCommentSetup:
    """Setup a new instance for uploading a new comment.

    Args:
    - request_ (Request): the https request received.
    - post_uid (str): the post uid which the comment is associated with.
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

    @staticmethod
    def _recaptcha_verified(request: Request) -> bool:
        token = request.form.get("g-recaptcha-response")
        payload = {"secret": RECAPTCHA_SECRET, "response": token}
        resp = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)
        resp = resp.json()

        if resp["success"]:
            return True
        return False

    def create_comment(self, post_uid: str, form: CommentForm) -> None:

        if not self._recaptcha_verified(request):
            return

        if current_user.is_authenticated:
            new_comment = Comment(
                name=current_user.username,
                email=current_user.email,
                post_uid=post_uid,
                comment_uid=self._comment_uid,
                comment=form.data.get("comment"),
            )
        else:
            new_comment = AnonymousComment(
                name=f'{form.data.get("name")} (Visitor)',
                email=form.data.get("email"),
                post_uid=post_uid,
                comment_uid=self._comment_uid,
                comment=form.data.get("comment"),
            )

        new_comment = asdict(new_comment)
        self._db_handler.comment.insert_one(new_comment)


def create_comment(post_uid: str, form: CommentForm) -> None:
    """initialize a new comment setup instance, process the request and upload new comment.

    Args:
        post_uid (str): the post uid which the comment is associated with.
        request (Request): the request with form sent.
    """

    uid_generator = UIDGenerator(db_handler=mongodb)

    comment_setup = NewCommentSetup(comment_uid_generator=uid_generator, db_handler=mongodb)
    comment_setup.create_comment(post_uid=post_uid, form=form)


##################################################################################################

# comment utilities

##################################################################################################


class CommentUtils:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def find_comments_by_post_uid(self, post_uid: str) -> list[dict]:
        result = (
            self._db_handler.comment.find({"post_uid": post_uid}).sort("created_at", 1).as_list()
        )
        return result


comment_utils = CommentUtils(db_handler=mongodb)
