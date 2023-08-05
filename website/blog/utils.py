import requests
import bcrypt
import random
import string
from math import ceil
from datetime import datetime, timedelta
from flask import request, flash, render_template, abort
from flask_login import current_user
from bs4 import BeautifulSoup
from website.extensions.db_mongo import db_users, db_posts, db_comments
from website.config import ENV, RECAPTCHA_SECRET


class HTML_Formatter:
    def __init__(self, html_string):

        self.soup = BeautifulSoup(html_string, "html.parser")

    def add_padding(self):

        # Find all tags in the HTML
        # except figure and img tag
        tags = self.soup.find_all(
            lambda tag: tag.name not in ["figure", "img"], recursive=False
        )

        # Add padding to each tag
        for tag in tags:
            current_style = tag.get("style", "")
            new_style = f"{current_style} padding-top: 10px; padding-bottom: 10px; "
            tag["style"] = new_style

        return self

    def change_heading_font(self):

        # Modify the style attribute for each heading tag
        headings = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        # Modify the style attribute for each heading tag
        for heading in headings:
            current_style = heading.get("style", "")
            new_style = f"{current_style} font-family: 'Ubuntu', 'Arial', sans-serif;;"
            heading["style"] = new_style

        return self

    def modify_figure(self, max_width="90%"):

        imgs = self.soup.find_all(["img"])

        # center image and modify size
        for img in imgs:
            current_style = img.get("style", "")
            new_style = f"{current_style} display: block; margin: 0 auto; max-width: {max_width}; min-width: 30% ;height: auto;"
            img["style"] = new_style

        captions = self.soup.find_all(["figcaption"])

        # center caption
        for caption in captions:
            current_style = caption.get("style", "")
            new_style = f"{current_style} text-align: center"
            caption["style"] = new_style

        return self

    def to_string(self):

        return str(self.soup)

    def to_blogpost(self):

        blogpost = self.add_padding().change_heading_font().modify_figure().to_string()

        return blogpost

    def to_about(self):

        about = self.add_padding().modify_figure(max_width="50%").to_string()

        return about
    
class CRUD_Utils:

    @staticmethod
    def create_user(request):

        # registeration
        # with unique email, username and blog name
        reg_form = request.form.to_dict()
        # make sure username has no space character
        reg_form["username"] = reg_form["username"].strip().replace(" ", "-")
        if db_users.exists("email", reg_form["email"]):
            flash("Email is already used. Please try another one.", category="error")
            return render_template("register.html")

        if db_users.exists("username", reg_form["username"]):
            flash("Username is already used. Please try another one.", category="error")
            return render_template("register.html")

        if db_users.exists("blogname", reg_form["blogname"]):
            flash("Blog name is already used. Please try another one.")
            return render_template("register.html")

        hashed_pw = bcrypt.hashpw(reg_form["password"].encode("utf-8"), bcrypt.gensalt(12))
        hashed_pw = hashed_pw.decode("utf-8")

        new_user_login = {"username": reg_form["username"]}
        new_user_info = {"username": reg_form["username"]}
        new_user_about = {"username": reg_form["username"]}

        new_user_login["email"] = reg_form["email"]
        new_user_login["password"] = hashed_pw

        new_user_info["blogname"] = reg_form["blogname"]
        new_user_info["posts_count"] = 0
        new_user_info["banner_url"] = ""
        new_user_info["profile_img_url"] = ""
        new_user_info["short_bio"] = ""
        new_user_info["social_links"] = []
        if ENV == "debug":
            new_user_info["created_at"] = datetime.now()
        elif ENV == "prod":
            new_user_info["created_at"] = datetime.now() + timedelta(hours=8)

        new_user_about["about"] = ""

        db_users.login.insert_one(new_user_login)
        db_users.info.insert_one(new_user_info)
        db_users.about.insert_one(new_user_about)

    @staticmethod
    def create_comment(post_uid, request):

        new_comment = {}
        if ENV == "debug":
            new_comment["created_at"] = datetime.now()
        elif ENV == "prod":
            new_comment["created_at"] = datetime.now() + timedelta(hours=8)
        new_comment["post_uid"] = post_uid
        new_comment["profile_pic"] = "/static/img/visitor.png"
        new_comment["profile_link"] = ""
        new_comment["comment"] = request.form.get("comment")
        alphabet = string.ascii_lowercase + string.digits
        uid = "".join(random.choices(alphabet, k=8))
        while db_comments.exists("comment_uid", uid):
            uid = "".join(random.choices(alphabet, k=8))
        new_comment["comment_uid"] = uid

        if current_user.is_authenticated:
            commenter = dict(
                db_users.info.find_one({"username": current_user.username})
            )
            new_comment["name"] = current_user.username
            new_comment["email"] = commenter["email"]
            new_comment["profile_link"] = f"/{current_user.username}/about"
            if commenter["profile_img_url"]:
                new_comment["profile_pic"] = commenter["profile_img_url"]
        else:
            new_comment["name"] = request.form.get("name")
            new_comment["email"] = request.form.get("email")

        db_comments.comment.insert_one(new_comment)

    @staticmethod
    def create_post(request):

         # create a new post in db
        new_post = request.form.to_dict()
        # set posting time
        if ENV == "debug":
            new_post["created_at"] = new_post["last_updated"] = datetime.now()
        elif ENV == "prod":
            new_post["created_at"] = new_post[
                "last_updated"
            ] = datetime.now() + timedelta(hours=8)
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

    @staticmethod
    def update_post(post_uid, request):

        updated_post = request.form.to_dict()
        # set last update time
        if ENV == "debug":
            updated_post["last_updated"] = datetime.now()
        elif ENV == "prod":
            updated_post["last_updated"] = datetime.now() + timedelta(hours=8)
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

    @staticmethod
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


        




def all_user_tags(username):

    result = db_posts.info.find({"author": username, "archived": False})

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


def is_comment_verified(token):

    payload = {"secret": RECAPTCHA_SECRET, "response": token}
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)
    response = r.json()


    if response["success"]:
        return True
    return False



def set_up_pagination(username, current_page, posts_per_page):

    # set up for pagination
    num_not_archieved = db_posts.info.count_documents(
        {"author": username, "archived": False}
    )
    if num_not_archieved == 0:
        max_page = 1
    else:
        max_page = ceil(num_not_archieved / posts_per_page)

    if current_page > max_page:
        # not a legal page number
        abort(404)

    enable_older_post = False
    if current_page * posts_per_page < num_not_archieved:
        enable_older_post = True

    enable_newer_post = False
    if current_page > 1:
        enable_newer_post = True

    pagination = {
        'enable_newer_post': enable_newer_post, 
        'enable_older_post': enable_older_post
    }

    return pagination

def get_today():

    if ENV == 'debug':
        today = datetime.now().strftime('%Y%m%d')
    elif ENV == 'prod':
        today = (datetime.now() + timedelta(hours=8)).strftime('%Y%m%d')
    return today

