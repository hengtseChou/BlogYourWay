from typing import Dict
from urllib.parse import urlparse

import bcrypt
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from app.config import TEMPLATE_FOLDER
from app.forms.users import LoginForm, SignUpForm
from app.helpers.posts import post_utils
from app.helpers.projects import projects_utils
from app.helpers.users import user_utils
from app.logging import logger, logger_utils
from app.mongo import mongodb

main = Blueprint("main", __name__, template_folder=TEMPLATE_FOLDER)


def flashing_if_errors(form_errors: Dict[str, list[str]]) -> None:
    """Flash error messages if form validation errors exist.

    Args:
        form_errors (Dict[str, list[str]]): Pass in a form.errors from a wtform class.
    """
    if form_errors:
        for field, errors in form_errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", category="error")


@main.route("/", methods=["GET"])
def landing_page() -> str:
    """Render the landing page.

    Returns:
        str: Rendered HTML of the landing page.
    """
    logger_utils.page_visited(request)
    return render_template("main/landing-page.html")


@main.route("/login", methods=["GET", "POST"])
def login() -> str:
    """Handle user login.

    Handles both GET and POST requests. If the user is already authenticated, redirects to the home page.
    On POST request, validates login form, checks credentials, and logs in the user.

    Returns:
        str: Rendered HTML of the login page or redirect to the home page on success.
    """
    if current_user.is_authenticated:
        flash("You are already logged in.")
        logger.debug(f"Attempt to duplicate logging from user {current_user.username}.")
        return redirect(url_for("frontstage.home", username=current_user.username))

    form = LoginForm()

    if form.validate_on_submit():
        if not mongodb.user_creds.exists("email", form.email.data):
            flash("Account not found. Please try again.", category="error")
            logger_utils.login_failed(request=request, msg=f"email {form.email.data} not found")
            return render_template("main/login.html", form=form)

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
        return redirect(url_for("backstage.root"))

    flashing_if_errors(form.errors)
    logger_utils.page_visited(request)
    return render_template("main/login.html", form=form)


@main.route("/signup", methods=["GET", "POST"])
def signup() -> str:
    """Handle user sign-up.

    Handles both GET and POST requests. On POST request, validates sign-up form and creates a new user.

    Returns:
        str: Rendered HTML of the sign-up page or redirect to the login page on success.
    """
    logger_utils.page_visited(request)
    form = SignUpForm()

    if form.validate_on_submit():
        user_utils.create_user(form)
        flash("Sign up succeeded.", category="success")
        return redirect(url_for("main.login"))

    flashing_if_errors(form.errors)
    return render_template("main/signup.html", form=form)


@main.route("/raise-exception", methods=["GET"])
def error_simulator() -> None:
    """Simulate an error by raising an exception.

    Raises:
        Exception: Always raised to simulate an error.
    """
    raise Exception("this is a simulation error.")


@main.route("/error", methods=["GET"])
def error_page() -> str:
    """Render the error page.

    Returns:
        str: Rendered HTML of the error page.
    """
    return render_template("main/500.html")


@main.route("/robots.txt", methods=["GET"])
def robotstxt() -> str:
    """Serve the robots.txt file.

    Returns:
        str: Content of the robots.txt file.
    """
    return open("robots.txt", "r").read()


@main.route("/sitemap")
@main.route("/sitemap/")
@main.route("/sitemap.xml")
def sitemap() -> str:
    """Generate and serve a sitemap of the website/application.

    Returns:
        str: XML content of the sitemap.
    """
    host_components = urlparse(request.host_url)
    host_base = f"{host_components.scheme}://{host_components.netloc}"

    # Static routes
    static_urls = [{"loc": f"{host_base}{route}"} for route in ["/", "/login", "/register"]]

    # Dynamic routes
    dynamic_urls = []
    for username in user_utils.get_all_username():
        dynamic_urls.extend(
            [
                {"loc": f"{host_base}/@{username}"},
                {"loc": f"{host_base}/@{username}/blog"},
                {"loc": f"{host_base}/@{username}/about"},
            ]
        )
    for username in user_utils.get_all_username_gallery_enabled():
        dynamic_urls.append({"loc": f"{host_base}/@{username}/gallery"})
    for username in user_utils.get_all_username_changelog_enabled():
        dynamic_urls.append({"loc": f"{host_base}/@{username}/changelog"})

    for post in post_utils.get_all_posts_info():
        slug = post.get("custom_slug")
        url = {
            "loc": f"{host_base}/@{post.get('author')}/posts/{post.get('post_uid')}/{slug if slug else ''}",
            "lastmod": post.get("last_updated"),
        }
        dynamic_urls.append(url)

    for project in projects_utils.get_all_projects_info():
        slug = project.get("custom_slug")
        url = {
            "loc": f"{host_base}/@{project.get('author')}/projects/{project.get('project_uid')}/{slug if slug else ''}",
            "lastmod": project.get("last_updated"),
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
