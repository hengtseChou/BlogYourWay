from urllib.parse import unquote

import bcrypt
import readtime
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user
from markdown import Markdown

from blogyourway.helpers.comments import comment_utils, create_comment
from blogyourway.helpers.common import sort_dict
from blogyourway.helpers.posts import html_to_about, html_to_blogpost, paging, post_utils
from blogyourway.helpers.users import user_utils
from blogyourway.services import logger, logger_utils, mongodb, sitemapper

blog = Blueprint("blog", __name__, template_folder="../templates/blog/")


@sitemapper.include(priority=1)
@blog.route("/", methods=["GET"])
def landing_page():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("landing-page.html")


@sitemapper.include()
@blog.route("/login", methods=["GET"])
def login_get():
    ###################################################################

    # early returns

    ###################################################################

    if current_user.is_authenticated:
        flash("You are already logged in.")
        logger.debug(f"Attempt to duplicate logging from user {current_user.username}.")
        return redirect(url_for("backstage.overview"))

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("login.html")


@blog.route("/login", methods=["POST"])
def login_post():
    ###################################################################

    # early returns

    ###################################################################

    login_form = request.form.to_dict()
    if not mongodb.user_creds.exists("email", login_form["email"]):
        flash("Account not found. Please try again.", category="error")
        logger_utils.login_failed(request=request, msg=f"email {login_form['email']} not found")
        return render_template("login.html")

    # check pw
    user_creds = mongodb.user_creds.find_one({"email": login_form["email"]})
    encoded_input_pw = login_form["password"].encode("utf8")
    encoded_valid_user_pw = user_creds["password"].encode("utf8")

    if not bcrypt.checkpw(encoded_input_pw, encoded_valid_user_pw):
        flash("Invalid password. Please try again.", category="error")
        logger_utils.login_failed(
            request=request, msg=f"invalid password with email {login_form['email']}"
        )
        return render_template("login.html")

    ###################################################################

    # main actions

    ###################################################################

    username = user_creds.get("username")
    user_info = user_utils.get_user_info(username)
    login_user(user_info)
    logger_utils.login_succeeded(request=request, username=username)
    flash("Login Succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("blog.home", username=username))


@sitemapper.include()
@blog.route("/register", methods=["GET"])
def register_get():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("register.html")


@blog.route("/register", methods=["POST"])
def register_post():
    ###################################################################

    # main actions

    ###################################################################

    user_utils.create_user(request=request)
    logger_utils.registration_succeeded(request=request)
    flash("Registration succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("blog.login_get"))


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@blog.route("/@<username>", methods=["GET"])
def home(username):
    ###################################################################

    # early returns

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": username})
    featured_posts = post_utils.find_featured_posts_info(username)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("home.html", user=user, posts=featured_posts)


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@blog.route("/@<username>/tags", methods=["GET"])
def tag(username):
    ###################################################################

    # early returns

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    # if no tag specified, show blog page
    tag_url_encoded = request.args.get("tag", default=None, type=str)
    if tag_url_encoded is None:
        return redirect(url_for("blog.blog_page", username=username))

    # abort for unknown tag
    tag = unquote(tag_url_encoded)
    user_info = user_utils.get_user_info(username)
    if tag not in user_info.tags.keys():
        logger.debug(f"invalid tag {tag}")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    posts = post_utils.find_all_posts_info(username)

    posts_with_desired_tag = []
    for post in posts:
        if tag in post["tags"]:
            post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
            posts_with_desired_tag.append(post)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("tag.html", user=user_info, posts=posts_with_desired_tag, tag=tag)


@sitemapper.include(
    url_variables={
        "username": post_utils.get_all_author(),
        "post_uid": post_utils.get_all_post_uid(),
    }
)
@blog.route("/@<username>/posts/<post_uid>", methods=["GET", "POST"])
def post(username, post_uid):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.post_info.exists("post_uid", post_uid):
        logger.debug(f"invalid post uid {post_uid}")
        abort(404)

    author = mongodb.post_info.find_one({"post_uid": post_uid})["author"]
    if username != author:
        logger.debug(f"User {username} does not own post {post_uid}.")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    author_info = mongodb.user_info.find_one({"username": username})
    target_post = post_utils.get_full_post(post_uid)

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes"])
    target_post["content"] = md.convert(target_post["content"])
    target_post["content"] = html_to_blogpost(target_post["content"])
    target_post["last_updated"] = target_post["last_updated"].strftime("%d %b %Y")
    target_post["readtime"] = str(readtime.of_html(target_post["content"]))

    # add comments
    # this section should be placed before finding comments to show on the postu'1 min read'
    if request.method == "POST":
        create_comment(post_uid, request)
        flash("Comment published!", category="success")

    # find comments
    # oldest to newest comment
    comments = comment_utils.find_comments_by_post_uid(post_uid)
    for comment in comments:
        comment["created_at"] = comment["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    post_utils.view_increment(post_uid)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("post.html", user=author_info, post=target_post, comments=comments)


@blog.route("/readcount-increment", methods=["GET"])
def readcount_increment():
    ###################################################################

    # main actions

    ###################################################################

    post_uid = request.args.get("post_uid", type=str)
    post_utils.read_increment(post_uid)

    ###################################################################

    # return page content

    ###################################################################

    return "OK"


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@blog.route("/@<username>/about", methods=["GET"])
def about(username):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": username})
    user_about = mongodb.user_about.find_one({"username": username})["about"]

    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    about = md.convert(user_about)
    about = html_to_about(about)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("about.html", user=user, about=about)


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@blog.route("/@<username>/blog", methods=["GET"])
def blog_page(username):
    ###################################################################

    # early returns

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    # set up pagination
    current_page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 5
    pagination = paging.setup(username, current_page, POSTS_EACH_PAGE)

    # skip and limit posts with given page
    posts = post_utils.find_posts_with_pagination(
        username=username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    # user info
    user_info = user_utils.get_user_info(username)
    tags = sort_dict(user_info.tags)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blog.html", user=user_info, posts=posts, tags=tags, pagination=pagination
    )


@blog.route("@<username>/social-links", methods=["GET"])
def social_link_endpoint(username):
    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": username})
    social_links = user["social_links"]
    link_idx = request.args.get("idx", type=int)
    target_url = social_links[link_idx - 1]["url"]
    if not target_url.startswith("https://"):
        target_url = "https://" + target_url

    ###################################################################

    # logging / metrics

    ###################################################################

    logger.debug(f"redirect to social-link[{link_idx}]: {target_url}")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(target_url)


@blog.route("/@<username>/get-profile-img", methods=["GET"])
def profile_img_endpoint(username):
    user = mongodb.user_info.find_one({"username": username})

    if user["profile_img_url"]:
        profile_img_url = user["profile_img_url"]
    else:
        profile_img_url = "/static/img/default-profile.png"

    return jsonify({"imageUrl": profile_img_url})


@blog.route("/error", methods=["GET"])
def error_simulator():
    raise Exception("this is a simulation error.")


@blog.route("/sitemap.xml", methods=["GET"])
def sitemap():
    return sitemapper.generate()


@blog.route("/robots.txt", methods=["GET"])
def robotstxt():
    return open("robots.txt", "r")
