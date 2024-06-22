from urllib.parse import unquote

import bcrypt
import readtime
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user
from markdown import Markdown

from blogyourway.helpers.articles import article_utils, html_to_about, html_to_article, paging
from blogyourway.helpers.comments import comment_utils, create_comment
from blogyourway.helpers.common import sort_dict
from blogyourway.helpers.users import user_utils
from blogyourway.services import logger, logger_utils, mongodb, sitemapper

frontstage = Blueprint("frontstage", __name__, template_folder="../templates/frontstage/")


@sitemapper.include(priority=1)
@frontstage.route("/", methods=["GET"])
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
@frontstage.route("/login", methods=["GET"])
def login_get():
    ###################################################################

    # early returns

    ###################################################################

    if current_user.is_authenticated:
        flash("You are already logged in.")
        logger.debug(f"Attempt to duplicate logging from user {current_user.username}.")
        return redirect(url_for("frontstage.home", username=current_user.username))

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("login.html")


@frontstage.route("/login", methods=["POST"])
def login_post():
    ###################################################################

    # early returns

    ###################################################################

    login_form = request.form.to_dict()
    if not mongodb.user_creds.exists("email", login_form.get("email")):
        flash("Account not found. Please try again.", category="error")
        logger_utils.login_failed(request=request, msg=f"email {login_form.get('email')} not found")
        return render_template("login.html")

    # check pw
    user_creds = mongodb.user_creds.find_one({"email": login_form.get("email")})
    encoded_input_pw = login_form.get("password").encode("utf8")
    encoded_valid_user_pw = user_creds.get("password").encode("utf8")

    if not bcrypt.checkpw(encoded_input_pw, encoded_valid_user_pw):
        flash("Invalid password. Please try again.", category="error")
        logger_utils.login_failed(
            request=request, msg=f"invalid password with email {login_form.get('email')}"
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

    return redirect(url_for("frontstage.home", username=username))


@sitemapper.include()
@frontstage.route("/register", methods=["GET"])
def register_get():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("register.html")


@frontstage.route("/register", methods=["POST"])
def register_post():
    ###################################################################

    # main actions

    ###################################################################

    new_user = user_utils.create_user(request=request)
    if new_user is not None:
        flash("Registration succeeded.", category="success")
        user_info = user_utils.get_user_info(new_user)
        login_user(user_info)
        return redirect(url_for("frontstage.home", username=new_user))

    else:
        return render_template("register.html")

    ###################################################################

    # return page content

    ###################################################################


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@frontstage.route("/@<username>", methods=["GET"])
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
    featured_articles = article_utils.find_featured_articles_info(username)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("home.html", user=user, articles=featured_articles)


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@frontstage.route("/@<username>/tags", methods=["GET"])
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

    articles = article_utils.find_all_articles_info(username)

    articles_with_desired_tag = []
    for article in articles:
        if tag in article.get("tags"):
            article["created_at"] = article.get("created_at").strftime("%Y-%m-%d")
            articles_with_desired_tag.append(article)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("tag.html", user=user_info, articles=articles_with_desired_tag, tag=tag)


@sitemapper.include(
    url_variables={
        "username": article_utils.get_all_author(),
        "article_uid": article_utils.get_all_article_uid(),
    }
)
@frontstage.route("/@<username>/articles/<article_uid>", methods=["GET", "POST"])
def article(username, article_uid):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.article_info.exists("article_uid", article_uid):
        logger.debug(f"invalid article uid {article_uid}")
        abort(404)

    author = mongodb.article_info.find_one({"article_uid": article_uid}).get("author")
    if username != author:
        logger.debug(f"User {username} does not own article {article_uid}.")
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    author_info = mongodb.user_info.find_one({"username": username})
    target_article = article_utils.get_full_article(article_uid)

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes"])
    target_article["content"] = md.convert(target_article.get("content"))
    target_article["content"] = html_to_article(target_article.get("content"))
    target_article["last_updated"] = target_article["last_updated"].strftime("%B %d, %Y")
    target_article["readtime"] = str(readtime.of_html(target_article.get("content")))

    # add comments
    # this section should be placed before finding comments to show on the postu'1 min read'
    if request.method == "POST":
        create_comment(article_uid, request)
        flash("Comment published!", category="success")

    # find comments
    # oldest to newest comment
    comments = comment_utils.find_comments_by_article_uid(article_uid)
    for comment in comments:
        comment["created_at"] = comment.get("created_at").strftime("%Y-%m-%d %H:%M:%S")

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    article_utils.view_increment(article_uid)

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "article.html", user=author_info, article=target_article, comments=comments
    )


@frontstage.route("/readcount-increment", methods=["GET"])
def readcount_increment():
    ###################################################################

    # main actions

    ###################################################################

    article_uid = request.args.get("article_uid", type=str)
    article_utils.read_increment(article_uid)

    ###################################################################

    # return page content

    ###################################################################

    return "OK"


@sitemapper.include(url_variables={"username": user_utils.get_all_username()})
@frontstage.route("/@<username>/about", methods=["GET"])
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
@frontstage.route("/@<username>/blog", methods=["GET"])
def blog(username):
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
    ARTICLES_EACH_PAGE = 5
    pagination = paging.setup(username, current_page, ARTICLES_EACH_PAGE)

    # skip and limit articles with given page
    articles = article_utils.find_articles_with_pagination(
        username=username, page_number=current_page, articles_per_page=ARTICLES_EACH_PAGE
    )
    for article in articles:
        article["created_at"] = article.get("created_at").strftime("%Y-%m-%d")

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
        "blog.html", user=user_info, articles=articles, tags=tags, pagination=pagination
    )


@frontstage.route("/@<username>/get-profile-img", methods=["GET"])
def get_profile_img(username):
    user = mongodb.user_info.find_one({"username": username})

    if user.get("profile_img_url"):
        profile_img_url = user["profile_img_url"]
    else:
        profile_img_url = "/static/img/default-profile.png"

    return jsonify({"imageUrl": profile_img_url})


@frontstage.route("/is-unique", methods=["GET"])
def is_unique():
    email = request.args.get("email", default=None, type=str)
    username = request.args.get("username", default=None, type=str)
    if email is not None:
        return jsonify(not mongodb.user_info.exists(key="email", value=email))
    elif username is not None:
        return jsonify(not mongodb.user_info.exists(key="username", value=username))


@frontstage.route("/error", methods=["GET"])
def error_simulator():
    raise Exception("this is a simulation error.")


@frontstage.route("/sitemap.xml", methods=["GET"])
def sitemap():
    return sitemapper.generate()


@frontstage.route("/robots.txt", methods=["GET"])
def robotstxt():
    return open("robots.txt", "r")
