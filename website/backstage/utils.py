import random
import string
from flask_login import current_user
from website.extensions.db_mongo import db_users, db_posts, db_comments
from website.extensions.log import logger
from website.blog.utils import get_today

def create_post(request):

    # create a new post in db
    new_post = request.form.to_dict()

    # set posting time
    new_post["created_at"] = new_post["last_updated"] = get_today()    
    # set other attributes
    new_post["author"] = current_user.username
    # process tags
    if new_post["tags"] == "":
        new_post["tags"] = []
    else:
        new_post["tags"] = [tag.strip() for tag in new_post["tags"].split(",")]
    for tag in new_post["tags"]:
        tag = tag.replace(" ", "-")
    
    new_post["comments"] = 0
    new_post["archived"] = False
    new_post["featured"] = False
    alphabet = string.ascii_lowercase + string.digits
    uid = "".join(random.choices(alphabet, k=8))
    while db_posts.exists("post_uid", uid):
        uid = "".join(random.choices(alphabet, k=8))
    new_post["post_uid"] = uid

    db_posts.content.insert_one({"post_uid": uid, "content": new_post["content"]})
    del new_post["content"]
    db_posts.info.insert_one(new_post)
    logger.debug(f'Add new post {uid}.')


def update_post(post_uid, request):

    updated_post = request.form.to_dict()
    updated_post["last_updated"] = get_today()    
    # process tags
    if updated_post["tags"] == "":
        updated_post["tags"] = []
    else:
        updated_post["tags"] = [tag.strip() for tag in updated_post["tags"].split(",")]
    for tag in updated_post["tags"]:
        tag = tag.replace(" ", "-")

    updated_post_content = updated_post["content"]
    del updated_post["content"]
    updated_post_info = updated_post

    db_posts.content.update_one(
        filter={"post_uid": post_uid}, update={"$set": updated_post_content}
    )
    db_posts.info.update_one(
        filter={"post_uid": post_uid}, update={"$set": updated_post_info}
    )
    logger.debug(f'Updated post id {post_uid}.')


def delete_user(username):

    # get all post id, because we want to also remove relevant comments
    # remove all posts
    # remove comments within the post
    # remove postfolio
    # remove user

    posts_uid_to_delete = []
    posts_to_delete = list(
        db_posts.info.find({"author": username})
    )
    for post in posts_to_delete:
        posts_uid_to_delete.append(post["post_uid"])
    for post_uid in posts_uid_to_delete:
        db_posts.info.delete_one({"post_uid": post_uid})
        db_posts.content.delete_one({"post_uid": post_uid})
        db_comments.comment.delete_many({"post_uid": post_uid})


    db_users.login.delete_one({"username": username})
    db_users.info.delete_one({"username": username})
    db_users.about.delete_one({"username": username})
    logger.debug(f'Deleted user {username}.')