from bcrypt import hashpw, checkpw, gensalt
from datetime import datetime
from flask import Blueprint, request, session, render_template, flash, redirect, url_for
from flask_login import login_required, logout_user, current_user
from application.extensions.mongo import db_users, db_posts, db_comments
from application.extensions.redis import redis_method
from application.extensions.log import logger
from application.blog.utils import Pagination
from application.backstage.utils import create_post, update_post, delete_user, switch_to_bool

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


@backstage.route("/", methods=["GET"])
@login_required
def redirect_overview():

    return url_for("backstage.overview")


@backstage.route("/overview", methods=["GET"])
@login_required
def overview():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "overview"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="overview", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    logger.debug(f"Retrieving stats for user {current_user.username} started.")

    now = datetime.now()
    user = db_users.info.find_one({"username": current_user.username})

    time_difference = now - user["created_at"]
    user["days_joined"] = format(time_difference.days + 1, ",")

    visitor_stats = redis_method.get_visitor_stats(current_user.username)
    daily_count = redis_method.get_daily_visitor_data(current_user.username)

    logger.debug(f"Retrieving stats for user {current_user.username} completed.")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "overview.html", user=user, daily_count=daily_count, visitor_stats=visitor_stats
    )


@backstage.route("/posts", methods=["GET", "POST"])
@login_required
def post_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "posts"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="posts control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    current_page = request.args.get("page", default=1, type=int)
    user = db_users.info.find_one({"username": current_user.username})

    if request.method == "POST":

        # logging for this is inside the create post function
        post_uid = create_post(request)
        db_users.info.simple_update(
            filter={"username": current_user.username},
            update={"posts_count": user["posts_count"] + 1},
        )
        logger.user.data_created(
            username=current_user.username,
            data_info=f"post {post_uid}",
            request=request,
        )
        flash("New post published successfully!", category="success")

    # query through posts
    # 20 posts for each page
    POSTS_EACH_PAGE = 20
    pagination = Pagination(current_user.username, current_page, POSTS_EACH_PAGE)

    posts = db_posts.find_posts_with_pagination(
        username=current_user.username,
        page_number=current_page,
        posts_per_page=POSTS_EACH_PAGE,
    )
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["clicks"] = redis_method.get_count(f"post_uid_{post['post_uid']}")
        post["clicks"] = format(post["clicks"], ",")
        post["comments"] = db_comments.comment.count_documents(
            {"post_uid": post["post_uid"]}
        )
        post["comments"] = format(post["comments"], ",")

    logger.log_for_pagination(
        username=current_user.username, num_of_posts_showing=len(posts), request=request
    )

    ###################################################################

    # return page content

    ###################################################################

    return render_template("posts.html", user=user, posts=posts, pagination=pagination)


@backstage.route("/about", methods=["GET"])
@login_required
def about_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "about"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="about control", request=request
    )

    user_info = db_users.info.find_one({"username": current_user.username})
    user_about = db_users.about.find_one({"username": current_user.username})
    user = {**user_info, **user_about}

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit_about.html", user=user)


@backstage.route("/about", methods=["POST"])
@login_required
def sending_updated_about():

    ###################################################################

    # main actions

    ###################################################################

    user_info = db_users.info.find_one({"username": current_user.username})
    user_about = db_users.about.find_one({"username": current_user.username})
    user = user_info | user_about

    form = request.form.to_dict()
    updated_info = {
        "profile_img_url": form["profile_img_url"],
        "short_bio": form["short_bio"],
    }
    updated_about = {"about": form["about"]}
    db_users.info.simple_update(
        filter={"username": user["username"]}, update=updated_info
    )
    db_users.about.simple_update(
        filter={"username": user["username"]}, update={"$set": updated_about}
    )
    user.update(updated_info)
    user.update(updated_about)
    logger.user.data_updated(
        username=current_user.username, data_info="about", request=request
    )
    flash("Information updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit_about.html", user=user)


