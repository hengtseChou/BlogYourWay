import bcrypt
from datetime import datetime
from flask import (
    Blueprint, request, session, render_template, flash, redirect, url_for
)
from flask_login import login_required, logout_user, current_user
from website.extensions.mongo import db_users, db_posts
from website.extensions.redis import redis_method
from website.extensions.log import logger
from website.blog.utils import set_up_pagination
from website.backstage.utils import create_post, update_post, delete_user

backstage = Blueprint("backstage", __name__, template_folder="../templates/backstage/")


@backstage.route("/overview", methods=["GET"])
@login_required
def overview():

    ###################################################################

    # status control / early returns

    ###################################################################

    session['user_status'] = 'overview'
    logger.debug(f'User {current_user.username} is now at the overview tab.')

    ###################################################################

    # main actions

    ###################################################################

    logger.debug(f'Retrieving stats for user {current_user.username} started.')

    now = datetime.now()
    user = db_users.info.find_one({"username": current_user.username})

    time_difference = now - user["created_at"]
    user['days_joined'] = format(time_difference.days + 1, ",")

    visitor_stats = redis_method.get_visitor_stats(current_user.username)
    daily_count = redis_method.get_daily_visitor_data(current_user.username)

    logger.debug(f'Retrieving stats for user {current_user.username} completed.')

    ###################################################################

    # return page content

    ###################################################################    

    return render_template("overview.html", 
                           user=user,
                           daily_count=daily_count, 
                           visitor_stats=visitor_stats)


@backstage.route("/posts", methods=["GET", "POST"])
@login_required
def post_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_status"] = "posts"
    logger.debug(f'User {current_user.username} is now at the posts control tab.')

    ###################################################################

    # main actions

    ###################################################################

    page = request.args.get("page", default=1, type=int)
    user = db_users.info.find_one({"username": current_user.username})

    if request.method == "POST":
        
        # logging for this is inside the create post function
        create_post(request)
        db_users.info.update_one(
            filter={"username": current_user.username},
            update={"$set": {"posts_count": user["posts_count"] + 1}},
        )
        flash("New post published successfully!", category="success")

    # query through posts
    # 20 posts for each page
    POSTS_EACH_PAGE = 20
    pagination = set_up_pagination(current_user.username, page, POSTS_EACH_PAGE)
    enable_newer_post = pagination['enable_newer_post']
    enable_older_post = pagination['enable_older_post']

    if page == 1:
        posts = list(
            db_posts.info
            .find({"author": current_user.username, "archived": False})
            .sort("created_at", -1)
            .limit(POSTS_EACH_PAGE)
        )  # descending: newest
    elif page > 1:
        posts = list(
            db_posts.info
            .find({"author": current_user.username, "archived": False})
            .sort("created_at", -1)
            .skip((page - 1) * POSTS_EACH_PAGE)
            .limit(POSTS_EACH_PAGE)
        )

    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["clicks"] = redis_method.get_count(f"post_uid_{post['post_uid']}")
        post["clicks"] = format(post["clicks"], ",")
        post["comments"] = format(post["comments"], ",")

    logger.debug(f'Showing {len(posts)} posts for user {current_user.username} at page {page} from {request.remote_addr}.')

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "posts.html",
        user=user,
        posts=posts,
        current_page=page,
        newer_posts=enable_newer_post,
        older_posts=enable_older_post,
    )


@backstage.route("/about", methods=["GET", "POST"])
@login_required
def about_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_status"] = "about"
    logger.debug(f'User {current_user.username} is now at the about control tab.')
    
    user_info = dict(db_users.info.find_one({"username": current_user.username}))
    user_about = dict(db_users.about.find_one({"username": current_user.username}))
    user = {**user_info, **user_about}

    if request.method == 'GET':        
        logger.debug(f"Editing about for user {current_user.username} from {request.remote_addr}.")
        return render_template("edit_about.html", user=user)

    ###################################################################

    # main actions

    ###################################################################

    form = request.form.to_dict()
    updated_info = {
        'profile_img_url': form['profile_img_url'],
        'short_bio': form['short_bio']
    }
    updated_about = {
        "about": form["about"]
    }
    db_users.info.update_one(
        filter={"username": user["username"]}, update={"$set": updated_info}
    )
    db_users.about.update_one(
        filter={"username": user["username"]}, update={"$set": updated_about}
    )
    user.update(updated_info)
    user.update(updated_about)
    logger.info(f"About for {current_user.username} is updated from {request.remote_addr}.")
    flash("Information updated!", category="success")

    ###################################################################

    # return page content

    ###################################################################

    return render_template(
        "edit_about.html", 
        user=user
    )


