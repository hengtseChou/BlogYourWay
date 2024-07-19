from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from blogyourway.config import TEMPLATE_FOLDER
from blogyourway.forms.posts import EditPostForm, NewPostForm
from blogyourway.forms.users import (
    EditAboutForm,
    GeneralSettingsForm,
    UpdatePasswordForm,
    UpdateSocialLinksForm,
    UserDeletionForm,
)
from blogyourway.logging import logger, logger_utils
from blogyourway.mongo import mongodb
from blogyourway.tasks.posts import create_post, post_utils, update_post
from blogyourway.tasks.projects import create_project, projects_utils, update_project
from blogyourway.tasks.users import user_utils
from blogyourway.tasks.utils import Paging, string_truncate, switch_to_bool
from blogyourway.views.main import flashing_if_errors

backstage = Blueprint("backstage", __name__, template_folder=TEMPLATE_FOLDER)


@backstage.route("/", methods=["GET"])
@login_required
def backstage_root():
    return redirect(url_for("backstage.posts_panel"))


@backstage.route("/posts", methods=["GET", "POST"])
@login_required
def posts_panel():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "posts"
    logger_utils.backstage(username=current_user.username, tab="posts")

    ###################################################################

    # main actions

    ###################################################################

    current_page = request.args.get("page", default=1, type=int)
    user = mongodb.user_info.find_one({"username": current_user.username})

    form = NewPostForm()

    if form.validate_on_submit():
        # logging for this is inside the create post function
        post_uid = create_post(form)
        if post_uid is not None:
            logger.debug(f"post {post_uid} has been created.")
            flash("New post published successfully!", category="success")

    flashing_if_errors(form.errors)

    # query through posts
    # 20 posts for each page
    POSTS_EACH_PAGE = 20
    paging = Paging(db_handler=mongodb)
    pagination = paging.setup(current_user.username, "post_info", current_page, POSTS_EACH_PAGE)
    posts = post_utils.find_posts_with_pagination(
        username=current_user.username,
        page_number=current_page,
        posts_per_page=POSTS_EACH_PAGE,
    )
    for post in posts:
        post["title"] = string_truncate(post.get("title"), 30)
        post["views"] = format(post.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post.get("post_uid")})
        post["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="posts", num=len(posts))

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "backstage/posts.html", user=user, posts=posts, pagination=pagination, form=form
    )


@backstage.route("/projects", methods=["GET", "POST"])
@login_required
def projects_panel():

    session["user_current_tab"] = "projects"
    logger_utils.backstage(username=current_user.username, tab="projects")

    current_page = request.args.get("page", default=1, type=int)

    if request.method == "POST":

        project_uid = create_project(request)
        if project_uid is not None:
            logger.debug(f"project {project_uid} has been created.")
            flash("New project published successfully!", category="success")

    user = mongodb.user_info.find_one({"username": current_user.username})
    PROJECTS_PER_PAGE = 10
    projects = projects_utils.find_projects_with_pagination(
        current_user.username, current_page, PROJECTS_PER_PAGE
    )
    paging = Paging(mongodb)
    paging.setup(current_user.username, "project_info", current_page, PROJECTS_PER_PAGE)

    for project in projects:
        project["title"] = string_truncate(project.get("title"), 40)
        project["views"] = format(project.get("views"), ",")

    logger_utils.pagination(tab="posts", num=len(projects))

    return render_template(
        "backstage/projects.html", user=user, projects=projects, pagination=paging
    )


@backstage.route("/archive", methods=["GET"])
@login_required
def archive_panel():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "archive"
    logger_utils.backstage(username=current_user.username, tab="archive")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    posts = post_utils.find_all_archived_posts_info(current_user.username)
    for post in posts:
        post["views"] = format(post.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post.get("post_uid")})
        post["comments"] = format(comment_count, ",")
    projects = projects_utils.find_all_archived_project_info(current_user.username)
    for project in projects:
        project["created_at"] = project.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
        project["views"] = format(project.get("views"), ",")

    logger_utils.pagination(tab="archive", num=(len(posts) + len(projects)))

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("backstage/archive.html", user=user, posts=posts, projects=projects)


