from urllib.parse import unquote

import readtime
from flask import (
    Blueprint,
    Request,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.config import TEMPLATE_FOLDER
from app.forms.comments import CommentForm
from app.helpers.comments import comment_utils, create_comment
from app.helpers.posts import post_utils
from app.helpers.projects import projects_utils
from app.helpers.users import user_utils
from app.helpers.utils import (
    Paging,
    convert_about,
    convert_post_content,
    convert_project_content,
    sort_dict,
)
from app.logging import logger, logger_utils
from app.mongo import mongodb
from app.views.main import flashing_if_errors

frontstage = Blueprint("frontstage", __name__, template_folder=TEMPLATE_FOLDER)


@frontstage.route("/@<username>", methods=["GET"])
def home(username: str) -> str:
    """Render the home page for a given user.

    Args:
        username (str): The username of the user whose home page is to be rendered.

    Returns:
        str: Rendered HTML of the home page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)

    user = mongodb.user_info.find_one({"username": username})
    featured_posts = post_utils.get_featured_posts_info(username)

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    return render_template("frontstage/home.html", user=user, posts=featured_posts)


@frontstage.route("/@<username>/blog", methods=["GET"])
def blog(username: str) -> str:
    """Render the blog page for a given user with pagination.

    Args:
        username (str): The username of the user whose blog page is to be rendered.

    Returns:
        str: Rendered HTML of the blog page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)

    current_page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 5
    paging = Paging(mongodb)
    pagination = paging.setup(username, "post_info", current_page, POSTS_EACH_PAGE)

    posts = post_utils.get_posts_info_with_pagination(
        username=username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )

    user = user_utils.get_user_info(username)
    tags = sort_dict(user.tags)
    tags = {tag: count for tag, count in tags.items() if count > 0}

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    return render_template(
        "frontstage/blog.html", user=user, posts=posts, tags=tags, pagination=pagination
    )


def blogpost_main_actions(username: str, post_uid: str, request: Request) -> str:
    """Handle the main actions for rendering a blog post.

    Args:
        username (str): The username of the post author.
        post_uid (str): The unique identifier of the post.
        request (Request): The Flask request object.

    Returns:
        str: Rendered HTML of the blog post page.
    """
    author = mongodb.user_info.find_one({"username": username})
    post = post_utils.get_full_post(post_uid)

    post["content"] = convert_post_content(post.get("content"))
    post["readtime"] = str(readtime.of_html(post.get("content")))

    form = CommentForm()
    if form.validate_on_submit():
        create_comment(post_uid, form)
        flash("Comment published!", category="success")
    flashing_if_errors(form.errors)

    comments = comment_utils.find_comments_by_post_uid(post_uid)

    logger_utils.page_visited(request)
    post_utils.view_increment(post_uid)
    user_utils.total_view_increment(username)

    return render_template(
        "frontstage/blogpost.html", user=author, post=post, comments=comments, form=form
    )


@frontstage.route("/@<username>/posts/<post_uid>", methods=["GET", "POST"])
def blogpost(username: str, post_uid: str) -> str:
    """Render a blog post page, optionally redirecting if a slug is present.

    Args:
        username (str): The username of the post author.
        post_uid (str): The unique identifier of the post.

    Returns:
        str: Rendered HTML of the blog post page or redirect to the slugged URL.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    if not mongodb.post_info.exists("post_uid", post_uid):
        logger.debug(f"Invalid post uid {post_uid}.")
        abort(404)

    post_info = mongodb.post_info.find_one({"post_uid": post_uid})
    if username != post_info.get("author"):
        logger.debug(f"User {username} does not own post {post_uid}.")
        abort(404)

    custom_slug = post_info.get("custom_slug")
    if custom_slug:
        return redirect(
            url_for(
                "frontstage.blogpost_with_slug",
                username=username,
                post_uid=post_uid,
                slug=custom_slug,
            )
        )

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/@<username>/posts/<post_uid>/<slug>", methods=["GET", "POST"])
def blogpost_with_slug(username: str, post_uid: str, slug: str) -> str:
    """Render a blog post page with a slug, or redirect if the slug does not match.

    Args:
        username (str): The username of the post author.
        post_uid (str): The unique identifier of the post.
        slug (str): The slug of the post.

    Returns:
        str: Rendered HTML of the blog post page or redirect to the correct slug URL.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    if not mongodb.post_info.exists("post_uid", post_uid):
        logger.debug(f"Invalid post uid {post_uid}.")
        abort(404)

    post_info = mongodb.post_info.find_one({"post_uid": post_uid})
    if username != post_info.get("author"):
        logger.debug(f"User {username} does not own post {post_uid}.")
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

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/@<username>/tags", methods=["GET"])
def tag(username: str) -> str:
    """Render a page showing posts and projects with a specified tag.

    Args:
        username (str): The username of the user whose posts and projects are to be displayed.

    Returns:
        str: Rendered HTML of the tag page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)

    tag_url_encoded = request.args.get("tag", default=None, type=str)
    if tag_url_encoded is None:
        return redirect(url_for("frontstage.blog", username=username))

    tag = unquote(tag_url_encoded)
    user = user_utils.get_user_info(username)

    posts = post_utils.get_posts_info(username)
    posts_with_desired_tag = [post for post in posts if tag in post.get("tags")]

    projects = projects_utils.get_projects_info(username)
    projects_with_desired_tag = [project for project in projects if tag in project.get("tags")]

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    return render_template(
        "frontstage/tag.html",
        user=user,
        posts=posts_with_desired_tag,
        projects=projects_with_desired_tag,
        tag=tag,
    )


@frontstage.route("/@<username>/gallery", methods=["GET"])
def gallery(username: str) -> str:
    """Render the gallery page for a given user.

    Args:
        username (str): The username of the user whose gallery is to be rendered.

    Returns:
        str: Rendered HTML of the gallery page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    user = user_utils.get_user_info(username)
    if not user.gallery_enabled:
        logger.debug(f"User {username} did not enable gallery feature.")
        abort(404)

    current_page = request.args.get("page", default=1, type=int)
    PROJECTS_EACH_PAGE = 12
    paging = Paging(mongodb)
    pagination = paging.setup(username, "project_info", current_page, PROJECTS_EACH_PAGE)

    projects = projects_utils.get_projects_info_with_pagination(
        username=username,
        page_number=current_page,
        projects_per_page=PROJECTS_EACH_PAGE,
    )
    for project in projects:
        project["created_at"] = project.get("created_at").strftime("%Y-%m-%d")

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    return render_template(
        "frontstage/gallery.html", user=user, projects=projects, pagination=pagination
    )