@backstage.route("/archive", methods=["GET"])
@login_required
def archive_control():

    ###################################################################

    # status control / early returns

    ###################################################################

    session["user_status"] = "archive"
    logger.debug(f'User {current_user.username} is now at the archive control tab.')

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({'username': current_user.username})
    posts = list(
        db_posts.info
        .find({"author": current_user.username, "archived": True})
        .sort("created_at", -1)
    )
    for post in posts:
        post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        post["clicks"] = redis_method.get_count(f"post_uid_{post['post_uid']}")
        post["clicks"] = format(post["clicks"], ",")
        post["comments"] = format(post["comments"], ",")

    logger.debug(f'Showing {len(posts)} archived posts for user {current_user.username} from {request.remote_addr}.')    

    ###################################################################

    # return page contents

    ###################################################################

    return render_template(
        "archive.html", 
        user=user,
        posts=posts 
    )


@backstage.route("/social-links", methods=["GET", "POST"])
@login_required
def social_link_control():

    ###################################################################

    # status control / early returns

    ###################################################################   

    session['user_status'] = 'social_link'
    logger.debug(f'User {current_user.username} is now at the social links control tab.')
    
    user = db_users.info.find_one({"username": current_user.username})
    social_links = user["social_links"]

    if request.method == 'GET':        
        logger.debug(f'Editing social links for user {current_user.username} from {request.remote_addr}.')
        return render_template("social_links.html", social_links=social_links, user=user)

    ###################################################################

    # main actions

    ###################################################################

    updated_links = []
    form = request.form.to_dict()
    form_values = list(form.values())

    for i in range(0, len(form_values), 2):
        updated_links.append({"platform": form_values[i + 1], "url": form_values[i]})

    db_users.info.update_one(
        filter={"username": current_user.username},
        update={"$set": {"social_links": updated_links}},
    )
    logger.info(f'Social links for user {current_user.username} is updated from {request.remote_addr}.')
    flash("Social Links updated", category="success")
    
    ###################################################################

    # return page content

    ###################################################################  

    return render_template(
        "social_links.html", 
        social_links=updated_links, 
        user=user
    )

@backstage.route("/theme", methods=["GET", "POST"])
@login_required
def theme():

    ###################################################################

    # status control / early returns

    ###################################################################

    session['user_status'] = 'theme'
    logger.debug(f'User {current_user.username} is now at the theme control tab.')

    ###################################################################

    # main actions

    ###################################################################

    user = db_users.info.find_one({'username': current_user.username})

    ###################################################################

    # return page contents

    ###################################################################

    return render_template(
        "theme.html", 
        user=user
    )


@backstage.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    ###################################################################

    # status control / early returns

    ################################################################### 
    
    session["user_status"] = "settings"
    logger.debug(f'User {current_user.username} is now at the settings tab.')   

    if request.method == 'GET':          
        user = db_users.info.find_one({"username": current_user.username})
        logger.debug(f'Editing setting for user {current_user.username} from {request.remote_addr}.')
        return render_template("settings.html", user=user)

    ###################################################################

    # main actions

    ###################################################################

    general = request.form.get("general")
    change_pw = request.form.get("changepw")
    delete_account = request.form.get("delete-account")

    if general is not None:

        banner_url = request.form.get("banner_url")
        db_users.info.update_one(
            filter={"username": current_user.username},
            update={"$set": {"banner_url": banner_url}},
        )
        logger.info(f'General setting for user {current_user.username} is updated from {request.remote_addr}.')
        flash("Update succeeded!", category="success")

    elif change_pw is not None:

        current_pw = request.form.get("current")
        new_pw = request.form.get("new")

        user_creds = db_users.login.find_one({"username": current_user.username})
        user = db_users.info.find_one({"username": current_user.username})

        # check pw
        if not bcrypt.checkpw(current_pw.encode("utf8"), user_creds["password"].encode("utf8")):
            logger.debug(f'Invalid password while updating password for user {current_user.username} from {request.remote_addr}')
            flash("Current password is invalid. Please try again.", category="error")
            return render_template("settings.html", user=user)

        # update new password
        hashed_pw = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt(12))
        hashed_pw = hashed_pw.decode("utf-8")
        db_users.login.update_one(
            filter={"username": current_user.username},
            update={"$set": {"password": hashed_pw}},
        )
        logger.info(f'Password for user {current_user.username} is updated from {request.remote_addr}.')
        flash("Password update succeeded!", category="success")

    elif delete_account is not None:
        
        confirm_pw = request.form.get("delete-confirm-pw")
        username =  current_user.username    
        user_creds = db_users.login.find_one({"username": username})
        user = db_users.info.find_one({"username": username})

        if not bcrypt.checkpw(confirm_pw.encode("utf8"), user_creds["password"].encode("utf8")):
            logger.debug(f'Invalid password while deleting account for user {current_user.username} from {request.remote_addr}')
            flash("Access denied, bacause password is invalid.", category="error")
            return render_template("settings.html", user=user)

        # deletion procedure  
        logout_user()
        logger.info(f'User {username} has logged out from {request.remote_addr}.')
        delete_user(username)
        flash("Account deleted successfully!", category="success")
        logger.info(f'User {username} has been deleted from {request.remote_addr}.')
        return redirect(url_for("blog.register"))

    user = db_users.info.find_one({"username": current_user.username})

    ###################################################################

    # return page content

    ###################################################################    

    return render_template(
        "settings.html", 
        user=user
    )