@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme_panel():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="theme")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("backstage/theme.html", user=user)


@backstage.route("/settings", methods=["GET", "POST"])
@login_required
def settings_panel():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="settings")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    form_general = GeneralSettingsForm(prefix="general")
    form_social = UpdateSocialLinksForm(prefix="social")
    form_update_pw = UpdatePasswordForm(prefix="pw")
    form_deletion = UserDeletionForm(prefix="deletion")

    if form_general.submit_settings.data and form_general.validate_on_submit():

        mongodb.user_info.update_values(
            filter={"username": current_user.username},
            update={
                "cover_url": form_general.cover_url.data,
                "blogname": form_general.blogname.data,
                "gallery_enabled": form_general.gallery_enabled.data,
                "changelog_enabled": form_general.changelog_enabled.data,
            },
        )
        logger.debug(f"general settings for {current_user.username} has been updated")
        flash("Update succeeded!", category="success")
        user = mongodb.user_info.find_one({"username": current_user.username})

    if form_social.submit_links.data and form_social.validate_on_submit():

        updated_links = []
        for i in range(5):
            url = form_social.data.get(f"url{i}", "")
            platform = form_social.data.get(f"platform{i}", "")
            if url and platform:
                updated_links.append((url, platform))
        while len(updated_links) < 5:
            updated_links.append(tuple())

        mongodb.user_info.update_values(
            filter={"username": current_user.username},
            update={"social_links": updated_links},
        )
        logger.debug(f"social links for {current_user.username} has been updated.")
        flash("Social Links updated!", category="success")
        user = mongodb.user_info.find_one({"username": current_user.username})

    if form_update_pw.submit_pw.data and form_update_pw.validate_on_submit():

        current_pw = form_update_pw.current_pw.data
        current_pw_encoded = current_pw.encode("utf-8")
        user_creds = mongodb.user_creds.find_one({"username": current_user.username})
        real_pw_encoded = user_creds.get("password").encode("utf-8")
        if not checkpw(current_pw_encoded, real_pw_encoded):
            logger.debug("invalid old password when changing password.")
            flash("Invalid current password. Please try again.", category="error")
            return render_template(
                "backstage/settings.html",
                user=user,
                form_general=form_general,
                form_social=form_social,
                form_update_pw=form_update_pw,
                form_deletion=form_deletion,
            )

        new_pw = form_update_pw.new_pw.data
        new_pw_hashed = hashpw(new_pw.encode("utf-8"), gensalt(12)).decode("utf-8")
        mongodb.user_creds.update_values(
            filter={"username": current_user.username},
            update={"password": new_pw_hashed},
        )
        logger.debug(f"password for user {current_user.username} has been updated.")
        flash("Password update succeeded!", category="success")

    if form_deletion.submit_delete.data and form_deletion.validate_on_submit():

        pw = form_deletion.password.data
        pw_encoded = pw.encode("utf-8")
        user_creds = mongodb.user_creds.find_one({"username": current_user.username})
        real_pw_encoded = user_creds.get("password").encode("utf-8")

        if not checkpw(pw_encoded, real_pw_encoded):
            flash("Invalid password. Access denied.", category="error")
            return render_template(
                "backstage/settings.html",
                user=user,
                form_general=form_general,
                form_social=form_social,
                form_update_pw=form_update_pw,
                form_deletion=form_deletion,
            )

        # deletion procedure
        username = current_user.username
        logout_user()
        logger_utils.logout(request=request, username=username)
        user_utils.delete_user(username)
        flash("Account deleted successfully!", category="success")
        logger.debug(f"User {username} has been deleted.")
        return redirect(url_for("main.signup"))

    flashing_if_errors(form_general.errors)
    flashing_if_errors(form_social.errors)
    flashing_if_errors(form_update_pw.errors)
    flashing_if_errors(form_deletion.errors)

    ###################################################################

    # return page contents

    ###################################################################

    return render_template(
        "backstage/settings.html",
        user=user,
        form_general=form_general,
        form_social=form_social,
        form_update_pw=form_update_pw,
        form_deletion=form_deletion,
    )


