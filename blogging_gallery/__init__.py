"""
Configure little-blog application in create_app() with a factory pattern.
"""
from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_session import Session
from pymongo.errors import ServerSelectionTimeoutError

from blogging_gallery.config import APP_SECRET, ENV, REDIS_HOST, REDIS_PORT, REDIS_PW
from blogging_gallery.services.cache import cache
from blogging_gallery.services.log import my_logger, return_client_ip
from blogging_gallery.services.mongo import my_database
from blogging_gallery.services.redis import my_redis
from blogging_gallery.services.socketio import socketio
from blogging_gallery.utils.users import User
from blogging_gallery.views import backstage_bp, blog_bp

if ENV == "develop":
    cache_config = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
elif ENV == "prod":
    cache_config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": REDIS_HOST,
        "CACHE_REDIS_PORT": REDIS_PORT,
        "CACHE_REDIS_PASSWORD": REDIS_PW,
    }


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
    my_logger.info("App initialization started.")
    app.secret_key = APP_SECRET

    # debug mode
    if ENV == "develop":
        app.config["DEBUG"] = True
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        my_logger.debug("Debugtoolbar configured.")

    ## login
    login_manager = LoginManager()
    login_manager.login_view = "blog.login_get"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)
    my_logger.debug("Login manager configured.")

    @login_manager.user_loader
    def user_loader(username: str) -> User:
        """register user loader for current_user to access"""
        user_creds = my_database.user_login.find_one({"username": username})
        user = User(user_creds)
        # return none if the ID is not valid
        return user

    # Register the custom error page
    @app.errorhandler(404)
    def page_not_found(error):
        client_ip = return_client_ip(request, ENV)
        my_logger.debug(f"{client_ip} - 404 not found at {request.environ['RAW_URI']}. ")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        client_ip = return_client_ip(request, ENV)
        my_logger.error(
            f"{client_ip} - 500 internal error at {request.environ['RAW_URI']}."
        )
        # flask app itself will show the error occurred
        return render_template("500.html"), 500

    my_logger.debug("Error handlers registered.")

    # blueprints
    app.register_blueprint(blog_bp, url_prefix="/")
    app.register_blueprint(backstage_bp, url_prefix="/backstage/")
    my_logger.debug("Blueprints registered.")

    # cache
    cache.init_app(app, config=cache_config)
    my_logger.debug("Flask-caching configured.")

    # socketio
    socketio.init_app(app, manage_session=False)
    my_logger.debug("Flask-socketio configured.")

    # session
    session = Session()
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = my_redis
    session.init_app(app)
    my_logger.debug("Flask-session configured.")

    # check connection
    try:
        my_database.client.server_info()
        my_logger.debug("MongoDB is connected.")
    except ServerSelectionTimeoutError as error:
        my_logger.error(error)
        exit("MongoDB is NOT connected. App initializaion failed.")

    try:
        my_redis.ping()
        my_logger.debug("Redis is connected.")
    except Exception as error:
        my_logger.error(error)
        exit("Redis is NOT connected. App initializaion failed.")

    my_logger.info("App initialization completed.")

    return app
