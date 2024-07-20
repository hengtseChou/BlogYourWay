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
def home(username):
    ##################################################################################################

    # early returns

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ##################################################################################################

    # main actions

    ##################################################################################################

    user = mongodb.user_info.find_one({"username": username})
    featured_posts = post_utils.get_featured_posts_info(username)

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template("frontstage/home.html", user=user, posts=featured_posts)


@frontstage.route("/@<username>/blog", methods=["GET"])
def blog(username):
    ##################################################################################################

    # early returns

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ##################################################################################################

    # main actions

    ##################################################################################################

    # set up pagination
    current_page = request.args.get("page", default=1, type=int)
    POSTS_EACH_PAGE = 5
    paging = Paging(mongodb)
    pagination = paging.setup(username, "post_info", current_page, POSTS_EACH_PAGE)

    # skip and limit posts with given page
    posts = post_utils.get_posts_info_with_pagination(
        username=username, page_number=current_page, posts_per_page=POSTS_EACH_PAGE
    )

    # user info
    user = user_utils.get_user_info(username)
    tags = sort_dict(user.tags)
    tags = {tag: count for tag, count in tags.items() if count > 0}

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template(
        "frontstage/blog.html", user=user, posts=posts, tags=tags, pagination=pagination
    )


def blogpost_main_actions(username: str, post_uid: str, request: Request) -> str:

    author = mongodb.user_info.find_one({"username": username})
    post = post_utils.get_full_post(post_uid)

    post["content"] = convert_post_content(post.get("content"))
    post["readtime"] = str(readtime.of_html(post.get("content")))

    form = CommentForm()
    # add comments
    # this section should be placed before finding comments to show on the post
    if form.validate_on_submit():
        create_comment(post_uid, form)
        flash("Comment published!", category="success")
    flashing_if_errors(form.errors)

    # find comments
    # oldest to newest comment
    comments = comment_utils.find_comments_by_post_uid(post_uid)

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    post_utils.view_increment(post_uid)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template(
        "frontstage/blogpost.html", user=author, post=post, comments=comments, form=form
    )


@frontstage.route("/@<username>/posts/<post_uid>", methods=["GET", "POST"])
def blogpost(username, post_uid):
    ##################################################################################################

    # early return for invalid inputs

    ##################################################################################################

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

    ##################################################################################################

    # main actions

    ##################################################################################################

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/@<username>/posts/<post_uid>/<slug>", methods=["GET", "POST"])
def blogpost_with_slug(username, post_uid, slug):
    ##################################################################################################

    # early return for invalid inputs

    ##################################################################################################

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

    ##################################################################################################

    # main actions

    ##################################################################################################

    return blogpost_main_actions(username, post_uid, request)


@frontstage.route("/@<username>/tags", methods=["GET"])
def tag(username):
    ##################################################################################################

    # early returns

    ##################################################################################################

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

    ##################################################################################################

    # main actions

    ##################################################################################################

    posts = post_utils.get_posts_info(username)

    posts_with_desired_tag = []
    for post in posts:
        if tag in post.get("tags"):
            posts_with_desired_tag.append(post)

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template(
        "frontstage/tag.html", user=user_info, posts=posts_with_desired_tag, tag=tag
    )


@frontstage.route("/@<username>/gallery", methods=["GET"])
def gallery(username):
    ##################################################################################################

    # early returns

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ##################################################################################################

    # main actions

    ##################################################################################################

    # set up pagination
    current_page = request.args.get("page", default=1, type=int)
    PROJECTS_EACH_PAGE = 12
    paging = Paging(mongodb)
    pagination = paging.setup(username, "project_info", current_page, PROJECTS_EACH_PAGE)

    # skip and limit posts with given page
    projects = projects_utils.get_projects_info_with_pagination(
        username=username,
        page_number=current_page,
        projects_per_page=PROJECTS_EACH_PAGE,
    )
    for project in projects:
        project["created_at"] = project.get("created_at").strftime("%Y-%m-%d")

    # user info
    user = user_utils.get_user_info(username)

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template(
        "frontstage/gallery.html", user=user, projects=projects, pagination=pagination
    )


def project_main_actions(username, project_uid, request):

    ##################################################################################################

    # main actions

    ##################################################################################################

    author = mongodb.user_info.find_one({"username": username})
    project = projects_utils.get_full_project(project_uid)
    project["content"] = convert_project_content(project.get("content"))

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)
    projects_utils.view_increment(project_uid)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template("frontstage/project.html", user=author, project=project)


@frontstage.route("/@<username>/project/<project_uid>", methods=["GET"])
def project(username, project_uid):
    ##################################################################################################

    # early return for invalid inputs

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.project_info.exists("project_uid", project_uid):
        logger.debug(f"invalid post uid {project_uid}")
        abort(404)

    project_info = mongodb.project_info.find_one({"project_uid": project_uid})
    if username != project_info.get("author"):
        logger.debug(f"User {username} does not own project {project_uid}")
        abort(404)

    custom_slug = project_info.get("custom_slug")
    if custom_slug != "":
        return redirect(
            url_for(
                "frontstage.project_with_slug",
                username=username,
                project_uid=project_uid,
                slug=custom_slug,
            )
        )

    ##################################################################################################

    # main actions

    ##################################################################################################

    return project_main_actions(username, project_uid, request)


@frontstage.route("/@<username>/project/<project_uid>/<slug>", methods=["GET"])
def project_with_slug(username, project_uid, slug):
    ##################################################################################################

    # early return for invalid inputs

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)
    if not mongodb.project_info.exists("project_uid", project_uid):
        logger.debug(f"invalid post uid {project_uid}")
        abort(404)

    project_info = mongodb.project_info.find_one({"project_uid": project_uid})
    if username != project_info.get("author"):
        logger.debug(f"User {username} does not own project {project_uid}")
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

    ##################################################################################################

    # main actions

    ##################################################################################################

    return project_main_actions(username, project_uid, request)


@frontstage.route("/@<username>/changelog", methods=["GET"])
def changelog(username):
    pass


@frontstage.route("/@<username>/about", methods=["GET"])
def about(username):
    ##################################################################################################

    # early return for invalid inputs

    ##################################################################################################

    if not mongodb.user_info.exists("username", username):
        logger.debug(f"invalid username {username}")
        abort(404)

    ##################################################################################################

    # main actions

    ##################################################################################################

    user = mongodb.user_info.find_one({"username": username})
    about = mongodb.user_about.find_one({"username": username})["about"]

    about = convert_about(about)

    ##################################################################################################

    # logging / metrics

    ##################################################################################################

    logger_utils.page_visited(request)
    user_utils.total_view_increment(username)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return render_template("frontstage/about.html", user=user, about=about)


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


@frontstage.route("/readcount-increment", methods=["GET"])
def readcount_increment():
    ##################################################################################################

    # main actions

    ##################################################################################################

    post_uid = request.args.get("post_uid", type=str)
    post_utils.read_increment(post_uid)

    ##################################################################################################

    # return page content

    ##################################################################################################

    return "OK"
