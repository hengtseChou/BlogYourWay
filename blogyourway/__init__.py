"""
Configure little-blog application in create_app() with a factory pattern.
"""

from flask import Flask, render_template, request
from flask_login import LoginManager
from pymongo.errors import ServerSelectionTimeoutError

from blogyourway.config import APP_SECRET, ENV
from blogyourway.helpers.users import UserInfo, user_utils
from blogyourway.services.logging import logger, return_client_ip
from blogyourway.services.mongo import mongodb
from blogyourway.services.sitemapper import sitemapper

from .views import backstage_bp, frontstage_bp


def create_app() -> Flask:
    """
    Defines:
    - secret key of application
    - login manager (login view, login message)
    - user loader
    - 404 error handler page
    - 500 error handler page
    - register blueprints (blog, backstage)
    - cache
    - socketio
    - server-side session
    - check connections for redis and mongo
    """

    app = Flask(__name__)
    logger.info("App initialization started.")
    app.secret_key = APP_SECRET

    # debug mode
    if ENV == "debug":
        app.config["DEBUG"] = True
        from flask_debugtoolbar import DebugToolbarExtension

        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        logger.debug("Debugtoolbar initialized.")

    ## login
    login_manager = LoginManager()
    login_manager.login_view = "blog.login_get"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)
    logger.debug("Login manager initialized.")

    @login_manager.user_loader
    def user_loader(username: str) -> UserInfo:
        """register user loader for current_user to access"""
        user_info = user_utils.get_user_info(username)
        # return none if the ID is not valid
        return user_info

    # Register the custom error page
    @app.errorhandler(404)
    def page_not_found(error):
        client_ip = return_client_ip(request, ENV)
        logger.debug(f"{client_ip} - 404 not found at {request.environ['RAW_URI']}. ")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        client_ip = return_client_ip(request, ENV)
        logger.error(f"{client_ip} - 500 internal error at {request.environ['RAW_URI']}.")
        # flask app itself will show the error occurred
        return render_template("500.html"), 500

    logger.debug("Error handlers registered.")

    # blueprints
    app.register_blueprint(frontstage_bp, url_prefix="/")
    app.register_blueprint(backstage_bp, url_prefix="/backstage/")
    logger.debug("Blueprints registered.")

    # sitemapper
    sitemapper.init_app(app)
    app.config["SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS"] = True
    app.config["SITEMAP_URL_SCHEME"] = "https"
    app.config["SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS"] = True
    logger.debug("Flask-sitemapper initialized.")

    # check connection
    try:
        mongodb.client.server_info()
        logger.debug("MongoDB connected.")
    except ServerSelectionTimeoutError as error:
        logger.error(error)
        exit("MongoDB is NOT connected. App initializaion failed.")

    logger.info("App initialization completed.")

    return app
