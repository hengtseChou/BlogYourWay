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

# New Comment Setup

##################################################################################################


class NewCommentSetup:
    """
    Handles the setup and creation of a new comment.

    Args:
        comment_uid_generator (UIDGenerator): The UID generator for comments.
        db_handler (Database): The database handler.

    Methods:
        _recaptcha_verified(request: Request) -> bool:
            Verifies the Recaptcha response.
        create_comment(post_uid: str, form: CommentForm) -> None:
            Creates and uploads a new comment based on the provided form data.
    """

    def __init__(self, comment_uid_generator: UIDGenerator, db_handler: Database) -> None:
        """
        Initializes a NewCommentSetup instance.

        Args:
            comment_uid_generator (UIDGenerator): The UID generator for comments.
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler
        self._comment_uid = comment_uid_generator.generate_comment_uid()

    @staticmethod
    def _recaptcha_verified(request: Request) -> bool:
        """
        Verifies the Recaptcha response to ensure it's valid.

        Args:
            request (Request): The HTTP request containing the Recaptcha token.

        Returns:
            bool: True if Recaptcha verification is successful, otherwise False.
        """
        token = request.form.get("g-recaptcha-response")
        payload = {"secret": RECAPTCHA_SECRET, "response": token}
        resp = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)
        resp = resp.json()
        return resp.get("success", False)

    def create_comment(self, post_uid: str, form: CommentForm) -> None:
        """
        Creates and uploads a new comment based on the form data and user's authentication status.

        Args:
            post_uid (str): The UID of the post the comment is associated with.
            form (CommentForm): The form containing comment data.
        """
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

        new_comment_data = asdict(new_comment)
        self._db_handler.comment.insert_one(new_comment_data)


def create_comment(post_uid: str, form: CommentForm) -> None:
    """
    Initializes a NewCommentSetup instance and creates a new comment.

    Args:
        post_uid (str): The UID of the post the comment is associated with.
        form (CommentForm): The form containing comment data.
    """
    uid_generator = UIDGenerator(db_handler=mongodb)
    comment_setup = NewCommentSetup(comment_uid_generator=uid_generator, db_handler=mongodb)
    comment_setup.create_comment(post_uid=post_uid, form=form)


##################################################################################################

# Comment Utilities

##################################################################################################


class CommentUtils:
    """
    Provides utility methods for handling comments.

    Args:
        db_handler (Database): The database handler.

    Methods:
        find_comments_by_post_uid(post_uid: str) -> list[dict]:
            Retrieves comments associated with a specific post UID.
    """

    def __init__(self, db_handler: Database) -> None:
        """
        Initializes a CommentUtils instance.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def find_comments_by_post_uid(self, post_uid: str) -> list[dict]:
        """
        Retrieves comments associated with a specific post UID.

        Args:
            post_uid (str): The UID of the post.

        Returns:
            list[dict]: A list of dictionaries containing comment information.
        """
        result = (
            self._db_handler.comment.find({"post_uid": post_uid}).sort("created_at", 1).as_list()
        )
        return result


comment_utils = CommentUtils(db_handler=mongodb)
