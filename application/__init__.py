"""
Configure little-blog application in create_app() with a factory pattern.
"""
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_debugtoolbar import DebugToolbarExtension

from application.config import APP_SECRET, ENV, REDIS_HOST, REDIS_PORT, REDIS_PW
from application.services.cache import cache
from application.services.log import my_logger, return_client_ip
from application.services.mongo import my_database
from application.utils.users import User
from application.views import backstage_bp, blog_bp

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
    - secret keys
    - login manager (login view, login message)
    - user loader
    - 404 error handler page
    - 500 error handler page
    - register blueprints (blog, backstage)
    """

    app = Flask(__name__)
    app.config["SECRET_KEY"] = APP_SECRET

    # debug mode
    if ENV == "develop":
        app.config["DEBUG"] = True
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

    ## login
    login_manager = LoginManager()
    login_manager.login_view = "blog.login_get"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)

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
        return render_template("500.html"), 500

    # blueprints
    app.register_blueprint(blog_bp, url_prefix="/")
    app.register_blueprint(backstage_bp, url_prefix="/backstage/")

    # cache
    cache.init_app(app, config=cache_config)

    my_logger.info("APP INIT")

    return app
