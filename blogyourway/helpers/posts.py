from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from typing import List

from bs4 import BeautifulSoup
from flask import Request, abort
from flask_login import current_user

from blogyourway.config import ENV
from blogyourway.helpers.common import FormValidator, MyDataClass, UIDGenerator, get_today
from blogyourway.services.mongo import Database, mongodb

###################################################################

# create new post

###################################################################


@dataclass
class ArticleInfo(MyDataClass):
    article_uid: str
    title: str
    subtitle: str
    author: str
    tags: List[str]
    cover_url: str
    created_at: datetime = field(init=False)
    last_updated: datetime = field(init=False)
    archived: bool = False
    featured: bool = False
    views: int = 0
    reads: int = 0

    def __post_init__(self):
        self.created_at = get_today(env=ENV)
        self.last_updated = get_today(env=ENV)


@dataclass
class ArticleContent(MyDataClass):
    article_uid: str
    author: str
    content: str


def process_tags(tag_string: str) -> list:
    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]


class NewArticleSetup:
    def __init__(self, article_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._article_uid = article_uid_generator.generate_article_uid()
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator):
        return True

    def _create_article_info(self, request: Request, author_name: str) -> dict:
        new_article_info = ArticleInfo(
            article_uid=self._article_uid,
            title=request.form.get("title"),
            subtitle=request.form.get("subtitle"),
            author=author_name,
            tags=process_tags(request.form.get("tags")),
            cover_url=request.form.get("cover_url"),
        )
        return new_article_info.as_dict()

    def _create_article_content(self, request: Request, author_name: str) -> dict:
        new_article_content = ArticleContent(
            article_uid=self._article_uid, author=author_name, content=request.form.get("content")
        )
        return new_article_content.as_dict()

    def _increment_tags_for_user(self, new_article_info: dict) -> None:
        username = new_article_info.get("author")
        tags = new_article_info.get("tags")
        tags_increments = {f"tags.{tag}": 1 for tag in tags}
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments=tags_increments, upsert=True
        )

    def create_article(self, author_name: str, request: Request) -> str | None:
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return None
        # validated
        new_article_info = self._create_article_info(author_name=author_name, request=request)
        new_article_content = self._create_article_content(author_name=author_name, request=request)

        self._db_handler.article_info.insert_one(new_article_info)
        self._db_handler.article_content.insert_one(new_article_content)
        self._increment_tags_for_user(new_article_info)

        return self._article_uid


def create_article(request):
    uid_generator = UIDGenerator(db_handler=mongodb)

    new_article_setup = NewArticleSetup(article_uid_generator=uid_generator, db_handler=mongodb)
    new_article_uid = new_article_setup.create_article(
        author_name=current_user.username, request=request
    )
    return new_article_uid


###################################################################

# updating a post

###################################################################


@dataclass
class UpdatedArticleInfo(MyDataClass):
    title: str
    subtitle: str
    tags: List[str]
    cover_url: str
    last_updated: datetime = field(init=False)

    def __post_init__(self):
        self.last_updated = get_today(env=ENV)


@dataclass
class UpdatedArticleContent(MyDataClass):
    content: str


class ArticleUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator):
        return True

    def _update_tags_for_user(self, article_uid: str, new_tags: dict) -> None:
        article_info = self._db_handler.article_info.find_one({"article_uid": article_uid})
        author = article_info.get("author")
        old_tags = article_info.get("tags")
        tags_reduction = {f"tags.{tag}": -1 for tag in old_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": author}, increments=tags_reduction
        )
        tags_increment = {f"tags.{tag}": 1 for tag in new_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": author}, increments=tags_increment, upsert=True
        )

    def _updated_article_info(self, request: Request) -> dict:
        updated_article_info = UpdatedArticleInfo(
            title=request.form.get("title"),
            subtitle=request.form.get("subtitle"),
            tags=process_tags(request.form.get("tags")),
            cover_url=request.form.get("cover_url"),
        )
        return updated_article_info.as_dict()

    def _updated_article_content(self, request: Request) -> dict:
        updated_article_content = UpdatedArticleContent(content=request.form.get("content"))
        return updated_article_content.as_dict()

    def update_article(self, article_uid: str, request: Request):
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return
        # validated
        updated_article_info = self._updated_article_info(request=request)
        updated_article_content = self._updated_article_content(request=request)

        self._update_tags_for_user(article_uid, updated_article_info.get("tags"))
        self._db_handler.article_info.update_values(
            filter={"article_uid": article_uid}, update=updated_article_info
        )
        self._db_handler.article_content.update_values(
            filter={"article_uid": article_uid}, update=updated_article_content
        )


