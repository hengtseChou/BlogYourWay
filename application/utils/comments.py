"""
This module includes a create comment function, and a comment utility class.
"""
import requests
from flask import Request
from flask_login import current_user
from application.config import RECAPTCHA_SECRET, ENV
from application.utils.common import UIDGenerator, get_today, FormValidator
from application.services.mongo import my_database, MyDatabase

###################################################################

# new comment setup

###################################################################


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

    def __init__(
        self, comment_uid_generator: UIDGenerator, db_handler: MyDatabase
    ) -> None:

        self._db_handler = db_handler
        self._comment_uid = comment_uid_generator.generate_comment_uid()

    def _form_validated(self, request: Request, validator: FormValidator):

        return True

    def _recaptcha_verified(self, request: Request):

        token = request.form.get("g-recaptcha-response")
        payload = {"secret": RECAPTCHA_SECRET, "response": token}
        resp = requests.post(
            "https://www.google.com/recaptcha/api/siteverify", params=payload
        )
        resp = resp.json()

        if resp["success"]:
            return True
        return False

    def _is_authenticated_commenter(self, user):

        if user.is_authenticated:
            return True
        return False

    def _create_authenticated_comment(
        self, request: Request, commenter_name: str, post_uid: str
    ):

        commenter = self._db_handler.user_info.find_one({"username": commenter_name})
        new_comment = {
            "name": commenter["username"],
            "email": commenter["email"],
            "profile_link": f'/{commenter["username"]}/about',
            "profile_pic": f'/{commenter["username"]}/get-profile-pic',
            "post_uid": post_uid,
            "comment_uid": self._comment_uid,
            "comment": request.form.get("comment"),
            "created_at": get_today(env=ENV),
        }

        return new_comment

    def _create_unauthenticated_comment(self, request: Request, post_uid: str):

        new_comment = {
            "name": f'{request.form.get("name")} (Visitor)',
            "email": request.form.get("email"),
            "profile_link": "",
            "profile_pic": "/static/img/visitor.png",
            "post_uid": post_uid,
            "comment_uid": self._comment_uid,
            "comment": request.form.get("comment"),
            "created_at": get_today(env=ENV),
        }

        if new_comment["email"]:
            new_comment["profile_link"] = f'mailto:{new_comment["email"]}'

        return new_comment

    def create_comment(self, post_uid: str, request: Request):

        validator = FormValidator()
        if not self._form_validated(request, validator):
            return
        if not self._recaptcha_verified(request):
            return

        if self._is_authenticated_commenter(current_user):
            new_comment = self._create_authenticated_comment(
                request=request, commenter_name=current_user.username, post_uid=post_uid
            )
        else:
            new_comment = self._create_unauthenticated_comment(request, post_uid)

        self._db_handler.comment.insert_one(new_comment)


def create_comment(post_uid: str, request: Request):
    """initialize a new comment setup instance, process the request and upload new comment.

    Args:
        post_uid (str): the post uid which the comment is associated with.
        request (Request): the request with form sent.
    """

    uid_generator = UIDGenerator(db_handler=my_database)

    comment_setup = NewCommentSetup(
        comment_uid_generator=uid_generator, db_handler=my_database
    )
    comment_setup.create_comment(post_uid=post_uid, request=request)


###################################################################

# comment utilities

###################################################################


class CommentUtils:
    def __init__(self, db_handler: MyDatabase):

        self._db_handler = db_handler

    def find_comments_by_post_uid(self, post_uid: str):

        result = (
            self._db_handler.comment.find({"post_uid": post_uid})
            .sort("created_at", 1)
            .as_list()
        )
        return result


comment_utils = CommentUtils(db_handler=my_database)