@backstage.route("/edit/post/<post_uid>", methods=["GET", "POST"])
@login_required
def edit_post(post_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="edit_post")

    ###################################################################

    # main actions

    ###################################################################

    form = EditPostForm()

    if form.validate_on_submit():

        update_post(post_uid, form)
        logger.debug(f"post {post_uid} is updated.")
        title = mongodb.post_info.find_one({"post_uid": post_uid}).get("title")
        title_truncated = string_truncate(title, max_len=20)
        flash(f'Your post "{title_truncated}" has been updated!', category="success")

    flashing_if_errors(form.errors)

    user = mongodb.user_info.find_one({"username": current_user.username})
    post = post_utils.get_full_post(post_uid)
    post["tags"] = ", ".join(post.get("tags"))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("backstage/edit-post.html", post=post, user=user, form=form)


@backstage.route("/about", methods=["GET", "POST"])
@login_required
def edit_about():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="about")

    ###################################################################

    # main actions

    ###################################################################

    user_info = mongodb.user_info.find_one({"username": current_user.username})
    user_about = mongodb.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    form = EditAboutForm()
    if form.validate_on_submit():
        updated_info = {
            "profile_img_url": form.profile_img_url.data,
            "short_bio": form.short_bio.data,
        }
        updated_about = {"about": form.editor.data}
        mongodb.user_info.update_values(
            filter={"username": user.get("username")}, update=updated_info
        )
        mongodb.user_about.update_values(
            filter={"username": user.get("username")}, update=updated_about
        )
        user.update(updated_info)
        user.update(updated_about)
        logger.debug(f"information for user {current_user.username} has been updated")
        flash("Information updated!", category="success")

    flashing_if_errors(form.errors)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("backstage/edit-about.html", user=user, form=form)


@backstage.route("/edit/project/<project_uid>", methods=["GET"])
@login_required
def edit_project_get(project_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="edit_project")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    project = projects_utils.get_full_project(project_uid)
    project["tags"] = ", ".join(project.get("tags"))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("backstage/edit-project.html", project=project, user=user)


@backstage.route("/edit/project/<project_uid>", methods=["POST"])
@login_required
def edit_project_post(project_uid):
    ###################################################################

    # main actions

    ###################################################################

    update_project(project_uid, request)
    logger.debug(f"project {project_uid} is updated.")
    title_truncated = string_truncate(
        mongodb.project_info.find_one({"project_uid": project_uid}).get("title"),
        max_len=20,
    )
    flash(f'Your project "{title_truncated}" has been updated!', category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.projects_panel"))


@backstage.route("/edit-featured", methods=["GET"])
@login_required
def toggle_featured():
    ###################################################################

    # status control / early returns

    ###################################################################

    ###################################################################

    # main actions

    ###################################################################

    post_uid = request.args.get("uid")
    truncated_post_title = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )

    if request.args.get("featured") == "to_true":
        updated_featured_status = True
        flash(
            f'Your post "{truncated_post_title}" is now featured on the home page!',
            category="success",
        )

    else:
        updated_featured_status = False
        flash(
            f'Your post "{truncated_post_title}" is now removed from the home page!',
            category="success",
        )

    mongodb.post_info.update_values(
        filter={"post_uid": post_uid}, update={"featured": updated_featured_status}
    )
    logger.debug(f"featuring status for post {post_uid} is now set to {updated_featured_status}")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.posts_panel"))


