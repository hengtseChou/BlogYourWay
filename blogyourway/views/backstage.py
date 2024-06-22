from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from blogyourway.helpers.articles import article_utils, create_article, paging, update_post
from blogyourway.helpers.common import string_truncate, switch_to_bool
from blogyourway.helpers.users import user_utils
from blogyourway.services.logging import logger, logger_utils
from blogyourway.services.mongo import mongodb

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


@backstage.route("/", methods=["GET"])
@login_required
def backstage_root():
    return redirect(url_for("backstage.post_control"))


@backstage.route("/articles", methods=["GET", "POST"])
@login_required
def post_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "articles"
    logger_utils.backstage(username=current_user.username, tab="articles")

    ###################################################################

    # main actions

    ###################################################################

    current_page = request.args.get("page", default=1, type=int)
    user = mongodb.user_info.find_one({"username": current_user.username})

    if request.method == "POST":
        # logging for this is inside the create post function
        article_uid = create_article(request)
        if article_uid is not None:
            logger.debug(f"post {article_uid} has been created.")
            flash("New post published successfully!", category="success")

    # query through articles
    # 20 articles for each page
    ARTICLES_EACH_PAGE = 20
    pagination = paging.setup(current_user.username, current_page, ARTICLES_EACH_PAGE)
    articles = article_utils.find_articles_with_pagination(
        username=current_user.username,
        page_number=current_page,
        articles_per_page=ARTICLES_EACH_PAGE,
    )
    for article in articles:
        article["title"] = string_truncate(article.get("title"), 30)
        article["created_at"] = article.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
        article["views"] = format(article.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"article_uid": article.get("article_uid")})
        article["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="articles", num_of_articles=len(articles))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("articles.html", user=user, articles=articles, pagination=pagination)


@backstage.route("/edit/articles/<article_uid>", methods=["GET"])
@login_required
def edit_post_get(article_uid):
    ###################################################################

    # status control / early returns

    ###################################################################

    logger_utils.backstage(username=current_user.username, tab="edit_post")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find({"username": current_user.username})
    target_article = article_utils.get_full_article(article_uid)
    target_article["tags"] = ", ".join(target_article.get("tags"))

    ###################################################################

    # return page content

    ###################################################################

    return render_template("edit-article.html", article=target_article, user=user)


@backstage.route("/edit/articles/<article_uid>", methods=["POST"])
@login_required
def edit_post_post(article_uid):
    ###################################################################

    # main actions

    ###################################################################

    update_post(article_uid, request)
    logger.debug(f"post {article_uid} is updated.")
    title_truncated = string_truncate(
        mongodb.article_info.find_one({"article_uid": article_uid}).get("title"), max_len=20
    )
    flash(f'Your article "{title_truncated}" has been updated!', category="success")

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

    ###################################################################

    # main actions

    ###################################################################

    article_uid = request.args.get("uid")
    truncated_post_title = string_truncate(
        mongodb.article_info.find_one({"article_uid": article_uid}).get("title"), max_len=20
    )

    if request.args.get("featured") == "to_true":
        updated_featured_status = True
        flash(
            f'Your article "{truncated_post_title}" is now featured on the home page!',
            category="success",
        )

    else:
        updated_featured_status = False
        flash(
            f'Your article "{truncated_post_title}" is now removed from the home page!',
            category="success",
        )

    mongodb.article_info.update_values(
        filter={"article_uid": article_uid}, update={"featured": updated_featured_status}
    )
    logger.debug(
        f"featuring status for article {article_uid} is now set to {updated_featured_status}"
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

    ###################################################################

    # main actions

    ###################################################################

    article_uid = request.args.get("uid")
    title_truncated = string_truncate(
        mongodb.article_info.find_one({"article_uid": article_uid}).get("title"), max_len=20
    )
    if request.args.get("archived") == "to_true":
        updated_archived_status = True
        flash(f'Your article "{title_truncated}" is now archived!', category="success")
    else:
        updated_archived_status = False
        flash(
            f'Your article "{title_truncated}" is now restored from the archive!',
            category="success",
        )

    mongodb.article_info.update_values(
        filter={"article_uid": article_uid}, update={"archived": updated_archived_status}
    )
    logger.debug(
        f"archive status for article {article_uid} is now set to {updated_archived_status}"
    )

    ###################################################################

    # return page contents

    ###################################################################

    if session["user_current_tab"] == "articles":
        return redirect(url_for("backstage.post_control"))

    elif session["user_current_tab"] == "archive":
        return redirect(url_for("backstage.archive_control"))


@backstage.route("/about", methods=["GET"])
@login_required
def about_control_get():
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
def about_control_post():
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
def archive_control():
    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_current_tab"] = "archive"
    logger_utils.backstage(username=current_user.username, tab="archive")

    ###################################################################

    # main actions

    ###################################################################

    user = mongodb.user_info.find_one({"username": current_user.username})
    articles = article_utils.find_all_archived_articles_info(current_user.username)
    for article in articles:
        article["created_at"] = article.get("created_at").strftime("%Y-%m-%d %H:%M:%S")
        article["views"] = format(article.get("views"), ",")
        comment_count = mongodb.comment.count_documents({"article_uid": article.get("article_uid")})
        article["comments"] = format(comment_count, ",")

    logger_utils.pagination(tab="archive", num_of_articles=len(articles))

    ###################################################################

    # return page contents

    ###################################################################

    return render_template("archive.html", user=user, articles=articles)


@backstage.route("/delete/article", methods=["GET"])
@login_required
def delete_post():
    ###################################################################

    # status control / early returns

    ###################################################################

    article_uid = request.args.get("uid")

    ###################################################################

    # main actions

    ###################################################################

    title_truncated = string_truncate(
        mongodb.article_info.find_one({"article_uid": article_uid}).get("title"), max_len=20
    )
    mongodb.article_info.delete_one({"article_uid": article_uid})
    mongodb.article_content.delete_one({"article_uid": article_uid})
    logger.debug(f"article {article_uid} has been deleted")
    flash(f'Your article "{title_truncated}" has been deleted!', category="success")

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("backstage.archive_control"))


@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme_control():
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
def settings_control_get():
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
def settings_control_post():
    ###################################################################

    # main actions

    ###################################################################

    general = request.form.get("general")
    change_pw = request.form.get("changepw")
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
        return redirect(url_for("blog.register_get"))

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
