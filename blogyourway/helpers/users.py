import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import bcrypt
from flask import Request, flash
from flask_login import UserMixin

from blogyourway.config import ENV
from blogyourway.helpers.common import FormValidator, MyDataClass, get_today
from blogyourway.services.logging import Logger, logger, logger_utils
from blogyourway.services.mongo import Database, mongodb


@dataclass
class UserInfo(UserMixin, MyDataClass):
    username: str
    email: str
    blogname: str
    cover_url: str = ""
    profile_img_url: str = ""
    short_bio: str = ""
    created_at: datetime = None
    changelog_enabled: bool = False
    gallery_enabled: bool = False
    total_views: int = 0
    tags: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = get_today(env=ENV)

    # override the get_id method from UserMixin
    def get_id(self):
        return self.username


@dataclass
class UserCreds(MyDataClass):
    username: str
    email: str
    password: str


@dataclass
class UserAbout(MyDataClass):
    username: str
    about: str = ""


###################################################################

# user registration

###################################################################


class NewUserSetup:
    def __init__(self, request: Request, db_handler: Database, logger: Logger) -> None:
        self._regist_form = request.form.to_dict()
        self._request = request
        self._db_handler = db_handler
        self._logger = logger

    def _form_validated(self, validator: FormValidator) -> bool:
        if not validator.validate_email(self._regist_form.get("email")):
            return False
        if not validator.validate_password(self._regist_form.get("password")):
            return False
        if not validator.validate_username(self._regist_form.get("username")):
            return False
        if not validator.validate_blogname(self._regist_form.get("blogname")):
            return False
        return True

    def _no_duplicates(self) -> bool:
        for field in ["email", "username"]:
            if self._db_handler.user_info.exists(field, self._regist_form.get(field)):
                flash(
                    f"{field.capitalize()} is already used. Please try another one.",
                    category="error",
                )
                logger_utils.registration_failed(
                    request=self._request,
                    msg=f"{field} {self._regist_form[field]} already used",
                )
                return True
        return False

    def _create_user_creds(self, username: str, email: str, hashed_password: str) -> Dict:
        new_user_creds = UserCreds(username=username, email=email, password=hashed_password)
        return new_user_creds.as_dict()

    def _create_user_info(self, username: str, email: str, blogname: str) -> Dict:
        new_user_info = UserInfo(username=username, email=email, blogname=blogname)
        return new_user_info.as_dict()

    def _create_user_about(self, username: str) -> Dict:
        new_user_about = UserAbout(username=username)
        return new_user_about.as_dict()

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hashing user input password.

        Args:
            password (str): a string of plain text password.

        Returns:
            str: a string of the hashed password encoded back to utf-8.
        """

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
        hashed_pw = hashed_pw.decode("utf-8")
        return hashed_pw

    def create_user(self) -> str | None:
        validator = FormValidator()

        if not self._form_validated(validator=validator):
            return None

        if self._no_duplicates():
            return None

        hashed_pw = self._hash_password(self._regist_form.get("password"))
        new_user_creds = self._create_user_creds(
            self._regist_form.get("username"), self._regist_form.get("email"), hashed_pw
        )
        new_user_info = self._create_user_info(
            self._regist_form.get("username"),
            self._regist_form.get("email"),
            self._regist_form.get("blogname"),
        )
        new_user_about = self._create_user_about(self._regist_form.get("username"))

        self._db_handler.user_creds.insert_one(new_user_creds)
        self._db_handler.user_info.insert_one(new_user_info)
        self._db_handler.user_about.insert_one(new_user_about)

        logger_utils.registration_succeeded(request=self._request)

        return new_user_info.get("username")


###################################################################

# deleting user

###################################################################


class UserDeletionSetup:
    def __init__(self, username: str, db_handler: Database, logger: Logger) -> None:
        self._user_to_be_deleted = username
        self._db_handler = db_handler
        self._logger = logger

    def _get_articles_uid_by_user(self) -> List[str]:
        articles = self._db_handler.article_info.find({"author": self._user_to_be_deleted})
        articles_uid = [article.get("article_uid") for article in articles]

        return articles_uid

    def _remove_all_posts(self) -> None:
        self._db_handler.article_info.delete_many({"author": self._user_to_be_deleted})
        self._db_handler.article_content.delete_many({"author": self._user_to_be_deleted})
        self._logger.debug(f"Deleted all articles written by user {self._user_to_be_deleted}.")

    def _remove_all_related_comments(self, article_uids: list) -> None:
        for article_uid in article_uids:
            self._db_handler.comment.delete_many({"article_uid": article_uid})
        self._logger.debug(f"Deleted comments under articles by user {self._user_to_be_deleted}.")

    def _remove_all_user_data(self) -> None:
        self._db_handler.user_creds.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_info.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_about.delete_one({"username": self._user_to_be_deleted})

        self._logger.debug(f"Deleted user information for user {self._user_to_be_deleted}.")

    def start_deletion_process(self) -> None:
        articles_uid = self._get_articles_uid_by_user()
        self._remove_all_posts()
        self._remove_all_related_comments(articles_uid)
        # this place should includes removing metrics data for the user
        self._remove_all_user_data()


###################################################################

# user utils

###################################################################


class UserUtils:
    def __init__(self, db_handler: Database, logger: logging.Logger) -> None:
        self._db_handler = db_handler
        self._logger = logger

    def get_all_username(self) -> List[str]:
        all_user_info = self._db_handler.user_info.find({})
        all_username = [user_info.get("username") for user_info in all_user_info]
        return all_username

    def get_user_info(self, username: str) -> UserInfo:
        user_info = self._db_handler.user_info.find_one({"username": username})
        if user_info is None:
            return None
        if "_id" in user_info:
            user_info.pop("_id")
        user_info = UserInfo(**user_info)
        return user_info

    def get_user_creds(self, email: str) -> UserCreds:
        user_creds = self._db_handler.user_creds.find_one({"email": email})
        if user_creds is None:
            return None
        if "_id" in user_creds:
            user_creds.pop("_id")
        user_creds = UserCreds(**user_creds)
        return user_creds

    def delete_user(self, username: str) -> None:
        user_deletion = UserDeletionSetup(
            username=username, db_handler=self._db_handler, logger=self._logger
        )
        user_deletion.start_deletion_process()

    def create_user(self, request: Request) -> str:
        """_summary_

        Args:
            request (request): flask request object

        Returns:
            str: username
        """
        user_registration = NewUserSetup(request, self._db_handler, self._logger)
        return user_registration.create_user()

    def total_view_increment(self, username: str) -> None:
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments={"total_views": 1}
        )


user_utils = UserUtils(db_handler=mongodb, logger=logger)
