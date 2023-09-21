import bcrypt
import readtime
from urllib.parse import unquote
from markdown import Markdown
from flask import (
    Blueprint,
    request,
    render_template,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_login import current_user, login_user
from application.config import ENV
from application.extensions.mongo import my_database
from application.extensions.redis import redis_method
from application.extensions.log import logger
from application.extensions.user import User
from application.blog.utils import (
    html_to_blogpost,
    html_to_about, 
    create_user,
    create_comment, 
    get_today, 
    all_tags, 
    paging,
    post_utils, 
    comment_utils
)

blog = Blueprint("blog", __name__, template_folder="../templates/blog/")

@blog.route("/", methods=["GET"])
def landing_page():

    ###################################################################

    # redis and logging

    ###################################################################

    logger.page_visited(request=request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"landing_page_{today}", request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("landing_page.html")


@blog.route("/login", methods=["GET"])
def login():

    ###################################################################

    # early returns

    ###################################################################

    if current_user.is_authenticated:
        flash("You are already logged in.")
        logger.debug(f"Attempt to duplicate logging in from {request.remote_addr}.")
        return redirect(url_for("backstage.panel"))

    ###################################################################

    # redis and logging

    ###################################################################

    logger.page_visited(request=request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("login.html")


@blog.route("/login", methods=["POST"])
def sending_login_form():

    ###################################################################

    # early returns

    ###################################################################

    login_form = request.form.to_dict()
    if not my_database.user_login.exists("email", login_form["email"]):
        flash("Account not found. Please try again.", category="error")
        logger.user.login_failed(msg="email not found", request=request)
        return render_template("login.html")

    # check pw
    user_creds = my_database.user_login.find_one({"email": login_form["email"]})
    encoded_input_pw = login_form["password"].encode("utf8")
    encoded_valid_user_pw = user_creds["password"].encode("utf8")

    if not bcrypt.checkpw(encoded_input_pw, encoded_valid_user_pw):
        flash("Invalid password. Please try again.", category="error")
        logger.user.login_failed(msg="invalid password", request=request)
        return render_template("login.html")

    ###################################################################

    # main actions

    ###################################################################

    user = User(user_creds)
    login_user(user)
    logger.user.login_succeeded(username=user_creds["username"], request=request)
    flash("Login Succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.overview"))


@blog.route("/register", methods=["GET"])
def register():

    ###################################################################

    # redis and logging

    ###################################################################

    logger.page_visited(request=request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("register.html")


@blog.route("/register", methods=["POST"])
def sending_register_form():

    ###################################################################

    # main actions

    ###################################################################

    username = create_user(request=request)
    logger.user.registration_succeeded(username=username, request=request)
    flash("Registration succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("blog.login"))


@blog.route("/@<username>", methods=["GET"])
def home(username):

    ###################################################################

    # early returns

    ###################################################################

    if not my_database.user_info.exists("username", username):
        logger.invalid_username(username=username, request=request)
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": username})
    featured_posts = post_utils.find_featured_posts_info(username)
    for post in featured_posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"{username}_home", request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.page_visited(request=request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("home.html", user=user, posts=featured_posts)


@blog.route("/@<username>/tags", methods=["GET"])
def tag(username):

    ###################################################################

    # early returns

    ###################################################################

    if not my_database.user_info.exists("username", username):
        logger.invalid_username(username=username, request=request)
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    # if no tag specified, show blog page
    tag_url_encoded = request.args.get("tag", default=None, type=str)
    if tag_url_encoded is None:
        return redirect(url_for("blog.blogpage", username=username))

    # abort for unknown tag
    tag = unquote(tag_url_encoded)
    tags_found = all_tags.from_user(username)
    if tag not in tags_found.keys():
        abort(404)

    user = my_database.user_info.find_one({"username": username})
    posts = post_utils.find_all_posts_info(username)

    posts_with_desired_tag = []
    for post in posts:
        if tag in post["tags"]:
            post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
            posts_with_desired_tag.append(post)

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_tag: {tag}", request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.full_path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("tag.html", user=user, posts=posts_with_desired_tag, tag=tag)


@blog.route("/@<username>/posts/<post_uid>", methods=["GET", "POST"])
def post(username, post_uid):

    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not my_database.user_info.exists("username", username):
        logger.invalid_username(username=username, request=request)
        abort(404)
    if not my_database.post_info.exists("post_uid", post_uid):
        logger.invalid_post_uid(username=username, post_uid=post_uid, request=request)
        abort(404)

    author_found_with_post_uid = (
        my_database.post_info
        .find_one({"post_uid": post_uid})["author"]
    )
    if username != author_found_with_post_uid:
        logger.invalid_autor_for_the_post(
            username=username, post_uid=post_uid, request=request
        )
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    author_info = my_database.user_info.find_one({"username": username})
    target_post = post_utils.get_full_post(post_uid)

    md = Markdown(extensions=["markdown_captions", "fenced_code", "footnotes"])
    target_post["content"] = md.convert(target_post["content"])
    target_post["content"] = html_to_blogpost(target_post["content"])
    target_post["last_updated"] = target_post["last_updated"].strftime("%Y-%m-%d")
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

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"post_uid_{target_post['post_uid']}", request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.page_visited(request=request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blogpost.html", user=author_info, post=target_post, comments=comments
    )


@blog.route("/@<username>/about", methods=["GET"])
def about(username):

    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not my_database.user_info.exists("username", username):
        logger.invalid_username(username=username, request=request)
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": username})
    user_about = my_database.user_about.find_one({"username": username})["about"]

    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    about = md.convert(user_about)
    about = html_to_about(about)

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_about", request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.page_visited(request=request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("about.html", user=user, about=about)


@blog.route("/@<username>/blog", methods=["GET"])
def blogg(username):

    ###################################################################

    # early returns

    ###################################################################

    if not my_database.user_info.exists("username", username):
        logger.invalid_username(username=username, request=request)
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": username})
    current_page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 10

    # create a tag dict
    tags_dict = all_tags.from_user(username)

    # set up pagination
    pagination = paging.setup(username, current_page, POSTS_EACH_PAGE)

    # skip and limit posts with given page
    posts = post_utils.find_posts_with_pagination(
        username=username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_blog", request)
    today = get_today(env=ENV).strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blog.html", user=user, posts=posts, tags=tags_dict, pagination=pagination
    )


@blog.route("/<username>/get-profile-pic", methods=["GET"])
def profile_pic_endpoint(username):

    user = my_database.user_info.find_one({"username": username})

    if user["profile_img_url"]:
        profile_img_url = user["profile_img_url"]
    else:
        profile_img_url = "/static/img/default-profile.png"

    return jsonify({"imageUrl": profile_img_url})