def project_main_actions(username: str, project_uid: str, request: Request) -> str:
    """Handle the main actions for rendering a project page.

    Args:
        username (str): The username of the project author.
        project_uid (str): The unique identifier of the project.
        request (Request): The Flask request object.

    Returns:
        str: Rendered HTML of the project page.
    """
    author = mongodb.user_info.find_one({"username": username})
    project = projects_utils.get_full_project(project_uid)
    project["content"] = convert_project_content(project.get("content"))

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)
    projects_utils.view_increment(project_uid)

    return render_template("frontstage/project.html", user=author, project=project)


@frontstage.route("/@<username>/project/<project_uid>", methods=["GET"])
def project(username: str, project_uid: str) -> str:
    """Render a project page, optionally redirecting if a slug is present.

    Args:
        username (str): The username of the project author.
        project_uid (str): The unique identifier of the project.

    Returns:
        str: Rendered HTML of the project page or redirect to the slugged URL.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    if not mongodb.project_info.exists("project_uid", project_uid):
        logger.debug(f"Invalid project uid {project_uid}.")
        abort(404)

    project_info = mongodb.project_info.find_one({"project_uid": project_uid})
    if username != project_info.get("author"):
        logger.debug(f"User {username} does not own project {project_uid}.")
        abort(404)

    custom_slug = project_info.get("custom_slug")
    if custom_slug:
        return redirect(
            url_for(
                "frontstage.project_with_slug",
                username=username,
                project_uid=project_uid,
                slug=custom_slug,
            )
        )

    return project_main_actions(username, project_uid, request)


@frontstage.route("/@<username>/project/<project_uid>/<slug>", methods=["GET"])
def project_with_slug(username: str, project_uid: str, slug: str) -> str:
    """Render a project page with a slug, or redirect if the slug does not match.

    Args:
        username (str): The username of the project author.
        project_uid (str): The unique identifier of the project.
        slug (str): The slug of the project.

    Returns:
        str: Rendered HTML of the project page or redirect to the correct slug URL.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    if not mongodb.project_info.exists("project_uid", project_uid):
        logger.debug(f"Invalid project uid {project_uid}.")
        abort(404)

    project_info = mongodb.project_info.find_one({"project_uid": project_uid})
    if username != project_info.get("author"):
        logger.debug(f"User {username} does not own project {project_uid}.")
        abort(404)

    custom_slug = project_info.get("custom_slug")
    if custom_slug != slug:
        return redirect(
            url_for(
                "frontstage.project_with_slug",
                username=username,
                project_uid=project_uid,
                slug=custom_slug,
            )
        )

    return project_main_actions(username, project_uid, request)


@frontstage.route("/@<username>/changelog", methods=["GET"])
def changelog(username: str) -> str:
    """Render the changelog page for a given user.

    Args:
        username (str): The username of the user whose changelog is to be rendered.

    Returns:
        str: Rendered HTML of the changelog page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)
    user = user_utils.get_user_info(username)
    if not user.changelog_enabled:
        logger.debug(f"User {username} did not enable changelog feature.")
        abort(404)

    return render_template("frontstage/changelog.html", user=user)


@frontstage.route("/@<username>/about", methods=["GET"])
def about(username: str) -> str:
    """Render the about page for a given user.

    Args:
        username (str): The username of the user whose about page is to be rendered.

    Returns:
        str: Rendered HTML of the about page.
    """
    if not mongodb.user_info.exists("username", username):
        logger.debug(f"Invalid username {username}.")
        abort(404)

    user = mongodb.user_info.find_one({"username": username})
    about = mongodb.user_about.find_one({"username": username}).get("about")
    about = convert_about(about)

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    return render_template("frontstage/about.html", user=user, about=about)


@frontstage.route("/@<username>/get-profile-img", methods=["GET"])
def get_profile_img(username: str) -> str:
    """Get the profile image URL of a user.

    Args:
        username (str): The username of the user.

    Returns:
        str: JSON response containing the profile image URL. Retrieve with key 'imageUrl'.
    """
    user = user_utils.get_user_info(username)
    return jsonify({"imageUrl": user.profile_img_url})


@frontstage.route("/is-unique", methods=["GET"])
def is_unique() -> str:
    """Check if the email or username is unique.

    Returns:
        str: JSON response indicating if the email or username is unique.
    """
    email = request.args.get("email", default=None, type=str)
    username = request.args.get("username", default=None, type=str)
    if email is not None:
        return jsonify(not mongodb.user_info.exists(key="email", value=email))
    elif username is not None:
        return jsonify(not mongodb.user_info.exists(key="username", value=username))


@frontstage.route("/readcount-increment", methods=["GET"])
def readcount_increment() -> str:
    """Increment the read count for a post.

    Returns:
        str: Confirmation message.
    """
    post_uid = request.args.get("post_uid", type=str)
    post_utils.read_increment(post_uid)
    return "OK"
