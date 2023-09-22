import requests
from flask import Request, request
from flask_login import current_user
from application.config import RECAPTCHA_SECRET, ENV
from application.utils.common import uid_generator, get_today
from application.services.mongo import my_database, MyDatabase

###################################################################

# new comment setup

###################################################################


class NewCommentSetup:
    def __init__(
        self,
        request: Request,
        post_uid: str,
        comment_uid_generator: uid_generator,
        db_handler: MyDatabase,
        commenter: current_user,
    ) -> None:

        self._request = request
        self._post_uid = post_uid
        self._db_handler = db_handler
        self._comment_uid = comment_uid_generator.generate_comment_uid()
        self._commenter = commenter

    def _form_validated(self):
        
        return True

    def _recaptcha_verified(self):

        token = self._request.form.get("g-recaptcha-response")
        payload = {"secret": RECAPTCHA_SECRET, "response": token}
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify", params=payload
        )
        response = r.json()

        if response["success"]:
            return True
        return False

    def _is_authenticated_commenter(self):

        if self._commenter.is_authenticated:
            return True
        return False

    def _create_authenticated_comment(self):

        commenter = self._db_handler.user_info.find_one(
            {"username": current_user.username}
        )
        new_comment = {
            "name": commenter["username"],
            "email": commenter["email"],
            "profile_link": f'/{commenter["username"]}/about',
            "profile_pic": f'/{commenter["username"]}/get-profile-pic',
            "post_uid": self._post_uid,
            "comment_uid": self._comment_uid,
            "comment": self._request.form.get("comment"),
            "created_at": get_today(env=ENV),
        }
        return new_comment

    def _create_unauthenticated_comment(self):

        new_comment = {
            "name": f'{request.form.get("name")} (Visitor)',
            "email": request.form.get("email"),
            "profile_link": "",
            "profile_pic": "/static/img/visitor.png",
            "post_uid": self._post_uid,
            "comment_uid": self._comment_uid,
            "comment": self._request.form.get("comment"),
            "created_at": get_today(env=ENV),
        }
        if new_comment["email"]:
            new_comment["profile_link"] = f'mailto:{new_comment["email"]}'
        return new_comment

    def create_comment(self):

        if not self._form_validated():
            return
        if not self._recaptcha_verified():
            return

        if self._is_authenticated_commenter():
            new_comment = self._create_authenticated_comment()
        else:
            new_comment = self._create_unauthenticated_comment()

        self._db_handler.comment.insert_one(new_comment)


def create_comment(post_uid, request):

    db = my_database
    uid_generator = uid_generator(db_handler=db)

    comment_setup = NewCommentSetup(
        request=request,
        post_uid=post_uid,
        comment_uid_generator=uid_generator,
        db_handler=db,
        commenter=current_user,
    )
    comment_setup.create_comment()

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