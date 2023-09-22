import re
import string
import random
from datetime import datetime, timedelta
from application.services.mongo import MyDatabase

###################################################################

# form validator

###################################################################


class FormValidator:

    def validate_email(self, email: str) -> bool:
        """Check if email is valid. E.g., test123@test.com.

        Args:
            email (str): plain text email address.

        Returns:
            bool: True is email address is valid..
        """
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z]{2,7})+$"
        if re.match(email_regex, email):
            return True
        return False
    
    def validate_password(self, password:str) -> bool:
        """Check if the plain (unhashed) password is valid. Password is at least 8 character, and must contains an uppercase/lowercase/number character.

        Args:
            password (str): plain text password.

        Returns:
            bool: True if password is valid
        """
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$"
        if re.match(password_regex, password):
            return True
        return False
    
    def validate_username(self, username: str) -> bool:
        """Check if username is valid. Username is letters, numbers, dot, dash, underscore only.

        Args:
            username (str): plain text username.

        Returns:
            bool: True if username is valid.
        """
        username_regex = r"^[a-zA-Z0-9][a-zA-Z0-9.\-_]*[a-zA-Z0-9]$"
        if re.match(username_regex, username):
            return True
        return False
    
    def validate_blogname(self, blogname: str) -> bool:
        """Check if the blog name is not longer than 20 characters.

        Args:
            blogname (str): plain text blog name.

        Returns:
            bool: True if the blog name is valid.
        """
        blogname_regex = r"^.{1,20}$"
        if re.match(blogname_regex, blogname):
            return True
        return False
    
###################################################################

# uid generator

###################################################################
    

class uid_generator:
    def __init__(self, db_handler: MyDatabase) -> None:
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

def get_today(env):

    if env == "debug":
        today = datetime.now()
    elif env == "prod":
        today = datetime.now() + timedelta(hours=8)
    else: 
        raise ValueError("Unknown enviroment argument.")
    return today

def switch_to_bool(switch_value: str | None) -> bool:
    """convert the return value of the bootstrap switch from the form into boolean.

    Args:
        switch_value (str | None): return value of switch checkbox from the form, possible values: "on" and None.

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
