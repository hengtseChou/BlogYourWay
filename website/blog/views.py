import bcrypt
import markdown
from urllib.parse import unquote
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_user, UserMixin, current_user
from website.extensions.db_mongo import db_users, db_posts, db_comments
from website.extensions.db_redis import redis_method
from website.blog.utils import (
    HTML_Formatter, CRUD_Utils, 
    all_user_tags, is_comment_verified, set_up_pagination, get_today
)

blog = Blueprint("blog", __name__, template_folder="../templates/blog/")
md = markdown.Markdown(extensions=["markdown_captions", "fenced_code"])

class User(UserMixin):
    # user id is set as username
    def __init__(self, user_data):
        for key, value in user_data.items():
            if key == "username":
                self.id = value
                self.username = value
                continue
            setattr(self, key, value)


@blog.route("/", methods=["GET"])
def landing_page():

    today = get_today()
    redis_method.increment_count(f'landing_page_{today}', request)

    return render_template("landing_page.html")


@blog.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        if current_user.is_authenticated:
            flash("You are already logged in.")
            return redirect(url_for("backstage.panel"))
        return render_template("login.html")

    login_form = request.form.to_dict()
    # find user in db
    if not db_users.exists("email", login_form["email"]):
        flash("Account not found. Please try again.", category="error")
        return render_template("login.html")

    user_creds = db_users.login.find_one({"email": login_form["email"]})
    # check pw
    if not bcrypt.checkpw(login_form["password"].encode("utf8"), user_creds["password"].encode("utf8")):
        flash("Invalid password. Please try again.", category="error")
        return render_template("login.html")
    # login user
    user = User(user_creds)
    login_user(user)
    flash("Login Succeeded.", category="success")
    return redirect(url_for("backstage.overview"))


@blog.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html") 

    CRUD_Utils.create_user(request=request)

    # succeeded and return to login page
    flash("Registeration succeeded.", category="success")
    return redirect(url_for("blog.login"))


@blog.route("/<username>/home", methods=["GET"])
def home(username):
    # /{hank}/home
    # get data, post of hank from db
    if not db_users.exists("username", username):
        abort(404)

    user = db_users.info.find_one({"username": username})
    featured_posts = (
        db_posts.info.find({"author": username, "featured": True, "archived": False})
        .sort("created_at", -1)
        .limit(10)
    )
    featured_posts = list(featured_posts)
    feature_idx = 1
    for post in featured_posts:
        post["idx"] = feature_idx
        feature_idx += 1
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    # update visitor counts
    redis_method.increment_count(f"{username}_home", request)
    today = get_today()
    redis_method.increment_count(f"{username}_{today}_uv", request)

    return render_template(
        "home.html", user=user, posts=featured_posts, num_of_posts=len(featured_posts)
    )


@blog.route("/<username>/tags", methods=["GET"])
def tag(username):

    if not db_users.exists("username", username):
        abort(404)
    user = db_users.info.find_one({"username": username})
    # currently no pagination for tag

    tag = request.args.get("tag", default=None, type=str)
    if tag is None:
        return redirect(url_for("blog.blogpage", username=username))
    # decode form url
    tag_decoded = unquote(tag)

    # abort for unknown tag
    all_tags = all_user_tags(username)
    if tag_decoded not in all_tags.keys():
        abort(404)

    posts = db_posts.info.find(
        {"author": username, "archived": False}
    ).sort("created_at", -1)

    posts = list(posts)
    posts_has_tag = []
    idx = 1
    for post in posts:
        if tag_decoded in post["tags"]:
            post["idx"] = idx
            idx += 1
            post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
            posts_has_tag.append(post)

    # update visitor counts
    redis_method.increment_count(f"{username}_tag: {tag_decoded}", request)
    today = get_today()
    redis_method.increment_count(f"{username}_uv_{today}", request)


    return render_template(
        "tag.html",
        user=user,
        posts=posts_has_tag,
        tag=tag_decoded,
        num_of_posts=len(posts_has_tag),
    )


@blog.route("/<username>/posts/<post_uid>", methods=["GET", "POST"])
def post(username, post_uid):

    if not db_users.exists("username", username):
        abort(404)
    if not db_posts.exists("post_uid", post_uid):
        abort(404)

    author = db_users.info.find_one({"username": username})
    target_post = dict(db_posts.info.find_one({"post_uid": post_uid}))
    target_post["content"] = db_posts.content.find_one({"post_uid": post_uid})["content"]

    # to verify the post is linked to the user
    if author["username"] != target_post["author"]:
        abort(404)

    # add comments
    if request.method == "POST":
        token = request.form.get("g-recaptcha-response")

        if is_comment_verified(token):

            CRUD_Utils.create_comment(post_uid, request)
            
            db_posts.info.update_one(
                filter={"post_uid": post_uid},
                update={"$set": {"comments": target_post["comments"] + 1}},
            )
            flash("Comment published!", category="success")

    target_post["content"] = md.convert(target_post["content"])
    target_post["content"] = HTML_Formatter(target_post["content"]).to_blogpost()
    target_post["last_updated"] = target_post["last_updated"].strftime("%Y-%m-%d")

    # find comments
    # oldest to newest comment
    comments = list(
        db_comments.comment
        .find({"post_uid": post_uid})
        .sort("created_at", 1)
    )
    for comment in comments:
        comment["created_at"] = comment["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    # update visitor counts
    redis_method.increment_count(f"post_uid_{target_post['post_uid']}", request)
    today = get_today()
    redis_method.increment_count(f"{username}_uv_{today}", request)


    return render_template(
        "blogpost.html", user=author, post=target_post, comments=comments
    )


@blog.route("/<username>/about", methods=["GET"])
def about(username):
    if not db_users.exists("username", username):
        abort(404)
    user = dict(db_users.info.find_one({"username": username}))
    user_about = db_users.about.find_one({"username": username})["about"]
    about_converted = md.convert(user_about)
    about_converted = HTML_Formatter(about_converted).to_about()

    # update visitor counts
    redis_method.increment_count(f"{username}_about", request)
    today = get_today()
    redis_method.increment_count(f"{username}_uv_{today}", request)


    return render_template("about.html", user=user, about=about_converted)


@blog.route("/<username>/blog", methods=["GET"])
def blogg(username):
    if not db_users.exists("username", username):
        abort(404)
    user = db_users.info.find_one({"username": username})
    page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 10

    # create a tag dict
    tags_dict = all_user_tags(username)

    # set up pagination
    pagination = set_up_pagination(username, page, POSTS_EACH_PAGE)
    enable_newer_post = pagination['enable_newer_post']
    enable_older_post = pagination['enable_older_post']

    # skip and limit posts with given page
    if page == 1:
        posts = (
            db_posts.info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .limit(POSTS_EACH_PAGE)
        )  # descending: newest
    elif page > 1:
        posts = (
            db_posts.info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .skip((page - 1) * POSTS_EACH_PAGE)
            .limit(POSTS_EACH_PAGE)
        )

    idx = 1
    posts = list(posts)
    for post in posts:
        post["idx"] = idx
        idx += 1
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
    num_of_posts = len(posts)

    # update visitor counts
    redis_method.increment_count(f"{username}_blog", request)
    today = get_today()
    redis_method.increment_count(f"{username}_uv_{today}", request)


    return render_template(
        "blog.html",
        user=user,
        posts=posts,
        num_of_posts=num_of_posts,
        tags=tags_dict,
        current_page=page,
        newer_posts=enable_newer_post,
        older_posts=enable_older_post,
    )
