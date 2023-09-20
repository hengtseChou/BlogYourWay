import random
import string
from flask import Request
from flask_login import current_user
from application.extensions.mongo import my_database, MyDatabase
from application.extensions.log import logger, MyLogger
from application.extensions.redis import redis_method
from application.blog.utils import get_today, uid_generator

###################################################################

# create new post

###################################################################

def process_tags(tag_string: str):
    if tag_string == "":
        return []
    return [tag.strip().replace(" ", "-") for tag in tag_string.split(",")]

class NewPostSetup:
    def __init__(self, 
                 request: Request, 
                 post_uid_generator: uid_generator, 
                 db_handler: MyDatabase,
                 author_name: str
        ) -> None:
        self._request = request
        self._post_uid = post_uid_generator.generate_post_uid()
        self._db_handler = db_handler
        self._author_name = author_name

    def _form_validatd(self):
        return True
    
    def _create_post_info(self) -> dict:
        new_post_info = {
            "title": self._request.form.get("title"),
            "subtitle": self._request.form.get("subtitle"),
            "author": self._author_name,
            "post_uid": self._post_uid, 
            "tags": process_tags(self._request.form.get("tags")),
            "banner_url": self._request.form.get("banner_url"),
            "created_at": get_today(),
            "last_updated": get_today(),
            "archived": False, 
            "featured": False
        }
        return new_post_info
    
    def _create_post_content(self) -> dict:
        new_post_content = {
            "post_uid": self._post_uid,
            "author": self._author_name,
            "content": self._request.form.get("content")
        }
        return new_post_content
    
    def create_post(self):
        new_post_info = self._create_post_info()
        new_post_content = self._create_post_content()

        self._db_handler.post_info.insert_one(new_post_info)
        self._db_handler.post_content.insert_one(new_post_content)

        return self._post_uid

def create_post(request):

    new_post_setup = NewPostSetup(
        request=request,
        post_uid_generator=uid_generator,
        db_handler=my_database, 
        author_name=current_user.username
    )
    return new_post_setup.create_post()

###################################################################

# updating a post

###################################################################

class PostUpdateSetup:

    def __init__(self, 
                 post_uid: str, 
                 request: Request, 
                 db_handler = MyDatabase
        ) -> None:
        self._post_uid = post_uid
        self._request = request
        self._db_handler = db_handler

    def _updated_post_info(self) -> dict:
        updated_post_info = {
            "title": self._request.form.get("title"),
            "subtitle": self._request.form.get("subtitle"),
            "tags": process_tags(self._request.form.get("tags")),
            "banner_url": self._request.form.get("banner_url"),
            "last_updated": get_today()
        }
        return updated_post_info
    
    def _updated_post_content(self) -> dict:
        updated_post_content = {
            "content": self._request.form.get("content")
        }
        return updated_post_content
    
    def update_post(self):

        updated_post_info = self._updated_post_info()
        updated_post_content = self._updated_post_content()
        
        self._db_handler.post_info.simple_update(
            filter={"post_uid": self._post_uid},
            update=updated_post_info
        )
        self._db_handler.post_content.simple_update(
            filter={"post_uid": self._post_uid},
            update=updated_post_content
        )        

def update_post(post_uid, request):
    post_update_setup = PostUpdateSetup(
        post_uid=post_uid,
        request=request,
        db_handler=my_database
    )
    post_update_setup.update_post()

###################################################################

# deleting user

###################################################################

class UserDeletionSetup:
    def __init__(self,
                 username: str, 
                 db_handler: MyDatabase,
                 logger: MyLogger
        ) -> None:
        self._user_to_be_deleted = username
        self._db_handler = db_handler
        self._logger = logger
    
    def _get_posts_uid_by_user(self) -> list:
        target_posts = self._db_handler.post_info.find({"author": self._user_to_be_deleted})
        target_posts_uid = [post["post_uid"] for post in target_posts]

        return target_posts_uid
    
    def _remove_all_posts(self):
        self._db_handler.post_info.delete_many({"author": self._user_to_be_deleted})
        self._db_handler.post_content.delete_many({"author": self._user_to_be_deleted})
        self._logger.debug(f"Deleted all posts written by user {self._user_to_be_deleted}.")
    
    def _remove_all_related_comments(self, post_uids: list):
        for post_uid in post_uids:
            self._db_handler.comment.delete_many({"post_uid": post_uid})
        self._logger.debug(f"Deleted relevant comments from user {self._user_to_be_deleted}.")

    def _remove_user(self):
        self._db_handler.user_login.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_info.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_about.delete_one({"username": self._user_to_be_deleted})
        logger.debug(f"Deleted user information for user {self._user_to_be_deleted}.")

    def start_deletion_process(self):
        target_posts_uid = self._get_posts_uid_by_user()
        self._remove_all_posts()
        self._remove_all_related_comments(target_posts_uid)
        # this place should includes removing metrics data for the user
        # redis_method.delete_with_prefix(username)
        self._remove_user()

def delete_user(username):
    user_deletion = UserDeletionSetup(
        username=username, 
        db_handler=my_database,
        logger=logger
    )
    user_deletion.start_deletion_process()

###################################################################

# other utilities

###################################################################

def switch_to_bool(switch_value: str | None)-> bool:
    if switch_value is None:
        return False
    return True

def string_truncate(text:str, max_len:int):
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."