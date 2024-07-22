"""
This module collects the common utulity functions from the application.
"""

import random
import string
from math import ceil

from bs4 import BeautifulSoup
from flask import abort
from markdown import Markdown

from app.mongo import Database

##################################################################################################

# uid generator

##################################################################################################


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

    def generate_project_uid(self) -> str:

        alphabet = string.ascii_lowercase + string.digits
        while True:
            project_uid = "".join(random.choices(alphabet, k=8))
            if not self._db_handler.project_info.exists("project_uid", project_uid):
                return project_uid


##################################################################################################

# formatter tool

##################################################################################################


class HTMLFormatter:
    def __init__(self, html: str):
        """Format markdown strings for additional styles for different pages.

        Args:
            html (str): a string that is already html.
        """
        self.__soup = BeautifulSoup(html, "html.parser")

    def add_padding(self):

        blocks = self.__soup.find_all(
            lambda tag: tag.name not in ["figure", "img"], recursive=False
        )
        for block in blocks:
            current_class = block.get("class", [])
            current_class.append("py-1")
            block["class"] = current_class

        return self

    def change_headings(self):

        small_headings = self.__soup.find_all("h3")
        for heading in small_headings:
            heading.name = "h5"

        medium_headings = self.__soup.find_all("h2")
        for heading in medium_headings:
            heading.name = "h3"

        big_headings = self.__soup.find_all("h1")
        for heading in big_headings:
            heading.name = "h2"
            heading["class"] = "py-3"

        return self

    def modify_figure(self):
        # center image and modify size
        figures = self.__soup.find_all(["figure"])
        for figure in figures:
            current_class = figure.get("class", [])
            current_class.extend(["figure", "w-100", "mx-auto"])
            figure["class"] = current_class

        imgs = self.__soup.find_all(["img"])
        for img in imgs:
            img_src = img["src"]
            img["src"] = ""
            img["data-src"] = img_src
            current_class = img.get("class", [])
            current_class.extend(["lazyload", "figure-img", "img-fluid", "rounded", "w-100"])
            img["class"] = current_class

        captions = self.__soup.find_all(["figcaption"])
        for caption in captions:
            current_class = caption.get("class", [])
            current_class.extend(["figure-caption", "text-center", "py-2"])
            caption["class"] = current_class

        return self

    def to_string(self) -> str:
        return str(self.__soup)


def convert_post_content(content: str) -> str:
    """convert the original text to the html text to be displayed in the blogpost page"""

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes", "toc"])
    html = md.convert("[TOC]\r\n" + content)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html


def convert_about(about: str) -> str:
    """convert the original text to the html text to be displayed in the about page"""

    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    html = md.convert(about)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html


def convert_project_content(content: str) -> str:
    """convert the original text to the html text to be displayed in the project page"""

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes", "toc"])
    html = md.convert(content)
    formatter = HTMLFormatter(html)
    html = formatter.add_padding().change_headings().modify_figure().to_string()

    return html


##################################################################################################

# pagination tool

##################################################################################################


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


##################################################################################################

# some other utility functions

##################################################################################################


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


def sort_dict(_dict: dict[str, int]) -> dict[str, int]:
    """Sort the dictionary by value

    Args:
        _dict (dict): unsorted dict

    Returns:
        dict: sorted dict
    """
    sorted_dict_key = sorted(_dict, key=_dict.get, reverse=True)
    sorted_dict = {}
    for key in sorted_dict_key:
        sorted_dict[key] = _dict[key]
    return sorted_dict


def process_tags(tag_string: str) -> list[str]:

    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]
