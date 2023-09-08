import bcrypt
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
from flask_login import UserMixin, current_user, login_user
from application.extensions.mongo import db_users, db_posts, db_comments
from application.extensions.redis import redis_method
from application.extensions.log import logger
from application.blog.utils import (
    HTML_Formatter,
    Pagination,
    create_user,
    create_comment,
    all_tags_from_user,
    is_comment_verified,
    get_today,
)

blog = Blueprint("blog", __name__, template_folder="../templates/blog/")


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
    ###################################################################

    # redis and logging

    ###################################################################

    logger.debug(f"The landing page was visited from {request.remote_addr}.")
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"landing_page_{today}", request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("landing_page.html")


@blog.route("/login", methods=["GET", "POST"])
def login():
    ###################################################################

    # early returns

    ###################################################################

    if request.method == "GET":
        logger.debug(f"{request.path} was visited from {request.remote_addr}.")

        if current_user.is_authenticated:
            flash("You are already logged in.")
            logger.debug(f"Attempt to duplicate logging in from {request.remote_addr}.")
            return redirect(url_for("backstage.panel"))

        return render_template("login.html")

    # find user in db
    login_form = request.form.to_dict()
    if not db_users.login.exists("email", login_form["email"]):
        flash("Account not found. Please try again.", category="error")
        logger.debug(
            f'Login failed. type: email {login_form["email"]} not found. IP: {request.remote_addr}.'
        )
        return render_template("login.html")

    # check pw
    user_creds = db_users.login.find_one({"email": login_form["email"]})
    encoded_input_pw = login_form["password"].encode("utf8")
    encoded_valid_user_pw = user_creds["password"].encode("utf8")

    if not bcrypt.checkpw(encoded_input_pw, encoded_valid_user_pw):
        flash("Invalid password. Please try again.", category="error")
        logger.debug(
            f"Login failed. type: incorrect password. IP: {request.remote_addr}."
        )
        return render_template("login.html")

    ###################################################################

    # main actions

    ###################################################################

    user = User(user_creds)
    login_user(user)
    logger.info(
        f'User {user_creds["username"]} has logged in from {request.remote_addr}.'
    )
    flash("Login Succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.overview"))


@blog.route("/register", methods=["GET", "POST"])
def register():
    ###################################################################

    # early returns

    ###################################################################

    if request.method == "GET":
        logger.debug(f"{request.path} was visited from {request.remote_addr}.")
        return render_template("register.html")

    ###################################################################

    # main actions

    ###################################################################

    reg_form = request.form.to_dict()
    create_user(reg_form=reg_form)
    logger.info(
        f'New user {reg_form["username"]} has been created from {request.remote_addr}'
    )
    flash("Registeration succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("blog.login"))


@blog.route("/<username>", methods=["GET"])
def redirect_home(username):
    return redirect(url_for("blog.home", username=username))


@blog.route("/<username>/home", methods=["GET"])
def home(username):
    ###################################################################

    # early returns

    ###################################################################

    if not db_users.info.exists("username", username):
        logger.debug(
            f"Invalid username {username} at {request.path}. IP: {request.remote_addr}."
        )
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": username})
    featured_posts = db_posts.find_featured_posts_info(username)
    for post in featured_posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"{username}_home", request)
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("home.html", user=user, posts=featured_posts)


@blog.route("/<username>/tags", methods=["GET"])
def tag(username):
    ###################################################################

    # early returns

    ###################################################################

    if not db_users.info.exists("username", username):
        logger.debug(
            f"Invalid username {username} at {request.path}. IP: {request.remote_addr}."
        )
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
    all_tags = all_tags_from_user(username)
    if tag not in all_tags.keys():
        abort(404)

    user = db_users.info.find_one({"username": username})
    posts = db_posts.find_all_posts_info(username)

    posts_with_desired_tag = []
    for post in posts:
        if tag in post["tags"]:
            post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
            posts_with_desired_tag.append(post)

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_tag: {tag}", request)
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.full_path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "tag.html",
        user=user,
        posts=posts_with_desired_tag,
        tag=tag
    )


