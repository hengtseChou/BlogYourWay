from urllib.parse import urlparse

import bcrypt
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from blogyourway.config import TEMPLATE_FOLDER
from blogyourway.forms.users import LoginForm, SignUpForm
from blogyourway.logging import logger, logger_utils
from blogyourway.mongo import mongodb
from blogyourway.tasks.posts import post_utils
from blogyourway.tasks.users import user_utils

main = Blueprint("main", __name__, template_folder=TEMPLATE_FOLDER)


@main.route("/", methods=["GET"])
def landing_page():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("main/landing-page.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    ###################################################################

    # early returns

    ###################################################################

    if current_user.is_authenticated:
        flash("You are already logged in.")
        logger.debug(f"Attempt to duplicate logging from user {current_user.username}.")
        return redirect(url_for("frontstage.home", username=current_user.username))

    ###################################################################

    # main actions

    ###################################################################

    form = LoginForm()

    if form.validate_on_submit():

        if not mongodb.user_creds.exists("email", form.email.data):
            flash("Account not found. Please try again.", category="error")
            logger_utils.login_failed(request=request, msg=f"email {form.email.data} not found")
            return render_template("main/login.html", form=form)

        # check pw
        user_creds = mongodb.user_creds.find_one({"email": form.email.data})
        encoded_input_pw = form.password.data.encode("utf8")
        encoded_valid_user_pw = user_creds.get("password").encode("utf8")

        if not bcrypt.checkpw(encoded_input_pw, encoded_valid_user_pw):
            flash("Invalid password. Please try again.", category="error")
            logger_utils.login_failed(
                request=request,
                msg=f"invalid password with email {form.email.data}",
            )
            return render_template("main/login.html", form=form)

        username = user_creds.get("username")
        user_info = user_utils.get_user_info(username)
        login_user(user_info)
        logger_utils.login_succeeded(request=request, username=username)
        flash("Login Succeeded.", category="success")
        return redirect(url_for("frontstage.home", username=username))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", category="error")
        return render_template("main/login.html", form=form)

    logger_utils.page_visited(request)
    return render_template("main/login.html", form=form)


@main.route("/signup", methods=["GET", "POST"])
def signup():
    ###################################################################

    # logging / metrics

    ###################################################################

    logger_utils.page_visited(request)
    form = SignUpForm()

    if form.validate_on_submit():
        user_utils.create_user(form)
        flash("Sign up succeeded.", category="success")
        return redirect(url_for("main.login"))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", category="error")
        return render_template("main/signup.html", form=form)

    ###################################################################

    # return page content

    ###################################################################

    return render_template("main/signup.html", form=form)


@main.route("/raise-exception", methods=["GET"])
def error_simulator():
    raise Exception("this is a simulation error.")


@main.route("/error", methods=["GET"])
def error_page():
    return render_template("main/500.html")


@main.route("/robots.txt", methods=["GET"])
def robotstxt():
    return open("robots.txt", "r")


@main.route("/sitemap")
@main.route("/sitemap/")
@main.route("/sitemap.xml")
def sitemap():
    """
    Route to dynamically generate a sitemap of your website/application.
    lastmod and priority tags omitted on static pages.
    lastmod included on dynamic content such as blog posts.
    """

    host_components = urlparse(request.host_url)
    host_base = host_components.scheme + "://" + host_components.netloc

    # Static routes with static content
    static_urls = []
    for route in ["/", "/login", "/register"]:
        static_urls.append({"loc": f"{host_base}{route}"})

    # Dynamic routes with dynamic content
    dynamic_urls = []
    for username in user_utils.get_all_username():
        dynamic_urls.append({"loc": f"{host_base}/@{username}"})
        dynamic_urls.append({"loc": f"{host_base}/@{username}/blog"})
        dynamic_urls.append({"loc": f"{host_base}/@{username}/about"})
    for post in post_utils.get_all_posts_info():
        slug = post.get("slug")
        if slug:
            url = {
                "loc": f"{host_base}/@{post.get('author')}/posts/{post.get('post_uid')}/{slug}",
                "lastmod": post.get("last_updated"),
            }
        else:
            url = {
                "loc": f"{host_base}/@{post.get('author')}/posts/{post.get('post_uid')}",
                "lastmod": post.get("last_updated"),
            }
        dynamic_urls.append(url)

    xml_sitemap = render_template(
        "main/sitemap.xml",
        static_urls=static_urls,
        dynamic_urls=dynamic_urls,
        host_base=host_base,
    )
    response = make_response(xml_sitemap)
    response.headers["Content-Type"] = "application/xml"
    logger.debug("Sitemap generated successfully.")

    return response
