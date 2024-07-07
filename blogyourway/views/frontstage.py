from urllib.parse import unquote, urlparse

import bcrypt
import readtime
from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_user
from markdown import Markdown

from blogyourway.config import RECAPTCHA_KEY
from blogyourway.helpers.comments import comment_utils, create_comment
from blogyourway.helpers.common import sort_dict
from blogyourway.helpers.posts import html_to_about, html_to_post, paging, post_utils
from blogyourway.helpers.users import user_utils
from blogyourway.services import logger, logger_utils, mongodb

frontstage = Blueprint("frontstage", __name__, template_folder="../templates/frontstage/")


@frontstage.context_processor
def inject_env_var():
    return {"RECAPTCHA_KEY": RECAPTCHA_KEY}


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


@frontstage.route("/signup", methods=["GET"])
def signup_get():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("signup.html")


@frontstage.route("/signup", methods=["POST"])
def signup_post():
    ###################################################################

    # main actions

    ###################################################################

    new_user = user_utils.create_user(request=request)
    if new_user is not None:
        flash("Sign up succeeded.", category="success")
        user_info = user_utils.get_user_info(new_user)
        login_user(user_info)
        return redirect(url_for("frontstage.home", username=new_user))

    else:
        return render_template("signup.html")

    ###################################################################

    # return page content

    ###################################################################


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
    featured_posts = post_utils.find_featured_posts_info(username)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("home.html", user=user, posts=featured_posts)


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
        return redirect(url_for("frontstage.blog", username=username))

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
        if tag in post.get("tags"):
            post["created_at"] = post.get("created_at").strftime("%Y-%m-%d")
            posts_with_desired_tag.append(post)

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("tag.html", user=user_info, posts=posts_with_desired_tag, tag=tag)


def blogpost_main_actions(username, post_uid, request):
    author_info = mongodb.user_info.find_one({"username": username})
    target_post = post_utils.get_full_post(post_uid)

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes"])
    target_post["content"] = md.convert(target_post.get("content"))
    target_post["content"] = html_to_post(target_post.get("content"))
    target_post["last_updated"] = target_post["last_updated"].strftime("%B %d, %Y")
    target_post["readtime"] = str(readtime.of_html(target_post.get("content")))

    # add comments
    # this section should be placed before finding comments to show on the postu'1 min read'
    if request.method == "POST":
        create_comment(post_uid, request)
        flash("Comment published!", category="success")

    # find comments
    # oldest to newest comment
    comments = comment_utils.find_comments_by_post_uid(post_uid)
    for comment in comments:
        comment["created_at"] = comment.get("created_at").strftime("%Y-%m-%d %H:%M:%S")

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    post_utils.view_increment(post_uid)
    user_utils.total_view_increment(username)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("blogpost.html", user=author_info, post=target_post, comments=comments)


@frontstage.route("/@<username>/posts/<post_uid>", methods=["GET", "POST"])
def blogpost(username, post_uid):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.post_info.exists("post_uid", post_uid):
        logger.debug(f"invalid post uid {post_uid}")
        abort(404)

    post_info = mongodb.post_info.find_one({"post_uid": post_uid})
    if username != post_info.get("author"):
        logger.debug(f"User {username} does not own post {post_uid}")
        abort(404)

    custom_slug = post_info.get("custom_slug")
    if custom_slug != "":
        return redirect(
            url_for(
                "frontstage.blogpost_with_slug",
                username=username,
                post_uid=post_uid,
                slug=custom_slug,
            )
        )

    ###################################################################

    # main actions

    ###################################################################

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/@<username>/posts/<post_uid>/<slug>", methods=["GET", "POST"])
def blogpost_with_slug(username, post_uid, slug):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.post_info.exists("post_uid", post_uid):
        logger.debug(f"invalid post uid {post_uid}")
        abort(404)

    post_info = mongodb.post_info.find_one({"post_uid": post_uid})
    if username != post_info.get("author"):
        logger.debug(f"User {username} does not own post {post_uid}")
        abort(404)

    custom_slug = post_info.get("custom_slug")
    if custom_slug != slug:
        return redirect(
            url_for(
                "frontstage.blogpost_with_slug",
                username=username,
                post_uid=post_uid,
                slug=custom_slug,
            )
        )

    ###################################################################

    # main actions

    ###################################################################

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/readcount-increment", methods=["GET"])
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
    user_utils.total_view_increment(username)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("about.html", user=user, about=about)


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
    POSTS_EACH_PAGE = 5
    pagination = paging.setup(username, current_page, POSTS_EACH_PAGE)

    # skip and limit posts with given page
    posts = post_utils.find_posts_with_pagination(
        username=username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )
    for post in posts:
        post["created_at"] = post.get("created_at").strftime("%Y-%m-%d")

    # user info
    user_info = user_utils.get_user_info(username)
    tags = sort_dict(user_info.tags)
    tags = {tag: count for tag, count in tags.items() if count > 0}

    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blog.html", user=user_info, posts=posts, tags=tags, pagination=pagination
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


@frontstage.route("/robots.txt", methods=["GET"])
def robotstxt():
    return open("robots.txt", "r")


@frontstage.route("/sitemap")
@frontstage.route("/sitemap/")
@frontstage.route("/sitemap.xml")
def sitemap():
    """
    Route to dynamically generate a sitemap of your website/application.
    lastmod and priority tags omitted on static pages.
    lastmod included on dynamic content such as blog posts.
    """

    host_components = urlparse(request.host_url)
    host_base = host_components.scheme + "://" + host_components.netloc

    # Static routes with static content
    static_urls = []
    for route in ["/", "/login", "/register"]:
        static_urls.append({"loc": f"{host_base}{route}"})

    # Dynamic routes with dynamic content
    dynamic_urls = []
    for username in user_utils.get_all_username():
        dynamic_urls.append({"loc": f"{host_base}/@{username}"})
        dynamic_urls.append({"loc": f"{host_base}/@{username}/blog"})
        dynamic_urls.append({"loc": f"{host_base}/@{username}/about"})
    for post in post_utils.get_all_posts_info():
        slug = post.get("slug")
        if slug:
            url = {
                "loc": f"{host_base}/@{post.get('author')}/posts/{post.get('post_uid')}/{slug}",
                "lastmod": post.get("last_updated"),
            }
        else:
            url = {
                "loc": f"{host_base}/@{post.get('author')}/posts/{post.get('post_uid')}",
                "lastmod": post.get("last_updated"),
            }
        dynamic_urls.append(url)

    xml_sitemap = render_template(
        "sitemap.xml", static_urls=static_urls, dynamic_urls=dynamic_urls, host_base=host_base
    )
    response = make_response(xml_sitemap)
    response.headers["Content-Type"] = "application/xml"
    logger.debug("Sitemap generated successfully..")

    return response
