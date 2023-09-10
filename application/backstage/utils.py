import random
import string
from flask_login import current_user
from application.extensions.mongo import db_users, db_posts, db_comments
from application.extensions.log import logger
from application.extensions.redis import redis_method
from application.blog.utils import get_today

alphabet = string.ascii_lowercase + string.digits


def create_post(request):

    form = request.form.to_dict()

    new_post_info = {}
    post_uid = "".join(random.choices(alphabet, k=8))
    while db_posts.info.exists("post_uid", post_uid):
        post_uid = "".join(random.choices(alphabet, k=8))
    new_post_info["post_uid"] = post_uid

    new_post_info["created_at"] = get_today()
    new_post_info["last_updated"] = get_today()
    new_post_info["title"] = form["title"]
    new_post_info["subtitle"] = form["subtitle"]
    new_post_info["banner_url"] = form["banner_url"]
    new_post_info["author"] = current_user.username

    new_post_info["comments"] = 0
    new_post_info["archived"] = False
    new_post_info["featured"] = False

    # process tags
    if form["tags"] == "":
        new_post_info["tags"] = []
    else:
        new_post_info["tags"] = [
            tag.strip().replace(" ", "-") for tag in form["tags"].split(",")
        ]

    db_posts.content.insert_one({"post_uid": post_uid, "content": form["content"]})
    db_posts.info.insert_one(new_post_info)

    return post_uid


def update_post(post_uid, request):

    form = request.form.to_dict()
    updated_post_info = {}
    updated_post_info["last_updated"] = get_today()
    updated_post_info["title"] = form["title"]
    updated_post_info["subtitle"] = form["subtitle"]
    updated_post_info["banner_url"] = form["banner_url"]

    # process tags
    if form["tags"] == "":
        updated_post_info["tags"] = []
    else:
        updated_post_info["tags"] = [
            tag.strip().replace(" ", "-") for tag in form["tags"].split(",")
        ]

    db_posts.content.simple_update(
        filter={"post_uid": post_uid}, update={"content": form["content"]}
    )
    db_posts.info.simple_update(filter={"post_uid": post_uid}, update=updated_post_info)


def delete_user(username):

    # get all post id, because we want to also remove relevant comments
    # remove all posts
    # remove comments within the post
    # remove postfolio
    # remove user

    posts_uid_to_delete = []
    posts_to_delete = db_posts.info.find({"author": username})

    for post in posts_to_delete:
        posts_uid_to_delete.append(post["post_uid"])
    for post_uid in posts_uid_to_delete:
        db_posts.info.delete_one({"post_uid": post_uid})
        db_posts.content.delete_one({"post_uid": post_uid})
        db_comments.comment.delete_many({"post_uid": post_uid})
        redis_method.delete(f"post_uid_{post_uid}")

    logger.debug(
        f"Deleted all posts by {username} and relevant comments from the post and the comment databases."
    )
    redis_method.delete_with_prefix(username)
    logger.debug(f"Deleted all log with {username} in the redis memory.")

    db_users.login.delete_one({"username": username})
    db_users.info.delete_one({"username": username})
    db_users.about.delete_one({"username": username})
    logger.debug(f"Deleted {username} from the user database.")


def switch_to_bool(switch_value: str | None)-> bool:

    if switch_value is None:
        return False
    return True