@backstage.route("/edit-archived", methods=["GET"])
@login_required
def toggle_archived():
    ###################################################################

    # status control / early returns

    ###################################################################

    ###################################################################

    # main actions

    ###################################################################

    content_type = request.args.get("type")

    if content_type == "post":

        post_uid = request.args.get("uid")
        post_info = mongodb.post_info.find_one({"post_uid": post_uid})

        author = post_info.get("author")
        tags = post_info.get("tags")
        title_truncated = string_truncate(post_info.get("title"), max_len=20)

        if request.args.get("archived") == "to_true":
            updated_archived_status = True
            tags_increment = {f"tags.{tag}": -1 for tag in tags}
            flash(f'Your post "{title_truncated}" is now archived!', category="success")
        else:
            updated_archived_status = False
            tags_increment = {f"tags.{tag}": 1 for tag in tags}
            flash(
                f'Your post "{title_truncated}" is now restored from the archive!',
                category="success",
            )

        mongodb.post_info.update_values(
            filter={"post_uid": post_uid}, update={"archived": updated_archived_status}
        )
        mongodb.user_info.make_increments(
            filter={"username": author}, increments=tags_increment, upsert=True
        )
        logger.debug(f"archive status for post {post_uid} is now set to {updated_archived_status}")

    elif content_type == "project":

        project_uid = request.args.get("uid")
        project_info = mongodb.project_info.find_one({"project_uid": project_uid})

        author = project_info.get("author")
        title_truncated = string_truncate(project_info.get("title"), max_len=20)

        if request.args.get("archived") == "to_true":
            updated_archived_status = True
            flash(f'Your project "{title_truncated}" is now archived!', category="success")
        else:
            updated_archived_status = False
            flash(
                f'Your project "{title_truncated}" is now restored from the archive!',
                category="success",
            )

        mongodb.project_info.update_values(
            filter={"project_uid": project_uid},
            update={"archived": updated_archived_status},
        )
        logger.debug(
            f"archive status for project {project_uid} is now set to {updated_archived_status}"
        )

    ###################################################################

    # return page contents

    ###################################################################

    if session["user_current_tab"] == "posts":
        return redirect(url_for("backstage.posts_panel"))

    elif session["user_current_tab"] == "archive":
        return redirect(url_for("backstage.archive_panel"))

    elif session["user_current_tab"] == "projects":
        return redirect(url_for("backstage.projects_panel"))


@backstage.route("/delete/post", methods=["GET"])
@login_required
def delete_post():
    ###################################################################

    # status control / early returns

    ###################################################################

    post_uid = request.args.get("uid")

    ###################################################################

    # main actions

    ###################################################################

    title_truncated = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    mongodb.post_info.delete_one({"post_uid": post_uid})
    mongodb.post_content.delete_one({"post_uid": post_uid})
    logger.debug(f"post {post_uid} has been deleted")
    flash(f'Your post "{title_truncated}" has been deleted!', category="success")
    # post must be archived before deletion
    # so no need to increment over tags here

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage.archive_panel"))


@backstage.route("/delete/project", methods=["GET"])
@login_required
def delete_project():
    ###################################################################

    # status control / early returns

    ###################################################################

    project_uid = request.args.get("uid")

    ###################################################################

    # main actions

    ###################################################################

    title_truncated = string_truncate(
        mongodb.project_info.find_one({"project_uid": project_uid}).get("title"),
        max_len=20,
    )
    mongodb.project_info.delete_one({"project_uid": project_uid})
    mongodb.project_content.delete_one({"project_uid": project_uid})
    logger.debug(f"project {project_uid} has been deleted")
    flash(f'Your project "{title_truncated}" has been deleted!', category="success")
    # post must be archived before deletion
    # so no need to increment over tags here

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage/backstage.archive_panel"))


@backstage.route("/logout", methods=["GET"])
@login_required
def logout():
    ###################################################################

    # main actions

    ###################################################################

    username = current_user.username
    logout_user()
    logger_utils.logout(request=request, username=username)

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("frontstage.home", username=username))
