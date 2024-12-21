from dataclasses import asdict
from datetime import datetime, timezone

from flask_login import current_user

from app.cache import cache, update_user_cache
from app.forms.posts import EditPostForm, NewPostForm
from app.helpers.utils import UIDGenerator, process_tags
from app.models.posts import PostContent, PostInfo
from app.mongo import Database, mongodb

##################################################################################################

# Creating a new post

##################################################################################################


class NewPostSetup:
    def __init__(self, post_uid_generator: UIDGenerator, db_handler: Database) -> None:
        """
        Initialize the NewPostSetup class.

        Args:
            post_uid_generator (UIDGenerator): The UID generator for posts.
            db_handler (Database): The database handler.
        """
        self._post_uid = post_uid_generator.generate_post_uid()
        self._db_handler = db_handler

    def _create_post_info(self, form: NewPostForm, author_name: str) -> dict:
        """
        Create a dictionary of post information.

        Args:
            form (NewPostForm): The form containing post data.
            author_name (str): The author's username.

        Returns:
            dict: A dictionary containing the post's information.
        """
        new_post_info = PostInfo(
            post_uid=self._post_uid,
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=author_name,
            tags=process_tags(form.tags.data),
            custom_slug=form.custom_slug.data,
            cover_url=form.cover_url.data,
        )
        return asdict(new_post_info)

    def _create_post_content(self, form: NewPostForm, author_name: str) -> dict:
        """
        Create a dictionary of post content.

        Args:
            form (NewPostForm): The form containing post data.
            author_name (str): The author's username.

        Returns:
            dict: A dictionary containing the post's content.
        """
        new_post_content = PostContent(
            post_uid=self._post_uid, author=author_name, content=form.editor.data
        )
        return asdict(new_post_content)

    def _increment_tags_for_user(self, new_post_info: dict) -> None:
        """
        Increment the tag counts for the user.

        Args:
            new_post_info (dict): A dictionary containing the post's information.
        """
        username = new_post_info.get("author")
        tags = new_post_info.get("tags")
        tags_increments = {f"tags.{tag}": 1 for tag in tags}
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments=tags_increments, upsert=True
        )
        update_user_cache(cache, username)

    def create_post(self, author_name: str, form: NewPostForm) -> str | None:
        """
        Create a new post in the database.

        Args:
            author_name (str): The author's username.
            form (NewPostForm): The form containing post data.

        Returns:
            str | None: The UID of the newly created post, or None if creation failed.
        """
        new_post_info = self._create_post_info(form=form, author_name=author_name)
        new_post_content = self._create_post_content(form=form, author_name=author_name)

        self._db_handler.post_info.insert_one(new_post_info)
        self._db_handler.post_content.insert_one(new_post_content)
        self._increment_tags_for_user(new_post_info)

        return self._post_uid


def create_post(form: NewPostForm) -> str:
    """
    Create a new post.

    Args:
        form (NewPostForm): The form containing post data.

    Returns:
        str: The UID of the newly created post.
    """
    uid_generator = UIDGenerator(db_handler=mongodb)
    new_post_setup = NewPostSetup(post_uid_generator=uid_generator, db_handler=mongodb)
    new_post_uid = new_post_setup.create_post(author_name=current_user.username, form=form)
    return new_post_uid


##################################################################################################

# Updating a post

##################################################################################################


class PostUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the PostUpdateSetup class.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def _update_tags_for_user(self, post_uid: str, new_tags: dict) -> None:
        """
        Update the tag counts for the user when a post is updated.

        Args:
            post_uid (str): The UID of the post being updated.
            new_tags (dict): The new tags associated with the post.
        """
        post_info = self._db_handler.post_info.find_one({"post_uid": post_uid})
        username = post_info.get("author")
        old_tags = post_info.get("tags")

        tags_reduction = {f"tags.{tag}": -1 for tag in old_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments=tags_reduction
        )
        tags_increment = {f"tags.{tag}": 1 for tag in new_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments=tags_increment, upsert=True
        )
        update_user_cache(cache, username)

    def update_post(self, post_uid: str, form: EditPostForm) -> None:
        """
        Update an existing post in the database.

        Args:
            post_uid (str): The UID of the post to update.
            form (EditPostForm): The form containing updated post data.
        """
        updated_post_info = {
            "title": form.title.data,
            "subtitle": form.subtitle.data,
            "tags": process_tags(form.tags.data),
            "cover_url": form.cover_url.data,
            "custom_slug": form.custom_slug.data,
            "last_updated": datetime.now(timezone.utc),
        }
        updated_post_content = {"content": form.editor.data}

        self._update_tags_for_user(post_uid, updated_post_info.get("tags"))
        self._db_handler.post_info.update_values(
            filter={"post_uid": post_uid}, update=updated_post_info
        )
        self._db_handler.post_content.update_values(
            filter={"post_uid": post_uid}, update=updated_post_content
        )


