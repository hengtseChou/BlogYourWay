from math import ceil

from bs4 import BeautifulSoup
from flask import Request, abort
from flask_login import current_user

from application.config import ENV
from application.services.mongo import MyDatabase, my_database
from application.utils.common import FormValidator, UIDGenerator, get_today

###################################################################

# create new post

###################################################################


def process_tags(tag_string: str):
    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]


class NewPostSetup:
    def __init__(self, post_uid_generator: UIDGenerator, db_handler: MyDatabase) -> None:
        self._post_uid = post_uid_generator.generate_post_uid()
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator):
        return True

    def _create_post_info(self, request: Request, author_name: str) -> dict:
        new_post_info = {
            "post_uid": self._post_uid,
            "title": request.form.get("title"),
            "subtitle": request.form.get("subtitle"),
            "author": author_name,
            "tags": process_tags(request.form.get("tags")),
            "banner_url": request.form.get("banner_url"),
            "created_at": get_today(env=ENV),
            "last_updated": get_today(env=ENV),
            "archived": False,
            "featured": False,
            "views": 0,
            "reads": 0,
        }
        return new_post_info

    def _create_post_content(self, request: Request, author_name: str) -> dict:
        new_post_content = {
            "post_uid": self._post_uid,
            "author": author_name,
            "content": request.form.get("content"),
        }
        return new_post_content

    def _create_post_view_sources(self, author_name: str) -> dict:
        new_post_view_sources = {
            "post_uid": self._post_uid,
            "author": author_name,
            "sources": {},
        }
        return new_post_view_sources

    def create_post(self, author_name: str, request: Request) -> str:
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return "Unvalidated"
        # validated
        new_post_info = self._create_post_info(author_name=author_name, request=request)
        new_post_content = self._create_post_content(
            author_name=author_name, request=request
        )
        new_post_view_sources = self._create_post_view_sources(author_name)

        self._db_handler.post_info.insert_one(new_post_info)
        self._db_handler.post_content.insert_one(new_post_content)
        self._db_handler.post_view_sources.insert_one(new_post_view_sources)

        return self._post_uid


def create_post(request):
    uid_generator = UIDGenerator(db_handler=my_database)

    new_post_setup = NewPostSetup(post_uid_generator=uid_generator, db_handler=my_database)
    new_post_uid = new_post_setup.create_post(
        author_name=current_user.username, request=request
    )
    return new_post_uid


###################################################################

# updating a post

###################################################################


class PostUpdateSetup:
    def __init__(self, db_handler=MyDatabase) -> None:
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator):
        return True

    def _updated_post_info(self, request: Request) -> dict:
        updated_post_info = {
            "title": request.form.get("title"),
            "subtitle": request.form.get("subtitle"),
            "tags": process_tags(request.form.get("tags")),
            "banner_url": request.form.get("banner_url"),
            "last_updated": get_today(env=ENV),
        }
        return updated_post_info

    def _updated_post_content(self, request: Request) -> dict:
        updated_post_content = {"content": request.form.get("content")}
        return updated_post_content

    def update_post(self, post_uid: str, request: Request):
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return
        # validated
        updated_post_info = self._updated_post_info(request=request)
        updated_post_content = self._updated_post_content(request=request)

        self._db_handler.post_info.update_values(
            filter={"post_uid": post_uid}, update=updated_post_info
        )
        self._db_handler.post_content.update_values(
            filter={"post_uid": post_uid}, update=updated_post_content
        )


def update_post(post_uid: str, request: Request):
    post_update_setup = PostUpdateSetup(db_handler=my_database)
    post_update_setup.update_post(post_uid=post_uid, request=request)


###################################################################

# formatter for posts that are saved as markdown

###################################################################


class HTMLFormatter:
    def __init__(self, html: str):
        """Format markdown strings for additional styles for different pages.

        Args:
            html (str): a string that is already html.
        """

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

    def to_string(self) -> str:
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

# counting tags in posts

###################################################################


class AllTags:
    def __init__(self, db_handler: MyDatabase) -> None:
        self._db_handler = db_handler

    def from_user(self, username):
        result = self._db_handler.post_info.find({"author": username, "archived": False})
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


all_tags = AllTags(db_handler=my_database)

###################################################################

# blogpost pagination

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

# post utilities

###################################################################


class PostUtils:
    def __init__(self, db_handler: MyDatabase):
        self._db_handler = db_handler

    def find_featured_posts_info(self, username: str):
        result = (
            self._db_handler.post_info.find(
                {"author": username, "featured": True, "archived": False}
            )
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
            self._db_handler.post_info.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_posts_with_pagination(
        self, username: str, page_number: int, posts_per_page: int
    ):
        if page_number == 1:
            result = (
                self._db_handler.post_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(posts_per_page)
                .as_list()
            )

        elif page_number > 1:
            result = (
                self._db_handler.post_info.find({"author": username, "archived": False})
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
        ).get("content")
        target_post["content"] = target_post_content

        return target_post


post_utils = PostUtils(db_handler=my_database)
