import requests
import bcrypt
import random
import string
import re
from math import ceil
from datetime import datetime, timedelta
from flask import flash, render_template, abort, request, Request
from flask_login import current_user
from bs4 import BeautifulSoup
from application.extensions.mongo import my_database, MyDatabase
from application.extensions.log import logger, MyLogger
from application.config import ENV, RECAPTCHA_SECRET

###################################################################

# html formatter

###################################################################


class HTMLFormatter:
    def __init__(self, html):

        self.__soup = BeautifulSoup(html, "html.parser")

    def add_padding(self):

        # add padding for all first level tags, except figure and img
        tags = self.__soup.find_all(
            lambda tag: tag.name not in ["figure", "img"], recursive=False
        )
        for tag in tags:
            current_style = tag.get("style", "")
            new_style = f"{current_style} padding-top: 10px; padding-bottom: 10px; "
            tag["style"] = new_style

        return self

    def change_heading_font(self):

        # Modify the style attribute for each heading tag
        headings = self.__soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        # Modify the style attribute for each heading tag
        for heading in headings:
            current_style = heading.get("style", "")
            new_style = f"{current_style} font-family: 'Ubuntu', 'Arial', sans-serif;;"
            heading["style"] = new_style

        return self

    def modify_figure(self, max_width="90%"):

        # center image and modify size
        imgs = self.__soup.find_all(["img"])
        for img in imgs:
            current_style = img.get("style", "")
            new_style = f"{current_style} display: block; margin: 0 auto; max-width: {max_width}; min-width: 30% ;height: auto;"
            img["style"] = new_style

        # center caption
        captions = self.__soup.find_all(["figcaption"])
        for caption in captions:
            current_style = caption.get("style", "")
            new_style = f"{current_style} text-align: center"
            caption["style"] = new_style

        return self

    def to_string(self):

        return str(self.__soup)


def html_to_blogpost(html):

    formatter = HTMLFormatter(html)
    blogpost = formatter.add_padding().change_heading_font().modify_figure().to_string()

    return blogpost

def html_to_about(html):

    formatter = HTMLFormatter(html)
    about = formatter.add_padding().modify_figure(max_width="50%").to_string()

    return about

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

# user registration

###################################################################

def get_today(env):

    if env == "debug":
        today = datetime.now()
    elif env == "prod":
        today = datetime.now() + timedelta(hours=8)
    return today


class NewUserSetup:
    def __init__(self, request: Request, db_handler: MyDatabase, logger: MyLogger):

        self._reg_form = request.form.to_dict()
        self._db_handler = db_handler
        self._logger = logger

    def _form_validated(self) -> bool:

        validator = FormValidator()

        if not validator.validate_email(self._reg_form["email"]):
            return False
        if not validator.validate_password(self._reg_form["password"]):
            return False
        if not validator.validate_username(self._reg_form["username"]):
            return False
        if not validator.validate_blogname(self._reg_form["blogname"]):
            return False
        return True    

    def _no_duplicates(self) -> bool:

        for field in ["email", "username", "blogname"]:

            if self._db_handler.user_login.exists(field, self._reg_form[field]):
                flash(f"{field.capitalize()} is already used. Please try another one.", category="error")
                self._logger.user.registration_failed(
                    msg=f'{field} {self._reg_form[field]} already used',
                    request=request,
                )
                return True

        return False

    def _hash_password(self, password: str) -> str:
        """Hashing user input password.

        Args:
            password (str): plain text password.

        Returns:
            str: a string of the hashed password encoded back to utf-8.
        """

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
        hashed_pw = hashed_pw.decode("utf-8")
        return hashed_pw

    def _create_user_login(
        self, username: str, email: str, hashed_password: str
    ) -> dict:

        new_user_login = {
            "username": username,
            "email": email,
            "password": hashed_password,
        }
        return new_user_login

    def _create_user_info(self, username: str, email: str, blogname: str) -> dict:

        new_user_info = {
            "username": username,
            "email": email,
            "blogname": blogname,
            "banner_url": "",
            "profile_img_url": "",
            "short_bio": "",
            "social_links": [],
            "change_log_enabled": False,
            "portfolio_enabled": True,
            "created_at": get_today(env=ENV),
        }
        return new_user_info

    def _create_user_about(self, username: str) -> dict:

        new_user_about = {"username": username, "about": ""}
        return new_user_about

    def create_user(self):

        if not self._form_validated():
            return render_template("register.html")

        if self._no_duplicates():
            return render_template("register.html")

        hashed_pw = self._hash_password(self._reg_form["password"])
        new_user_login = self._create_user_login(
            self._reg_form["username"], self._reg_form["email"], hashed_pw
        )
        new_user_info = self._create_user_info(
            self._reg_form["username"],
            self._reg_form["email"],
            self._reg_form["blogname"],
        )
        new_user_about = self._create_user_about(self._reg_form["username"])

        self._db_handler.user_login.insert_one(new_user_login)
        self._db_handler.user_info.insert_one(new_user_info)
        self._db_handler.user_about.insert_one(new_user_about)

        return self._reg_form["username"]


