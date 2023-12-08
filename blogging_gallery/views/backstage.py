from bcrypt import checkpw, gensalt, hashpw
from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from blogging_gallery.services.log import my_logger
from blogging_gallery.services.mongo import my_database
from blogging_gallery.utils.common import string_truncate, switch_to_bool
from blogging_gallery.utils.posts import create_post, paging, post_utils, update_post
from blogging_gallery.utils.users import delete_user
from blogging_gallery.utils.dashboard import CollectMetricData

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


@backstage.route("/", methods=["GET"])
@login_required
def backstage_root():
    return redirect(url_for("backstage.overview"))


@backstage.route("/overview", methods=["GET"])
@login_required
def overview():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "overview"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="overview", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})
    user["created_at"] = user["created_at"].strftime("%b %d, %Y")

    data_collector = CollectMetricData(
        username=current_user.username,
        start_time=datetime.now() - timedelta(days=30),
        end_time=datetime.now()
    )


    pv = data_collector.total_pv()
    uv = data_collector.total_uv()
    site_traffic = data_collector.site_traffic()
    index_page_traffic = data_collector.index_pages_traffic()

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "overview.html",
        user=user,
        traffic=site_traffic,
        index_page_traffic=index_page_traffic,
        total_pv=pv,
        total_uv=uv
    )


@backstage.route("/posts", methods=["GET", "POST"])
@login_required
def post_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "posts"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="posts control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    current_page = request.args.get("page", default=1, type=int)
    user = my_database.user_info.find_one({"username": current_user.username})

    if request.method == "POST":
        # logging for this is inside the create post function
        post_uid = create_post(request)
        my_logger.user.data_created(
            username=current_user.username, data_info=f"post {post_uid}", request=request
        )
        flash("New post published successfully!", category="success")

    # query through posts
    # 20 posts for each page
    POSTS_EACH_PAGE = 20
    pagination = paging.setup(current_user.username, current_page, POSTS_EACH_PAGE)
    posts = post_utils.find_posts_with_pagination(
        username=current_user.username,
        page_number=current_page,
        posts_per_page=POSTS_EACH_PAGE,
    )
    for post in posts:
        post["title"] = string_truncate(post["title"], 30)
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post["views"], ",")
        comment_count = my_database.comment.count_documents({"post_uid": post["post_uid"]})
        post["comments"] = format(comment_count, ",")

    my_logger.log_for_pagination(
        username=current_user.username, num_of_posts=len(posts), request=request
    )

    ###################################################################

    # return page content

    ###################################################################

    return render_template("posts.html", user=user, posts=posts, pagination=pagination)


@backstage.route("/posts/edit/<post_uid>", methods=["GET"])
@login_required
def edit_post_get(post_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    if session["user_current_tab"] != "posts":
        my_logger.invalid_procedure(
            username=current_user.username,
            procedure=f"edit post {post_uid}",
            request=request,
        )
        flash("Access Denied!", category="error")
        return redirect(url_for("backstage.post_control"))

    session["user_current_tab"] = "editing_post"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="edit post", request=request
    )
    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find({"username": current_user.username})
    target_post = post_utils.get_full_post(post_uid)
    target_post["tags"] = ", ".join(target_post["tags"])

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit_blogpost.html", post=target_post, user=user)