@blog.route("/<username>/posts/<post_uid>", methods=["GET", "POST"])
def post(username, post_uid):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not db_users.info.exists("username", username):
        logger.debug(
            f"Post for invalid user {username} was entered. type: invalid username. IP: {request.remote_addr}."
        )
        abort(404)
    if not db_posts.info.exists("post_uid", post_uid):
        logger.debug(
            f"Tags for invalid user {username} was entered. type: invalid post id {post_uid}. IP: {request.remote_addr}."
        )
        abort(404)

    author_by_post_uid = db_posts.info.find_one({'post_uid': post_uid})['author']
    if username != author_by_post_uid: 
        logger.debug(
            f"The author entered ({username}) was not the author of the post {post_uid}. IP: {request.remote_addr}."
        )
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    author_info = db_users.info.find_one({"username": username})
    target_post = db_posts.get_full_post(post_uid)

    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    target_post["content"] = md.convert(target_post["content"])
    target_post["content"] = HTML_Formatter(html=target_post["content"]).to_blogpost()
    target_post["last_updated"] = target_post["last_updated"].strftime("%Y-%m-%d")

    # find comments
    # oldest to newest comment
    comments = db_comments.find_comments_by_post_uid(post_uid)
    for comment in comments:
        comment["created_at"] = comment["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    # add comments
    if request.method == "POST":

        token = request.form.get("g-recaptcha-response")

        if is_comment_verified(token):

            create_comment(post_uid, request)
            db_posts.info.simple_update(
                filter={"post_uid": post_uid},
                update={"comments": target_post["comments"] + 1}
            )
            flash("Comment published!", category="success")

    ###################################################################

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"post_uid_{target_post['post_uid']}", request)
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blogpost.html", 
        user=author_info, 
        post=target_post, 
        comments=comments
    )


@blog.route("/<username>/about", methods=["GET"])
def about(username):
    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not db_users.info.exists("username", username):
        logger.debug(
            f"Invalid username {username} at {request.path}. IP: {request.remote_addr}."
        )
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": username})
    user_about = db_users.about.find_one({"username": username})["about"]

    md = Markdown(extensions=["markdown_captions", "fenced_code"])
    about = md.convert(user_about)
    about = HTML_Formatter(about).to_about()

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_about", request)
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "about.html", 
        user=user, 
        about=about
    )


@blog.route("/<username>/blog", methods=["GET"])
def blogg(username):
    ###################################################################

    # early returns

    ###################################################################

    if not db_users.info.exists("username", username):
        logger.debug(
            f"Invalid username {username} at {request.path}. IP: {request.remote_addr}."
        )
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": username})
    current_page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 10

    # create a tag dict
    tags_dict = all_tags_from_user(username)

    # set up pagination
    pagination = Pagination(username, current_page, POSTS_EACH_PAGE)
    allow_previous_page = pagination.is_previous_page_allowed()
    allow_next_page = pagination.is_next_page_allowed()

    # skip and limit posts with given page
    posts = db_posts.find_posts_with_pagination(
        username=username,
        page_number=current_page,
        posts_per_page=POSTS_EACH_PAGE
    )
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_blog", request)
    today = get_today().strftime("%Y%m%d")
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f"{request.path} was visited from {request.remote_addr}.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blog.html",
        user=user,
        posts=posts,
        tags=tags_dict,
        current_page=current_page,
        allow_previous_page=allow_previous_page,
        allow_next_page=allow_next_page,
    )


@blog.route("/<username>/get-profile-pic", methods=["GET"])
def profile_img_endpoint(username):
    user = db_users.info.find_one({"username": username})
    if user["profile_img_url"]:
        profile_img_url = user["profile_img_url"]
    else:
        profile_img_url = "/static/img/default-profile.png"

    return jsonify({"imageUrl": profile_img_url})