def create_user(request: request) -> str:

    user_registration = NewUserSetup(request, my_database, logger)
    return user_registration.create_user()

###################################################################

# create new comment

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


class CommentSetup:
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

    comment_setup = CommentSetup(
        request=request,
        post_uid=post_uid,
        comment_uid_generator=uid_generator,
        db_handler=db,
        commenter=current_user,
    )
    comment_setup.create_comment()


###################################################################

# to set pagination

###################################################################


class Paging:
    def __init__(self, db_handler: MyDatabase) -> None:

        self._db_handler = db_handler
        self._has_setup = False
        self._allow_previous_page = None
        self._allow_next_page = None
        self._current_page = None

    def setup(self, username, current_page, posts_per_page):

        self._has_setup = True
        self._allow_previous_page = False
        self._allow_next_page = False
        self._current_page = current_page

        # set up for pagination
        num_not_archieved = self._db_handler.post_info.count_documents(
            {"author": username, "archived": False}
        )
        if num_not_archieved == 0:
            max_page = 1
        else:
            max_page = ceil(num_not_archieved / posts_per_page)

        if current_page > max_page:
            # not a legal page number
            abort(404)

        if current_page * posts_per_page < num_not_archieved:
            self._allow_previous_page = True

        if current_page > 1:
            self._allow_next_page = True

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


paging = Paging(db_handler=my_database)

###################################################################

# to find tags from a user

###################################################################


class All_Tags:
    def __init__(self, db_handler: MyDatabase) -> None:

        self._db_handler = db_handler

    def from_user(self, username):

        result = self._db_handler.post_info.find(
            {"author": username, "archived": False}
        )
        tags_dict = {}
        for post in result:
            post_tags = post["tags"]
            for tag in post_tags:
                if tag not in tags_dict:
                    tags_dict[tag] = 1
                else:
                    tags_dict[tag] += 1

        sorted_tags_key = sorted(tags_dict, key=tags_dict.get, reverse=True)
        sorted_tags = {}
        for key in sorted_tags_key:
            sorted_tags[key] = tags_dict[key]

        return sorted_tags


all_tags = All_Tags(db_handler=my_database)

###################################################################

# post utilities

###################################################################


class PostUtils:
    def __init__(self, db_handler: MyDatabase):

        self._db_handler = db_handler

    def find_featured_posts_info(self, username: str):

        result = (
            self._db_handler.post_info
            .find({"author": username, "featured": True, "archived": False})
            .sort("created_at", -1)
            .limit(10)
            .as_list()
        )
        return result

    def find_all_posts_info(self, username: str):

        result = (
            self._db_handler.post_info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_all_archived_posts_info(self, username: str):

        result = (
            self._db_handler.post_info
            .find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_posts_with_pagination(
        self, username: str, page_number: int, posts_per_page: int
    ):
        
        if page_number == 1:
            result = (
                self._db_handler.post_info
                .find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(posts_per_page)
                .as_list()
            )

        elif page_number > 1:
            result = (
                self._db_handler.post_info
                .find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * posts_per_page)
                .limit(posts_per_page)
                .as_list()
            )

        return result

    def get_full_post(self, post_uid: str):

        target_post = self._db_handler.post_info.find_one({"post_uid": post_uid})
        target_post_content = self._db_handler.post_content.find_one(
            {"post_uid": post_uid}
        )["content"]
        target_post["content"] = target_post_content

        return target_post


post_utils = PostUtils(db_handler=my_database)

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