@backstage.route("/posts/edit/<post_uid>", methods=["POST"])
@login_required
def edit_post_post(post_uid):
    ###################################################################

    # main actions

    ###################################################################

    update_post(post_uid, request)
    my_logger.user.data_updated(
        username=current_user.username, data_info=f"post {post_uid}", request=request
    )
    truncated_post_title = string_truncate(
        my_database.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    flash(f'Your post "{truncated_post_title}" has been updated!', category="success")

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
        my_logger.invalid_procedure(
            username=current_user.username,
            procedure=f"change featured status for post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.post_control"))

    ###################################################################

    # main actions

    ###################################################################

    truncated_post_title = string_truncate(
        my_database.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
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

    my_database.post_info.update_values(
        filter={"post_uid": post_uid}, update={"featured": updated_featured_status}
    )
    my_logger.user.data_updated(
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
        my_logger.invalid_procedure(
            username=current_user.username,
            procedure=f"change archived status for post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    truncated_post_title = string_truncate(
        my_database.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    if request.args.get("archived") == "to_true":
        updated_archived_status = True
        flash(f'Your post "{truncated_post_title}" is now archived!', category="success")
    else:
        updated_archived_status = False
        flash(
            f'Your post "{truncated_post_title}" is now restored from the archive!',
            category="success",
        )

    my_database.post_info.update_values(
        filter={"post_uid": post_uid}, update={"archived": updated_archived_status}
    )
    my_logger.user.data_updated(
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


@backstage.route("/about", methods=["GET"])
@login_required
def about_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "about"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="about control", request=request
    )

    user_info = my_database.user_info.find_one({"username": current_user.username})
    user_about = my_database.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit_about.html", user=user)


@backstage.route("/about", methods=["POST"])
@login_required
def about_control_post():
    ###################################################################

    # main actions

    ###################################################################

    user_info = my_database.user_info.find_one({"username": current_user.username})
    user_about = my_database.user_about.find_one({"username": current_user.username})
    user = user_info | user_about

    form = request.form.to_dict()
    updated_info = {
        "profile_img_url": form["profile_img_url"],
        "short_bio": form["short_bio"],
    }
    updated_about = {"about": form["about"]}
    my_database.user_info.update_values(
        filter={"username": user["username"]}, update=updated_info
    )
    my_database.user_about.update_values(
        filter={"username": user["username"]}, update=updated_about
    )
    user.update(updated_info)
    user.update(updated_about)
    my_logger.user.data_updated(
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
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="archive control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})
    posts = post_utils.find_all_archived_posts_info(current_user.username)
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["views"] = format(post["views"], ",")
        comment_count = my_database.comment.count_documents({"post_uid": post["post_uid"]})
        post["comments"] = format(comment_count, ",")

    my_logger.log_for_pagination(
        username=current_user.username, num_of_posts=len(posts), request=request
    )

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

    if session["user_current_tab"] != "archive":
        my_logger.invalid_procedure(
            username=current_user.username,
            procedure=f"deleting post {post_uid}",
            request=request,
        )
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    truncated_post_title = string_truncate(
        my_database.post_info.find_one({"post_uid": post_uid}).get("title"), max_len=20
    )
    my_database.post_info.delete_one({"post_uid": post_uid})
    my_database.post_content.delete_one({"post_uid": post_uid})
    my_logger.user.data_deleted(
        username=current_user.username, data_info=f"post {post_uid}", request=request
    )
    flash(f'Your post "{truncated_post_title}" has been deleted!', category="success")

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage.archive_control"))


@backstage.route("/social-links", methods=["GET"])
@login_required
def social_links_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "social_link"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="social link control", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})
    social_links = user["social_links"]

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social_links.html", social_links=social_links, user=user)


@backstage.route("/social-links", methods=["POST"])
@login_required
def social_links_control_post():
    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})
    form = request.form.to_dict()
    form_values = list(form.values())

    updated_links = []
    for i in range(0, len(form_values), 2):
        updated_links.append({"platform": form_values[i + 1], "url": form_values[i]})
    my_database.user_info.update_values(
        filter={"username": current_user.username}, update={"social_links": updated_links}
    )
    my_logger.user.data_updated(
        username=current_user.username, data_info="social links", request=request
    )
    flash("Social Links updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template("social_links.html", social_links=updated_links, user=user)


@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "theme"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="theme", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("theme.html", user=user)


@backstage.route("/settings", methods=["GET"])
@login_required
def settings_control_get():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "settings"
    my_logger.log_for_backstage_tab(
        username=current_user.username, tab="settings", request=request
    )

    ###################################################################

    # main actions

    ###################################################################

    user = my_database.user_info.find_one({"username": current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("settings.html", user=user)


@backstage.route("/settings", methods=["POST"])
@login_required
def settings_control_post():
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

        my_database.user_info.update_values(
            filter={"username": current_user.username},
            update={
                "banner_url": banner_url,
                "blogname": blogname,
                "change_log_enabled": enable_change_log,
                "portfolio_enabled": enable_portfolio,
            },
        )
        my_logger.user.data_updated(
            username=current_user.username, data_info="general settings", request=request
        )
        flash("Update succeeded!", category="success")

    elif change_pw is not None:
        current_pw_input = request.form.get("current")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        new_pw = request.form.get("new")

        user_creds = my_database.user_login.find_one({"username": current_user.username})
        user = my_database.user_info.find_one({"username": current_user.username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        # check pw
        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            my_logger.invalid_procedure(
                username=current_user.username,
                procedure="update password (invalid old password)",
                request=request,
            )
            flash("Current password is invalid. Please try again.", category="error")
            return render_template("settings.html", user=user)

        # update new password
        hashed_new_pw = hashpw(new_pw.encode("utf-8"), gensalt(12)).decode("utf-8")
        my_database.user_login.update_values(
            filter={"username": current_user.username}, update={"password": hashed_new_pw}
        )
        my_logger.user.data_updated(
            username=current_user.username, data_info="password", request=request
        )
        flash("Password update succeeded!", category="success")

    elif delete_account is not None:
        current_pw_input = request.form.get("delete-confirm-pw")
        encoded_current_pw_input = current_pw_input.encode("utf8")
        username = current_user.username
        user = my_database.user_info.find_one({"username": username})
        user_creds = my_database.user_login.find_one({"username": username})
        encoded_valid_user_pw = user_creds["password"].encode("utf8")

        if not checkpw(encoded_current_pw_input, encoded_valid_user_pw):
            my_logger.invalid_procedure(
                username=current_user.username,
                procedure="delete account (invalid password)",
                request=request,
            )
            flash("Access denied, bacause password is invalid.", category="error")
            return render_template("settings.html", user=user)

        # deletion procedure
        logout_user()
        my_logger.user.logout(username=username, request=request)
        delete_user(username)
        flash("Account deleted successfully!", category="success")
        my_logger.user.user_deleted(username=username, request=request)
        return redirect(url_for("blog.register_get"))

    user = my_database.user_info.find_one({"username": current_user.username})

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
    session.pop("user_current_tab", None)
    my_logger.user.logout(username=username, request=request)

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("blog.home", username=username))