@backstage.route("/posts/edit/<post_uid>", methods=["GET", "POST"])
@login_required
def edit_post(post_uid):

    ###################################################################

    # status control / early returns

    ###################################################################    

    if session["user_status"] != "posts":
        logger.debug(f'Invalid procedure to edit post {post_uid} by {current_user.username} from {request.remote_addr}.')
        flash("Access Denied!", category="error")
        return redirect(url_for("backstage.post_control"))
    
    session['user_status'] = 'editing_post'
    logger.debug(f'User {current_user.username} is now at the post editing tab.')

    if request.method == "GET":
        user = db_users.info.find({"username": current_user.username})
        target_post = db_posts.info.find_one({"post_uid": post_uid})
        target_post = dict(target_post)
        target_post["content"] = db_posts.content.find_one({"post_uid": post_uid})[
            "content"
        ]
        target_post["tags"] = ", ".join(target_post["tags"])
        logger.debug(f'Editing post {post_uid} by {current_user.username} from {request.remote_addr}.')

        return render_template("edit_blogpost.html", post=target_post, user=user)    

    ###################################################################

    # main actions

    ###################################################################

    update_post(post_uid, request)
    logger.debug(f'Post {post_uid} by {current_user.username} is updated from {request.remote_addr}.')
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

    if session["user_status"] != 'posts':
        logger.debug(f'Invalid procedure to change featured status for post {post_uid} by {current_user.username} from {request.remote_addr}.')
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.post_control"))

    ###################################################################

    # main actions

    ###################################################################

    if request.args.get("featured") == "to_true":
        updated_featured_status = True
    else:
        updated_featured_status = False

    db_posts.info.update_one(
        filter={"post_uid": post_uid},
        update={"$set": {"featured": updated_featured_status}},
    )
    logger.debug(f'Featured status for post {post_uid} by {current_user.username} is set to {updated_featured_status} from {request.remote_addr}.')

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

    if session['user_status'] not in ['posts', 'archive']:
        logger.debug(f'Invalid procedure to change archived status for post {post_uid} by {current_user.username} from {request.remote_addr}.')
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    if request.args.get("archived") == "to_true":
        updated_archived_status = True
    else:
        updated_archived_status = False

    post_uid = request.args.get("uid")
    db_posts.info.update_one(
        filter={"post_uid": post_uid},
        update={"$set": {"archived": updated_archived_status}},
    )
    logger.debug(f'Archived status for post {post_uid} by {current_user.username} is set to {updated_archived_status} from {request.remote_addr}.')

    ###################################################################

    # return page contents

    ###################################################################
    
    if session["user_status"] == "posts":        
        return redirect(url_for("backstage.post_control"))

    elif session["user_status"] == "archive":        
        return redirect(url_for("backstage.archive_control"))


@backstage.route("/delete", methods=["GET"])
@login_required
def delete():

    ###################################################################

    # status control / early returns

    ###################################################################

    if session["user_status"] != "archive":
        logger.debug(f'Invalid procedure to delete content for {current_user.username} from {request.remote_addr}.')
        flash("Access Denied. ", category="error")
        return redirect(url_for("backstage.archive_control"))

    ###################################################################

    # main actions

    ###################################################################

    target = request.args.get("type")

    if target == "post":

        post_uid = request.args.get("uid")        
        db_posts.info.delete_one({"post_uid": post_uid})
        db_posts.content.delete_one({"post_uid": post_uid})
        logger.info(f'Post {post_uid} by {current_user.username} has been deleted from {request.remote_addr}.')
        flash("Post deleted!", category="success")
        return redirect(url_for("backstage.archive_control"))
    
    elif target == "work":

        # delete work
        return redirect(url_for("backstage.archive_control"))

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
    logger.info(f'User {username} has logger out from {request.remote_addr}.')

    ###################################################################

    # return page contents

    ###################################################################

    return redirect(url_for("blog.home", username=username))