@backstage.route("/archive", methods=["GET"])
@login_required
def archive_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "archive"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="archive control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": current_user.username})
    posts = db_posts.find_all_archived_posts_info(current_user.username)
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["clicks"] = redis_method.get_count(f"post_uid_{post['post_uid']}")
        post["clicks"] = format(post["clicks"], ",")
        post["comments"] = format(post["comments"], ",")

    logger.log_for_pagination(
        username=current_user.username, num_of_posts_showing=len(posts), request=request
    )

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("archive.html", user=user, posts=posts)


@backstage.route("/social-links", methods=["GET"])
@login_required
def social_link_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "social_link"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="social link control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": current_user.username})
    social_links = user["social_links"]

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social_links.html", social_links=social_links, user=user)


@backstage.route("/social-links", methods=["POST"])
@login_required
def sending_updated_social_links():

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": current_user.username})
    updated_links = []
    form = request.form.to_dict()
    form_values = list(form.values())

    for i in range(0, len(form_values), 2):
        updated_links.append({"platform": form_values[i + 1], "url": form_values[i]})

    db_users.info.simple_update(
        filter={"username": current_user.username},
        update={"social_links": updated_links},
    )
    logger.user.data_updated(
        username=current_user.username, data_info="social links", request=request
    )
    flash("Social Links updated", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social_links.html", social_links=updated_links, user=user)


@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "theme"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="theme", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("theme.html", user=user)


@backstage.route("/settings", methods=["GET"])
@login_required
def settings():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "settings"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="settings", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/settings", methods=["POST"])
@login_required
def sending_updated_settings():

    ###################################################################

    # main actions

    ###################################################################

    general = request.form.get("general")
    change_pw = request.form.get("changepw")
    delete_account = request.form.get("delete-account")

    if general is not None:

        banner_url = request.form.get("banner_url")
        blogname = request.form.get("blogname")
        enable_change_log = switch_to_bool(request.form.get("enable_change_log"))
        enable_portfolio = switch_to_bool(request.form.get("enable_portfolio"))

        db_users.info.simple_update(
            filter={"username": current_user.username},
            update={
                "banner_url": banner_url, 
                "blogname": blogname, 
                "change_log_enabled": enable_change_log,
                "portfolio_enabled": enable_portfolio
            },
        )
        logger.user.data_updated(
            username=current_user.username,
            data_info="general settings",
            request=request,
        )
        flash("Update succeeded!", category="success")

    elif change_pw is not None:

        current_pw_input = request.form.get("current")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        new_pw = request.form.get("new")

        user_creds = db_users.login.find_one({"username": current_user.username})
        user = db_users.info.find_one({"username": current_user.username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        # check pw
        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            logger.invalid_procedure(
                username=current_user.username,
                procedure="update password (invalid old password)",
                request=request,
            )
            flash("Current password is invalid. Please try again.", category="error")
            return render_template("settings.html", user=user)

        # update new password
        hashed_new_pw = hashpw(new_pw.encode("utf-8"), gensalt(12)).decode("utf-8")
        db_users.login.simple_update(
            filter={"username": current_user.username},
            update={"password": hashed_new_pw},
        )
        logger.user.data_updated(
            username=current_user.username, data_info="password", request=request
        )
        flash("Password update succeeded!", category="success")

    elif delete_account is not None:

        current_pw_input = request.form.get("delete-confirm-pw")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        username = current_user.username
        user = db_users.info.find_one({"username": username})
        user_creds = db_users.login.find_one({"username": username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            logger.invalid_procedure(
                username=current_user.username,
                procedure="delete account (invalid password)",
                request=request,
            )
            flash("Access denied, bacause password is invalid.", category="error")
            return render_template("settings.html", user=user)

        # deletion procedure
        logout_user()
        logger.user.logout(username=username, request=request)
        delete_user(username)
        flash("Account deleted successfully!", category="success")
        logger.user.deleted(username=username, request=request)
        return redirect(url_for("blog.register"))

    user = db_users.info.find_one({"username": current_user.username})

    ###################################################################

    # return page content

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/posts/edit/<post_uid>", methods=["GET"])
@login_required
def edit_post(post_uid):

    ###################################################################

    # status control / early returns

    ###################################################################

    if session["user_current_tab"] != "posts":
        logger.invalid_procedure(
            username=current_user.username,
            procedure=f"edit post {post_uid}",
            request=request,
        )
        flash("Access Denied!", category="error")
        return redirect(url_for("backstage.post_control"))

    session["user_current_tab"] = "editing_post"
    logger.log_for_backstage_tab(
        username=current_user.username, tab="edit post", request=request
    )
    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find({"username": current_user.username})
    target_post = db_posts.get_full_post(post_uid)
    target_post["tags"] = ", ".join(target_post["tags"])

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit_blogpost.html", post=target_post, user=user)


@backstage.route("/posts/edit/<post_uid>", methods=["POST"])
@login_required
def sending_edited_post(post_uid):

    ###################################################################

    # main actions

    ###################################################################

    update_post(post_uid, request)
    logger.user.data_updated(
        username=current_user.username, data_info=f"post {post_uid}", request=request
    )
    flash(f"Post {post_uid} update succeeded!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.post_control"))


@backstage.route("/edit-featured", methods=["GET"])
@login_required
def edit_featured():

    ###################################################################

    # status control / early returns

    ###################################################################

    post_uid = request.args.get("uid")
    if session["user_current_tab"] != "posts":
        logger.invalid_procedure(
            username=current_user.username,
            procedure=f"change featured status for post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.post_control"))

    ###################################################################

    # main actions

    ###################################################################

    if request.args.get("featured") == "to_true":
        updated_featured_status = True
        flash(f"Post {post_uid} is now featured on the home page!", category="success")

    else:
        updated_featured_status = False
        flash(f"Post {post_uid} is now removed from the home page!", category="success")

    db_posts.info.simple_update(
        filter={"post_uid": post_uid},
        update={"featured": updated_featured_status},
    )
    logger.user.data_updated(
        username=current_user.username,
        data_info=f"featured status for post {post_uid} (now set to {updated_featured_status})",
        request=request,
    )

    ###################################################################

    # return page content

    ###################################################################

    return redirect(url_for("backstage.post_control"))


@backstage.route("/edit-archived", methods=["GET"])
@login_required
def edit_archived():

    ###################################################################

    # status control / early returns

    ###################################################################

    post_uid = request.args.get("uid")
    if session["user_current_tab"] not in ["posts", "archive"]:
        logger.invalid_procedure(
            username=current_user.username,
            procedure=f"change archived status for post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    if request.args.get("archived") == "to_true":
        updated_archived_status = True
        flash(f"Post {post_uid} is now archived!", category="success")

    else:
        updated_archived_status = False
        flash(f"Post {post_uid} is now restored from the archive!", category="success")

    db_posts.info.simple_update(
        filter={"post_uid": post_uid},
        update={"archived": updated_archived_status},
    )
    logger.user.data_updated(
        username=current_user.username,
        data_info=f"archived status for post {post_uid} (now set to {updated_archived_status})",
        request=request,
    )

    ###################################################################

    # return page contents

    ###################################################################

    if session["user_current_tab"] == "posts":
        return redirect(url_for("backstage.post_control"))

    elif session["user_current_tab"] == "archive":
        return redirect(url_for("backstage.archive_control"))


@backstage.route("/delete/post", methods=["GET"])
@login_required
def delete_post():

    ###################################################################

    # status control / early returns

    ###################################################################

    post_uid = request.args.get("uid")

    if session["user_current_tab"] != "archive":
        logger.invalid_procedure(
            username=current_user.username,
            procedure=f"deleting post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    db_posts.info.delete_one({"post_uid": post_uid})
    db_posts.content.delete_one({"post_uid": post_uid})
    logger.user.data_updated(
        username=current_user.username, data_info=f"post {post_uid}", request=request
    )
    flash(f"Post {post_uid} has been deleted!", category="success")

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage.archive_control"))


@backstage.route("/logout", methods=["GET"])
@login_required
def logout():

    ###################################################################

    # main actions

    ###################################################################

    username = current_user.username
    logout_user()
    logger.user.logout(username=username, request=request)

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("blog.home", username=username))