def update_post(post_uid: str, form: EditPostForm) -> None:
    """
    Update an existing post.

    Args:
        post_uid (str): The UID of the post to update.
        form (EditPostForm): The form containing updated post data.
    """
    post_update_setup = PostUpdateSetup(db_handler=mongodb)
    post_update_setup.update_post(post_uid=post_uid, form=form)


##################################################################################################

# Post utilities

##################################################################################################


class PostUtils:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the PostUtils class.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def get_all_posts_info(self, include_archive=False) -> list[dict]:
        """
        Get information about all posts.

        Args:
            include_archive (bool, optional): Whether to include archived posts. Defaults to False.

        Returns:
            list[dict]: A list of dictionaries containing post information.
        """
        if include_archive:
            result = self._db_handler.post_info.find({}).as_list()
        else:
            result = self._db_handler.post_info.find({"archived": False}).as_list()
        return result

    def get_featured_posts_info(self, username: str) -> list[dict]:
        """
        Get information about featured posts for a specific user.

        Args:
            username (str): The username of the post author.

        Returns:
            list[dict]: A list of dictionaries containing featured post information.
        """
        result = (
            self._db_handler.post_info.find(
                {"author": username, "featured": True, "archived": False}
            )
            .sort("created_at", -1)
            .limit(10)
            .as_list()
        )
        return result

    def get_post_infos(self, username: str, archive="exclude") -> list[dict]:
        """
        Get information about posts for a specific user.

        Args:
            username (str): The username of the post author.
            archive (str, optional): Whether to include archived posts. Defaults to "exclude". Possible values: "exclude", "include", "only".

        Returns:
            list[dict]: A list of dictionaries containing post information.
        """
        if archive == "exclude":
            result = (
                self._db_handler.post_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .as_list()
            )
        elif archive == "include":
            result = (
                self._db_handler.post_info.find({"author": username})
                .sort("created_at", -1)
                .as_list()
            )
        elif archive == "only":
            result = (
                self._db_handler.post_info.find({"author": username, "archived": True})
                .sort("created_at", -1)
                .as_list()
            )
        return result

    def get_post_infos_with_pagination(
        self, username: str, page_number: int, posts_per_page: int
    ) -> list[dict]:
        """
        Get paginated information about posts for a specific user.

        Args:
            username (str): The username of the post author.
            page_number (int): The page number.
            posts_per_page (int): The number of posts per page.

        Returns:
            list[dict]: A list of dictionaries containing post information.
        """
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

    def get_full_post(self, post_uid: str) -> dict:
        """
        Get the full information of a post, including its content.

        Args:
            post_uid (str): The UID of the post to retrieve.

        Returns:
            dict: A dictionary containing the full post information.
        """
        post = self._db_handler.post_info.find_one({"post_uid": post_uid})
        post_content = self._db_handler.post_content.find_one({"post_uid": post_uid}).get("content")
        post["content"] = post_content
        return post

    def read_increment(self, post_uid: str) -> None:
        """
        Increment the read count for a specific post.

        Args:
            post_uid (str): The UID of the post to increment.
        """
        self._db_handler.post_info.make_increments(
            filter={"post_uid": post_uid}, increments={"reads": 1}
        )

    def view_increment(self, post_uid: str) -> None:
        """
        Increment the view count for a specific post.

        Args:
            post_uid (str): The UID of the post to increment.
        """
        self._db_handler.post_info.make_increments(
            filter={"post_uid": post_uid}, increments={"views": 1}
        )


post_utils = PostUtils(db_handler=mongodb)
