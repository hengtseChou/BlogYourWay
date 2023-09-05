import bcrypt
import markdown
from urllib.parse import unquote
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_user, UserMixin, current_user
from website.extensions.mongo import db_users, db_posts, db_comments
from website.extensions.redis import redis_method
from website.extensions.log import logger
from website.blog.utils import (
    HTML_Formatter,
    Pagination,
    create_user, 
    create_comment,
    all_tags_from_user,
    is_comment_verified, 
    get_today
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

    ###################################################################

    # redis and logging

    ###################################################################

    logger.debug(f'The landing page was visited from {request.remote_addr}.')
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f'landing_page_{today}', request)

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

        logger.debug(f'{request.path} was visited from {request.remote_addr}.')

        if current_user.is_authenticated:
            flash("You are already logged in.")
            logger.debug(f'Attempt to duplicate logging in from {request.remote_addr}.')
            return redirect(url_for("backstage.panel"))
                      
        return render_template("login.html")

    # find user in db
    login_form = request.form.to_dict()
    if not db_users.exists("email", login_form["email"]):
        flash("Account not found. Please try again.", category="error")
        logger.debug(f'Login failed. type: email {login_form["email"]} not found. IP: {request.remote_addr}.')
        return render_template("login.html")

    # check pw
    user_creds = db_users.login.find_one({"email": login_form["email"]})
    if not bcrypt.checkpw(login_form["password"].encode("utf8"), user_creds["password"].encode("utf8")):
        flash("Invalid password. Please try again.", category="error")
        logger.debug(f'Login failed. type: incorrect password. IP: {request.remote_addr}.')
        return render_template("login.html")
    
    ###################################################################

    # main actions

    ###################################################################

    user = User(user_creds)
    login_user(user)
    logger.info(f'User {user_creds["username"]} has logged in from {request.remote_addr}.')
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
        logger.debug(f'{request.path} was visited from {request.remote_addr}.')
        return render_template("register.html")
    
    ###################################################################

    # main actions

    ###################################################################

    reg_form = request.form.to_dict()
    create_user(reg_form=reg_form)
    logger.info(f'New user {reg_form["username"]} has been created from {request.remote_addr}')
    flash("Registeration succeeded.", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("blog.login"))

@blog.route("/<username>", methods=['GET'])
def redirect_home(username):

    return redirect(url_for('blog.home', username=username))


@blog.route("/<username>/home", methods=["GET"])
def home(username):

    ###################################################################

    # early returns

    ###################################################################

    if not db_users.exists("username", username):
        logger.debug(f'Invalid username {username} at {request.path}. IP: {request.remote_addr}.')
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": username})
    featured_posts = list(
        db_posts.info
        .find({"author": username, "featured": True, "archived": False})
        .sort("created_at", -1)
        .limit(10)
    )
    for post in featured_posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"{username}_home", request)
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f'{request.path} was visited from {request.remote_addr}.')

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "home.html", 
        user=user, 
        posts=featured_posts
    )


@blog.route("/<username>/tags", methods=["GET"])
def tag(username):

    ###################################################################

    # early returns

    ###################################################################

    if not db_users.exists("username", username):
        logger.debug(f'Invalid username {username} at {request.path}. IP: {request.remote_addr}.')
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
    posts = list(
        db_posts.info
        .find({"author": username, "archived": False})
        .sort("created_at", -1)
    )

    posts_with_desired_tag = []
    for post in posts:
        if tag in post["tags"]:
            post["created_at"] = post["created_at"].strftime("%Y-%m-%d")
            posts_with_desired_tag.append(post)

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_tag: {tag}", request)
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f'{request.full_path} was visited from {request.remote_addr}.')

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "tag.html",
        user=user,
        posts=posts_with_desired_tag,
        tag=tag,
        num_of_posts=len(posts_with_desired_tag),
    )


@blog.route("/<username>/posts/<post_uid>", methods=["GET", "POST"])
def post(username, post_uid):

    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not db_users.exists("username", username):
        logger.debug(f'Post for invalid user {username} was entered. type: invalid username. IP: {request.remote_addr}.')
        abort(404)
    if not db_posts.exists("post_uid", post_uid):
        logger.debug(f'Tags for invalid user {username} was entered. type: invalid post id {post_uid}. IP: {request.remote_addr}.')
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    author = db_users.info.find_one({"username": username})
    target_post = dict(db_posts.info.find_one({"post_uid": post_uid}))
    target_post["content"] = db_posts.content.find_one({"post_uid": post_uid})["content"]

    # to verify the post is linked to the user
    if author["username"] != target_post["author"]:
        logger.debug(f'The author entered ({username}) was not the author of the post {post_uid}. IP: {request.remote_addr}.')
        abort(404)

    # add comments
    if request.method == "POST":

        token = request.form.get("g-recaptcha-response")

        if is_comment_verified(token):

            create_comment(post_uid, request)
            
            db_posts.info.update_one(
                filter={"post_uid": post_uid},
                update={"$set": {"comments": target_post["comments"] + 1}},
            )
            flash("Comment published!", category="success")

    target_post["content"] = md.convert(target_post["content"])
    target_post["content"] = HTML_Formatter(html=target_post["content"]).to_blogpost()
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

    ###################################################################

    # redis and logging

    ###################################################################

    redis_method.increment_count(f"post_uid_{target_post['post_uid']}", request)
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f'{request.path} was visited from {request.remote_addr}.')

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "blogpost.html", 
        user=author, 
        post=target_post, 
        comments=comments
    )


@blog.route("/<username>/about", methods=["GET"])
def about(username):

    ###################################################################

    # early return for invalid inputs

    ###################################################################

    if not db_users.exists("username", username):
        logger.debug(f'Invalid username {username} at {request.path}. IP: {request.remote_addr}.')
        abort(404)

    ###################################################################

    # main actions

    ###################################################################

    user = dict(db_users.info.find_one({"username": username}))
    user_about = db_users.about.find_one({"username": username})["about"]
    about = md.convert(user_about)
    about = HTML_Formatter(about).to_about()

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_about", request)
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f'{request.path} was visited from {request.remote_addr}.')

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

    if not db_users.exists("username", username):
        logger.debug(f'Invalid username {username} at {request.path}. IP: {request.remote_addr}.')
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
    if current_page == 1:
        posts = (
            db_posts.info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .limit(POSTS_EACH_PAGE)
        )  # descending: newest
    elif current_page > 1:
        posts = (
            db_posts.info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .skip((current_page - 1) * POSTS_EACH_PAGE)
            .limit(POSTS_EACH_PAGE)
        )

    posts = list(posts)
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d")

    ###################################################################

    # visiting counts and logging

    ###################################################################

    redis_method.increment_count(f"{username}_blog", request)
    today = get_today().strftime('%Y%m%d')
    redis_method.increment_count(f"{username}_uv_{today}", request)

    logger.debug(f'{request.path} was visited from {request.remote_addr}.')

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
        allow_next_page=allow_next_page
    )

@blog.route('/<username>/get-profile-pic', methods=['GET'])
def profile_img_endpoint(username):

    user = dict(db_users.info.find_one({"username": username}))
    if user['profile_img_url']:
        profile_img_url = user['profile_img_url']
    else:
        profile_img_url = "/static/img/default-profile.png"
    
    return jsonify({'imageUrl': profile_img_url})
