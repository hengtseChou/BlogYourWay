from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from blogyourway.helpers.common import Paging, string_truncate, switch_to_bool
from blogyourway.helpers.posts import create_post, post_utils, update_post
from blogyourway.helpers.projects import create_project, projects_utils
from blogyourway.helpers.users import user_utils
from blogyourway.services.logging import logger, logger_utils
from blogyourway.services.mongo import mongodb

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


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

    if request.method == "POST":
        # logging for this is inside the create post function
        post_uid = create_post(request)
        if post_uid is not None:
            logger.debug(f"post {post_uid} has been created.")
            flash("New post published successfully!", category="success")

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
        post["created_at"] = post.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post.get("post_uid")})
        post["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="posts", num_of_posts=len(posts))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("posts.html", user=user, posts=posts, pagination=pagination)


@backstage.route("/edit/post/<post_uid>", methods=["GET"])
@login_required
def edit_post_get(post_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="edit_post")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find({"username": current_user.username})
    target_post = post_utils.get_full_post(post_uid)
    target_post["tags"] = ", ".join(target_post.get("tags"))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-post.html", post=target_post, user=user)


@backstage.route("/edit/post/<post_uid>", methods=["POST"])
@login_required
def edit_post_post(post_uid):
    ###################################################################

    # main actions

    ###################################################################

    update_post(post_uid, request)
    logger.debug(f"post {post_uid} is updated.")
    title_truncated = string_truncate(
        mongodb.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    flash(f'Your post "{title_truncated}" has been updated!', category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.posts_panel"))


@backstage.route("/edit-featured", methods=["GET"])
@login_required
def edit_featured():
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
def edit_archived():
    ###################################################################

    # status control / early returns

    ###################################################################

    ###################################################################

    # main actions

    ###################################################################

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

    ###################################################################

    # return page contents

    ###################################################################

    if session["user_current_tab"] == "posts":
        return redirect(url_for("backstage.posts_panel"))

    elif session["user_current_tab"] == "archive":
        return redirect(url_for("backstage.archive_panel"))


@backstage.route("/about", methods=["GET"])
@login_required
def edit_about_get():
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

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-about.html", user=user)


@backstage.route("/about", methods=["POST"])
@login_required
def edit_about_post():
    ###################################################################

    # main actions

    ###################################################################

    user_info = mongodb.user_info.find_one({"username": current_user.username})
    user_about = mongodb.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    form = request.form.to_dict()
    updated_info = {"profile_img_url": form.get("profile_img_url"), "short_bio": form["short_bio"]}
    updated_about = {"about": form.get("about")}
    mongodb.user_info.update_values(filter={"username": user.get("username")}, update=updated_info)
    mongodb.user_about.update_values(
        filter={"username": user.get("username")}, update=updated_about
    )
    user.update(updated_info)
    user.update(updated_about)
    logger.debug(f"information for user {current_user.username} has been updated")
    flash("Information updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-about.html", user=user)


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
        post["created_at"] = post.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"post_uid": post.get("post_uid")})
        post["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="archive", num_of_posts=len(posts))

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("archive.html", user=user, posts=posts)


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

    return render_template("theme.html", user=user)


@backstage.route("/settings", methods=["GET"])
@login_required
def settings_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="settings")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/settings", methods=["POST"])
@login_required
def settings_post():
    ###################################################################

    # main actions

    ###################################################################

    general = request.form.get("general")
    change_pw = request.form.get("changepw")
    social_links = request.form.get("social-links")
    delete_account = request.form.get("delete-account")

    if general is not None:
        cover_url = request.form.get("cover_url")
        blogname = request.form.get("blogname")
        enable_changelog = switch_to_bool(request.form.get("changelog_enabled"))
        enable_portfolio = switch_to_bool(request.form.get("gallery_enabled"))

        mongodb.user_info.update_values(
            filter={"username": current_user.username},
            update={
                "cover_url": cover_url,
                "blogname": blogname,
                "changelog_enabled": enable_changelog,
                "gallery_enabled": enable_portfolio,
            },
        )
        logger.debug(f"general settings for {current_user.username} has been updated")
        flash("Update succeeded!", category="success")

    elif social_links is not None:
        user = mongodb.user_info.find_one({"username": current_user.username})
        form = request.form.to_dict()
        form_values = list(form.values())

        updated_links = []
        for i in range(0, len(form_values) - 1, 2):
            updated_links.append({"platform": form_values[i + 1], "url": form_values[i]})
        mongodb.user_info.update_values(
            filter={"username": current_user.username}, update={"social_links": updated_links}
        )
        logger.debug(f"social links for {current_user.username} has been updated.")
        flash("Social Links updated!", category="success")

    elif change_pw is not None:
        current_pw_input = request.form.get("current")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        new_pw = request.form.get("new")

        user_creds = mongodb.user_creds.find_one({"username": current_user.username})
        user = mongodb.user_info.find_one({"username": current_user.username})
        encoded_valid_user_pw = user_creds.get("password").encode("utf8")

        # check pw
        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            logger.debug("invalid old password when changing password.")
            flash("Current password is invalid. Please try again.", category="error")
            return render_template("settings.html", user=user)

        # update new password
        hashed_new_pw = hashpw(new_pw.encode("utf-8"), gensalt(12)).decode("utf-8")
        mongodb.user_creds.update_values(
            filter={"username": current_user.username}, update={"password": hashed_new_pw}
        )
        logger.debug(f"password for user {current_user.username} has been updated.")
        flash("Password update succeeded!", category="success")

    elif delete_account is not None:
        current_pw_input = request.form.get("delete-confirm-pw")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        username = current_user.username
        user = mongodb.user_info.find_one({"username": username})
        user_creds = mongodb.user_creds.find_one({"username": username})
        encoded_valid_user_pw = user_creds.get("password").encode("utf8")

        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            flash("Access denied, bacause password is invalid.", category="error")
            return render_template("settings.html", user=user)

        # deletion procedure
        logout_user()
        logger_utils.logout(request=request, username=username)
        user_utils.delete_user(username)
        flash("Account deleted successfully!", category="success")
        logger.debug(f"User {username} has been deleted.")
        return redirect(url_for("frontstage.register_get"))

    user = mongodb.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page content

    ###################################################################

    return render_template("settings.html", user=user)


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


@backstage.route("/projects", methods=["GET", "POST"])
@login_required
def projects_panel():

    session["user_current_tab"] = "projects"
    logger_utils.backstage(username=current_user.username, tab="projects")

    user = mongodb.user_info.find_one({"username": current_user.username})

    if request.method == "POST":

        project_uid = create_project(request)
        if project_uid is not None:
            logger.debug(f"project {project_uid} has been created.")
            flash("New project published successfully!", category="success")

    user = mongodb.user_info.find_one({"username": current_user.username})
    projects = projects_utils.find_projects_info_by_username(current_user.username)

    return render_template("projects.html", user=user, projects=projects)
