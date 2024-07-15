"""
This module collects the common utulity functions from the application.
"""

import random
import re
import string
from math import ceil

from flask import Request, abort

from blogyourway.mongo import Database

###################################################################

# form validator

###################################################################


class FormValidator:
    def validate_email(self, email: str) -> bool:
        """
        Validate an email address.

        Parameters:
        - email (str): a string of the email address to be validated.

        Returns:
        - bool: True if the email address is valid; False otherwise.

        Criteria:
        - Must have a valid format with '@' and a top-level domain (TLD).
        - Local part (before '@') must not have spaces or start/end with a space.
        - Domain part (after '@') must not have consecutive dots or special characters.
        - Should not be empty and should contain both local and domain parts.

        Example:
        - validate_email("john.doe@example.com") -> True
        - validate_email("invalid.email") -> False
        """

        email_regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z]{2,7})+$")
        if re.match(email_regex, email):
            return True
        return False

    def validate_password(self, password: str) -> bool:
        """
        Validate a password.

        Parameters:
        - password (str): a string of the password to be validated.

        Returns:
        - bool: True if the password is valid; False otherwise.

        Criteria:
        - At least 8 characters long.
        - At least one uppercase letter.
        - At least one lowercase letter.
        - At least one number.
        - May include special characters.
        - No spaces allowed (leading or trailing).

        Example:
        - validate_password("P@ssw0rd") -> True
        - validate_password("short") -> False
        - validate_password("Pwd 123") -> False
        """

        password_regex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$")
        if re.match(password_regex, password):
            return True
        return False

    def validate_username(self, username: str) -> bool:
        """
        Validate a username.

        Parameters:
        - username (str): a string of the username to be validated.

        Returns:
        - bool: True if the username is valid; False otherwise.

        Criteria:
        - Must start with a lowercase letter or digit.
        - Can have zero or more lowercase letters, digits, or hyphens in the middle.
        - Optionally, may end with a lowercase letter or digit.
        """
        username_regex = re.compile(r"^[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?$")
        if re.match(username_regex, username):
            return True
        return False

    def validate_blogname(self, blogname: str) -> bool:
        """Check if the blog name is not longer than 20 characters.

        Args:
        - blogname (str): a string of the blog name to be validated.

        Returns:
        - bool: True if the blog name is valid.
        """
        blogname_regex = re.compile(r"^.{1,20}$")
        if re.match(blogname_regex, blogname):
            return True
        return False


###################################################################

# uid generator

###################################################################


class UIDGenerator:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def generate_comment_uid(self) -> str:
        """look into the comment database and give a unique id for new comment

        Returns:
            str: an unique comment uid string
        """

        alphabet = string.ascii_lowercase + string.digits
        while True:
            comment_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.comment.exists("comment_uid", comment_uid):
                return comment_uid

    def generate_post_uid(self) -> str:
        """look into the post database and give a unique id for new post

        Returns:
            str: an unique post uid string
        """
        alphabet = string.ascii_lowercase + string.digits
        while True:
            post_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.post_info.exists("post_uid", post_uid):
                return post_uid


###################################################################

# some other utility functions

###################################################################


def switch_to_bool(switch_value: str | None) -> bool:
    """convert the return value of the bootstrap switch from the form into boolean.

    Args:
        switch_value (str | None): return value of switch checkbox from the form,
        possible values: "on" and None.

    Returns:
        bool: a boolean value.
    """
    if switch_value is None:
        return False
    return True


def string_truncate(text: str, max_len: int) -> str:
    """Truncate the input string to the given max len, with the trailing dot dot dot.

    If the input is shorter, nothing will be changed.

    Args:
        text (str): string to be truncated.
        max_len (int): shorten the string to this length at maximum (dot dot dot not included).

    Returns:
        str: truncated string.
    """
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."


def sort_dict(_dict: dict) -> dict:
    sorted_dict_key = sorted(_dict, key=_dict.get, reverse=True)
    sorted_dict = {}
    for key in sorted_dict_key:
        sorted_dict[key] = _dict[key]
    return sorted_dict


class Paging:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler
        self._has_setup = False
        self._allow_previous_page = None
        self._allow_next_page = None
        self._current_page = None

    def setup(self, username, database, current_page, num_per_page):
        self._has_setup = True
        self._database = database
        self._allow_previous_page = False
        self._allow_next_page = False
        self._current_page = current_page

        # set up for pagination
        # factory mode
        if self._database == "post_info":
            num_not_archieved = self._db_handler.post_info.count_documents(
                {"author": username, "archived": False}
            )
        elif self._database == "project_info":
            num_not_archieved = self._db_handler.project_info.count_documents(
                {"author": username, "archived": False}
            )
        else:
            raise Exception("Unknown database option for paging class.")

        if num_not_archieved == 0:
            max_page = 1
        else:
            max_page = ceil(num_not_archieved / num_per_page)

        if current_page > max_page or current_page < 1:
            # not a legal page number
            abort(404)

        if current_page * num_per_page < num_not_archieved:
            self._allow_next_page = True

        if current_page > 1:
            self._allow_previous_page = True

        return self

    @property
    def is_previous_page_allowed(self):
        if not self._has_setup:
            raise AttributeError("pagination has not setup yet.")
        return self._allow_previous_page

    @property
    def is_next_page_allowed(self):
        if not self._has_setup:
            raise AttributeError("pagination has not setup yet.")
        return self._allow_next_page

    @property
    def current_page(self):
        if not self._has_setup:
            raise AttributeError("pagination has not setup yet.")
        return self._current_page


def process_tags(tag_string: str) -> list[str]:
    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]


def process_form_images(request: Request) -> list[dict[str, str]]:

    images = []
    num_of_images = len([i for i in request.form.keys() if "url" in i])
    for i in range(1, num_of_images + 1):
        image = {
            "url": request.form.get(f"url-{i}"),
            "caption": request.form.get(f"caption-{i}"),
        }
        images.append(image)
    return images
