import random
import string
from math import ceil

from bs4 import BeautifulSoup
from flask import abort
from markdown import Markdown
from typing_extensions import Self

from app.mongo import Database


##################################################################################################

# uid generator

##################################################################################################


class UIDGenerator:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the UIDGenerator with a database handler.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def generate_comment_uid(self) -> str:
        """
        Look into the comment database and generate a unique ID for a new comment.

        Returns:
            str: A unique comment UID string.
        """
        alphabet = string.ascii_lowercase + string.digits
        while True:
            comment_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.comment.exists("comment_uid", comment_uid):
                return comment_uid

    def generate_post_uid(self) -> str:
        """
        Look into the post database and generate a unique ID for a new post.

        Returns:
            str: A unique post UID string.
        """
        alphabet = string.ascii_lowercase + string.digits
        while True:
            post_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.post_info.exists("post_uid", post_uid):
                return post_uid

    def generate_project_uid(self) -> str:
        """
        Look into the project database and generate a unique ID for a new project.

        Returns:
            str: A unique project UID string.
        """
        alphabet = string.ascii_lowercase + string.digits
        while True:
            project_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.project_info.exists("project_uid", project_uid):
                return project_uid
    
    def generate_changelog_uid(self) -> str:
        alphabet = string.ascii_lowercase + string.digits
        while True:
            changelog_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.changelog.exists("changelog_uid", changelog_uid):
                return changelog_uid



##################################################################################################

# formatter tool

##################################################################################################


class HTMLFormatter:
    def __init__(self, html: str) -> None:
        """
        Initialize the HTMLFormatter.

        Args:
            html (str): A string that is already HTML.
        """
        self._soup = BeautifulSoup(html, "html.parser")

    def add_padding(self) -> Self:
        """
        Add padding to HTML elements except 'figure' and 'img'.

        Returns:
            HTMLFormatter: The formatter instance.
        """
        blocks = self._soup.find_all(
            lambda tag: tag.name not in ["figure", "img"], recursive=False
        )
        for block in blocks:
            current_class = block.get("class", [])
            current_class.append("py-1")
            block["class"] = current_class

        return self

    def change_headings(self) -> Self:
        """
        Change the heading levels in the HTML.

        Returns:
            HTMLFormatter: The formatter instance.
        """
        small_headings = self._soup.find_all("h3")
        for heading in small_headings:
            heading.name = "h5"

        medium_headings = self._soup.find_all("h2")
        for heading in medium_headings:
            heading.name = "h3"

        big_headings = self._soup.find_all("h1")
        for heading in big_headings:
            heading.name = "h2"
            heading["class"] = "py-3"

        return self

    def modify_figure(self) -> Self:
        """
        Modify figure and image elements to center them and adjust their sizes.

        Returns:
            HTMLFormatter: The formatter instance.
        """
        figures = self._soup.find_all("figure")
        for figure in figures:
            current_class = figure.get("class", [])
            current_class.extend(["figure", "w-100", "mx-auto"])
            figure["class"] = current_class

        imgs = self._soup.find_all(["img"])
        for img in imgs:
            img_src = img["src"]
            img["src"] = ""
            img["data-src"] = img_src
            current_class = img.get("class", [])
            current_class.extend(["lazyload", "figure-img", "img-fluid", "rounded", "w-100"])
            img["class"] = current_class

        captions = self._soup.find_all(["figcaption"])
        for caption in captions:
            current_class = caption.get("class", [])
            current_class.extend(["figure-caption", "text-center", "py-2"])
            caption["class"] = current_class

        return self
    
    def modify_hyperlink(self) -> Self:
        """
        Apply color theme to hyperlinks in the post.

        Returns:
            HTMLFormatter: The formatter instance.
        """
        links = self._soup.find_all("a")
        for link in links:
            current_class = link.get("class", [])
            current_class.extend(["main-theme-link"])
            link["class"] = current_class

        return self
        

    def to_string(self) -> str:
        """
        Convert the formatted HTML back to a string.

        Returns:
            str: The formatted HTML string.
        """
        return str(self._soup)


def convert_post_content(content: str) -> str:
    """
    Convert the original text to HTML for display on the blog post page.

    Args:
        content (str): The original markdown content.

    Returns:
        str: The converted HTML content.
    """
    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes", "toc"])
    html = md.convert("[TOC]\r\n" + content)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().modify_hyperlink().to_string()

    return html


