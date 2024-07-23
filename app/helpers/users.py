import logging
from dataclasses import asdict

import bcrypt

from app.forms.users import SignUpForm
from app.logging import Logger, logger, logger_utils
from app.models.users import UserAbout, UserCreds, UserInfo
from app.mongo import Database, mongodb

##################################################################################################

# user registration

##################################################################################################


class NewUserSetup:
    def __init__(self, form: SignUpForm, db_handler: Database, logger: Logger) -> None:
        """
        Initialize the NewUserSetup class.

        Args:
            form (SignUpForm): The form containing user registration data.
            db_handler (Database): The database handler.
            logger (Logger): The logger instance.
        """
        self._regist_form = form
        self._db_handler = db_handler
        self._logger = logger

    def _create_user_creds(self, username: str, email: str, hashed_password: str) -> dict:
        """
        Create a dictionary of user credentials.

        Args:
            username (str): The user's username.
            email (str): The user's email.
            hashed_password (str): The hashed password.

        Returns:
            dict: A dictionary containing the user's credentials.
        """
        new_user_creds = UserCreds(username=username, email=email, password=hashed_password)
        return asdict(new_user_creds)

    def _create_user_info(self, username: str, email: str, blogname: str) -> dict:
        """
        Create a dictionary of user information.

        Args:
            username (str): The user's username.
            email (str): The user's email.
            blogname (str): The user's blog name.

        Returns:
            dict: A dictionary containing the user's information.
        """
        new_user_info = UserInfo(username=username, email=email, blogname=blogname)
        return asdict(new_user_info)

    def _create_user_about(self, username: str) -> dict:
        """
        Create a dictionary of user about information.

        Args:
            username (str): The user's username.

        Returns:
            dict: A dictionary containing the user's about information.
        """
        new_user_about = UserAbout(username=username)
        return asdict(new_user_about)

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash the user's password.

        Args:
            password (str): The plaintext password.

        Returns:
            str: The hashed password.
        """
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
        return hashed_pw.decode("utf-8")

    def create_user(self) -> str:
        """
        Create a new user in the database.

        Returns:
            str: The username of the newly created user.
        """
        hashed_pw = self._hash_password(self._regist_form.password.data)
        new_user_creds = self._create_user_creds(
            self._regist_form.username.data, self._regist_form.email.data, hashed_pw
        )
        new_user_info = self._create_user_info(
            self._regist_form.username.data,
            self._regist_form.email.data,
            self._regist_form.blogname.data,
        )
        new_user_about = self._create_user_about(self._regist_form.username.data)

        self._db_handler.user_creds.insert_one(new_user_creds)
        self._db_handler.user_info.insert_one(new_user_info)
        self._db_handler.user_about.insert_one(new_user_about)

        logger_utils.registration_succeeded(self._regist_form.username.data)

        return self._regist_form.username.data


##################################################################################################

# deleting user

##################################################################################################


class UserDeletionSetup:
    def __init__(self, username: str, db_handler: Database, logger: Logger) -> None:
        """
        Initialize the UserDeletionSetup class.

        Args:
            username (str): The username of the user to be deleted.
            db_handler (Database): The database handler.
            logger (Logger): The logger instance.
        """
        self._user_to_be_deleted = username
        self._db_handler = db_handler
        self._logger = logger

    def _get_posts_uid_by_user(self) -> list[str]:
        """
        Get a list of post UIDs authored by the user.

        Returns:
            list[str]: A list of post UIDs.
        """
        posts = self._db_handler.post_info.find({"author": self._user_to_be_deleted})
        return [post.get("post_uid") for post in posts]

    def _remove_all_posts(self) -> None:
        """
        Remove all posts authored by the user.
        """
        self._db_handler.post_info.delete_many({"author": self._user_to_be_deleted})
        self._db_handler.post_content.delete_many({"author": self._user_to_be_deleted})
        self._logger.debug(f"Deleted all posts written by user {self._user_to_be_deleted}.")

    def _remove_all_related_comments(self, post_uids: list[str]) -> None:
        """
        Remove all comments related to the user's posts.

        Args:
            post_uids (list[str]): A list of post UIDs.
        """
        for post_uid in post_uids:
            self._db_handler.comment.delete_many({"post_uid": post_uid})
        self._logger.debug(f"Deleted comments under posts by user {self._user_to_be_deleted}.")

    def _remove_all_user_data(self) -> None:
        """
        Remove all user data from the database.
        """
        self._db_handler.user_creds.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_info.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_about.delete_one({"username": self._user_to_be_deleted})

        self._logger.debug(f"Deleted user information for user {self._user_to_be_deleted}.")

    def start_deletion_process(self) -> None:
        """
        Start the user deletion process.
        """
        posts_uid = self._get_posts_uid_by_user()
        self._remove_all_posts()
        self._remove_all_related_comments(posts_uid)
        self._remove_all_user_data()


##################################################################################################

# user utils

##################################################################################################


class UserUtils:
    def __init__(self, db_handler: Database, logger: logging.Logger) -> None:
        """
        Initialize the UserUtils class.

        Args:
            db_handler (Database): The database handler.
            logger (logging.Logger): The logger instance.
        """
        self._db_handler = db_handler
        self._logger = logger

    def get_all_username(self) -> list[str]:
        """
        Get a list of all usernames.

        Returns:
            list[str]: A list of all usernames.
        """
        all_user_info = self._db_handler.user_info.find({})
        return [user_info.get("username") for user_info in all_user_info]

    def get_all_username_gallery_enabled(self) -> list[str]:
        """
        Get a list of all usernames with gallery enabled.

        Returns:
            list[str]: A list of usernames with gallery enabled.
        """
        all_user_info = self._db_handler.user_info.find({"gallery_enabled": True})
        return [user_info.get("username") for user_info in all_user_info]

    def get_all_username_changelog_enabled(self) -> list[str]:
        """
        Get a list of all usernames with changelog enabled.

        Returns:
            list[str]: A list of usernames with changelog enabled.
        """
        all_user_info = self._db_handler.user_info.find({"changelog_enabled": True})
        return [user_info.get("username") for user_info in all_user_info]

    def get_user_info(self, username: str) -> UserInfo:
        """
        Get user information by username.

        Args:
            username (str): The username.

        Returns:
            UserInfo: The user information.
        """
        user_info = self._db_handler.user_info.find_one({"username": username})
        if user_info is None:
            return None
        user_info.pop("_id", None)
        return UserInfo(**user_info)

    def get_user_creds(self, email: str) -> UserCreds:
        """
        Get user credentials by email.

        Args:
            email (str): The email address.

        Returns:
            UserCreds: The user credentials.
        """
        user_creds = self._db_handler.user_creds.find_one({"email": email})
        if user_creds is None:
            return None
        user_creds.pop("_id", None)
        return UserCreds(**user_creds)

    def delete_user(self, username: str) -> None:
        """
        Delete a user by username.

        Args:
            username (str): The username of the user to be deleted.
        """
        user_deletion = UserDeletionSetup(
            username=username, db_handler=self._db_handler, logger=self._logger
        )
        user_deletion.start_deletion_process()

    def create_user(self, form: SignUpForm) -> str:
        """
        Create a new user.

        Args:
            form (SignUpForm): The form containing user registration data.

        Returns:
            str: The username of the newly created user.
        """
        user_registration = NewUserSetup(form, self._db_handler, self._logger)
        return user_registration.create_user()

    def total_view_increment(self, username: str) -> None:
        """
        Increment the total view count for a user.

        Args:
            username (str): The username.
        """
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments={"total_views": 1}
        )


user_utils = UserUtils(db_handler=mongodb, logger=logger)