def update_post(article_uid: str, request: Request):
    post_update_setup = ArticleUpdateSetup(db_handler=mongodb)
    post_update_setup.update_article(article_uid=article_uid, request=request)


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
        tags = self.__soup.find_all(lambda tag: tag.name not in ["figure", "img"], recursive=False)
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


def html_to_article(html):
    formatter = HTMLFormatter(html)
    article = formatter.add_padding().change_heading_font().modify_figure().to_string()

    return article


def html_to_about(html):
    formatter = HTMLFormatter(html)
    about = formatter.add_padding().modify_figure(max_width="50%").to_string()

    return about


###################################################################

# blogpost pagination

###################################################################


class Paging:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler
        self._has_setup = False
        self._allow_previous_page = None
        self._allow_next_page = None
        self._current_page = None

    def setup(self, username, current_page, articles_per_page):
        self._has_setup = True
        self._allow_previous_page = False
        self._allow_next_page = False
        self._current_page = current_page

        # set up for pagination
        num_not_archieved = self._db_handler.article_info.count_documents(
            {"author": username, "archived": False}
        )
        if num_not_archieved == 0:
            max_page = 1
        else:
            max_page = ceil(num_not_archieved / articles_per_page)

        if current_page > max_page or current_page < 1:
            # not a legal page number
            abort(404)

        if current_page * articles_per_page < num_not_archieved:
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


paging = Paging(db_handler=mongodb)


###################################################################

# article utilities

###################################################################


class ArticleUtils:
    def __init__(self, db_handler: Database):
        self._db_handler = db_handler

    def get_all_article_uid(self) -> list:
        all_article_info = self._db_handler.article_info.find({})
        all_article_uid = [article_info.get("article_uid") for article_info in all_article_info]
        return all_article_uid

    def get_all_author(self) -> list:
        all_article_info = self._db_handler.article_info.find({})
        all_author = [article_info.get("author") for article_info in all_article_info]
        return all_author

    def get_all_last_update(self) -> list:
        all_article_info = self._db_handler.article_info.find({})
        all_last_updated = [article_info.get("last_updated") for article_info in all_article_info]
        return all_last_updated

    def find_featured_articles_info(self, username: str):
        result = (
            self._db_handler.article_info.find(
                {"author": username, "featured": True, "archived": False}
            )
            .sort("created_at", -1)
            .limit(10)
            .as_list()
        )
        for post in result:
            post["created_at"] = post.get("created_at").strftime("%B %d, %Y")
        return result

    def find_all_articles_info(self, username: str):
        result = (
            self._db_handler.article_info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_all_archived_articles_info(self, username: str):
        result = (
            self._db_handler.article_info.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_articles_with_pagination(
        self, username: str, page_number: int, articles_per_page: int
    ):
        if page_number == 1:
            result = (
                self._db_handler.article_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(articles_per_page)
                .as_list()
            )

        elif page_number > 1:
            result = (
                self._db_handler.article_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * articles_per_page)
                .limit(articles_per_page)
                .as_list()
            )

        return result

    def get_full_article(self, article_uid: str):
        target_article = self._db_handler.article_info.find_one({"article_uid": article_uid})
        target_article_content = self._db_handler.article_content.find_one(
            {"article_uid": article_uid}
        ).get("content")
        target_article["content"] = target_article_content

        return target_article

    def read_increment(self, article_uid: str) -> None:
        self._db_handler.article_info.make_increments(
            filter={"article_uid": article_uid}, increments={"reads": 1}
        )

    def view_increment(self, article_uid: str) -> None:
        self._db_handler.article_info.make_increments(
            filter={"article_uid": article_uid}, increments={"views": 1}
        )


article_utils = ArticleUtils(db_handler=mongodb)