def convert_about(about: str) -> str:
    """
    Convert the original text to HTML for display on the about page.

    Args:
        about (str): The original markdown content.

    Returns:
        str: The converted HTML content.
    """
    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    html = md.convert(about)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html


def convert_project_content(content: str) -> str:
    """
    Convert the original text to HTML for display on the project page.

    Args:
        content (str): The original markdown content.

    Returns:
        str: The converted HTML content.
    """
    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes", "toc"])
    html = md.convert(content)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html

def convert_changelog_content(content: str) -> str:

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes"])
    html = md.convert(content)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html


##################################################################################################

# pagination tool

##################################################################################################


class Paging:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the Paging class with a database handler.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler
        self._has_setup = False
        self._allow_previous_page = None
        self._allow_next_page = None
        self._current_page = None

    def setup(self, username: str, database: str, current_page: int, num_per_page: int) -> Self:
        """
        Set up pagination for a user and database.

        Args:
            username (str): The username.
            database (str): The name of the database.
            current_page (int): The current page number.
            num_per_page (int): The number of items per page.

        Returns:
            Paging: The paging instance.

        Raises:
            Exception: If the database option is unknown.
            abort: If the current page is not a legal page number.
        """
        self._has_setup = True
        self._database = database
        self._allow_previous_page = False
        self._allow_next_page = False
        self._current_page = current_page

        # set up for pagination
        # factory mode
        if self._database == "post_info":
            num_not_archived = self._db_handler.post_info.count_documents(
                {"author": username, "archived": False}
            )
        elif self._database == "project_info":
            num_not_archived = self._db_handler.project_info.count_documents(
                {"author": username, "archived": False}
            )
        elif self._database == "changelog":
            num_not_archived = self._db_handler.changelog.count_documents(
                {"author": username, "archived": False}
            )
        else:
            raise Exception("Unknown database option for paging class.")

        if num_not_archived == 0:
            max_page = 1
        else:
            max_page = ceil(num_not_archived / num_per_page)

        if current_page > max_page or current_page < 1:
            # not a legal page number
            abort(404)

        if current_page * num_per_page < num_not_archived:
            self._allow_next_page = True

        if current_page > 1:
            self._allow_previous_page = True

        return self

    @property
    def is_previous_page_allowed(self) -> bool:
        """
        Check if the previous page is allowed.

        Returns:
            bool: True if the previous page is allowed, False otherwise.

        Raises:
            AttributeError: If pagination has not been set up yet.
        """
        if not self._has_setup:
            raise AttributeError("Pagination has not been set up yet.")
        return self._allow_previous_page

    @property
    def is_next_page_allowed(self) -> bool:
        """
        Check if the next page is allowed.

        Returns:
            bool: True if the next page is allowed, False otherwise.

        Raises:
            AttributeError: If pagination has not been set up yet.
        """
        if not self._has_setup:
            raise AttributeError("Pagination has not been set up yet.")
        return self._allow_next_page

    @property
    def current_page(self) -> int:
        """
        Get the current page number.

        Returns:
            int: The current page number.

        Raises:
            AttributeError: If pagination has not been set up yet.
        """
        if not self._has_setup:
            raise AttributeError("Pagination has not been set up yet.")
        return self._current_page


##################################################################################################

# some other utility functions

##################################################################################################


def slicing_title(text: str, max_len: int) -> str:
    """
    Truncate the input string to the given max length, with trailing ellipsis if truncated.

    Args:
        text (str): The string to be truncated.
        max_len (int): The maximum length of the string (excluding ellipsis).

    Returns:
        str: The truncated string.
    """
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."


def sort_dict(_dict: dict[str, int]) -> dict[str, int]:
    """
    Sort the dictionary by value in descending order.

    Args:
        _dict (dict): The unsorted dictionary.

    Returns:
        dict: The sorted dictionary.
    """
    sorted_dict_key = sorted(_dict, key=_dict.get, reverse=True)
    sorted_dict = {}
    for key in sorted_dict_key:
        sorted_dict[key] = _dict[key]
    return sorted_dict


def process_tags(tag_string: str) -> list[str]:
    """
    Process a comma-separated tag string into a list of tags.

    Args:
        tag_string (str): The comma-separated tag string.

    Returns:
        list[str]: The list of processed tags.
    """
    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]
