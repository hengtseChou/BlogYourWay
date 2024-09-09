import time
from typing import Tuple

from flask import Flask, render_template, request
from flask_login import LoginManager
from pymongo.errors import ServerSelectionTimeoutError

from app.cache import cache
from app.config import APP_SECRET, CACHE_TIMEOUT, ENV, REDIS_URL, REDISHOST, REDISPORT
from app.helpers.users import user_utils
from app.logging import logger, return_client_ip
from app.models.users import UserInfo
from app.mongo import mongodb
from app.views import backstage_bp, frontstage_bp, main_bp


def create_app() -> Flask:
    """Create and configure the Flask application.

    This function sets up the application with the following:
    - Secret key for session management
    - In-memory caching configuration
    - Login manager for user authentication
    - Error handlers for 404 and 500 errors
    - Registration of blueprints
    - MongoDB connection check

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    logger.info("App initialization started.")
    app.secret_key = APP_SECRET

    # develop environment configuration
    if ENV == "dev":
        app.config["DEBUG"] = True

        from flask_debugtoolbar import DebugToolbarExtension

        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        logger.debug("Debugtoolbar initialized.")

    # Cache configuration
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_HOST"] = REDISHOST
    app.config["CACHE_REDIS_PORT"] = REDISPORT
    app.config["CACHE_REDIS_DB"] = 0
    app.config["CACHE_REDIS_URL"] = REDIS_URL
    app.config["CACHE_DEFAULT_TIMEOUT"] = CACHE_TIMEOUT
    cache.init_app(app)
    logger.debug(f"{app.config['CACHE_TYPE']} initialized.")

    # Login manager configuration
    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)
    logger.debug("Login manager initialized.")

    @login_manager.user_loader
    def user_loader(username: str) -> UserInfo:
        """Load a user by username from the cache or fetch from the database.

        Args:
            username (str): The username of the user to load.

        Returns:
            UserInfo: The user information object.
        """
        user = cache.get(username)
        if not user:
            user = user_utils.get_user_info(username)
            if user:
                logger.debug("Updating user cache from user loader.")
                cache.set(username, user, timeout=5 * 60)
        return user

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(error) -> Tuple[str, int]:
        """Handle 404 errors.

        Args:
            error: The error that caused the 404 response.

        Returns:
            Tuple[str, int]: The rendered template and HTTP status code.
        """
        client_ip = return_client_ip(request, ENV)
        logger.debug(f"{client_ip} - 404 not found at {request.environ['RAW_URI']}. ")
        return render_template("main/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error) -> Tuple[str, int]:
        """Handle 500 errors.

        Args:
            error: The error that caused the 500 response.

        Returns:
            Tuple[str, int]: The rendered template and HTTP status code.
        """
        client_ip = return_client_ip(request, ENV)
        logger.error(f"{client_ip} - 500 internal error at {request.environ['RAW_URI']}.")
        return render_template("main/500.html"), 500

    logger.debug("Error handlers registered.")

    # Register blueprints
    app.register_blueprint(frontstage_bp, url_prefix="/")
    app.register_blueprint(backstage_bp, url_prefix="/backstage/")
    app.register_blueprint(main_bp, url_prefix="/")
    logger.debug("Blueprints registered.")

    # Check MongoDB connection
    while True:
        try:
            mongodb.client.server_info()
            logger.debug("MongoDB connected.")
            break
        except ServerSelectionTimeoutError:
            logger.error("MongoDB is NOT connected. Retry in 60 secs.")
            time.sleep(60)

    logger.info("App initialization completed.")

    return app
