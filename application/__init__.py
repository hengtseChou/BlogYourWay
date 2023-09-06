from flask import Flask, render_template, request
from flask_login import LoginManager
import os
from application.blog.views import blog, User
from application.backstage.views import backstage
from application.extensions.log import logger
from application.extensions.mongo import db_users


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(16).hex()

    ## login
    login_manager = LoginManager()
    login_manager.login_view = "blog.login"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(username):
        user_creds = db_users.login.find_one({"username": username})
        user = User(user_creds)
        # return none if the ID is not valid
        return user

    # Register the custom 404 error page
    @app.errorhandler(404)
    def page_not_found(e):
        logger.debug(f'404 not found at {request.path} from {request.remote_addr}.')
        return render_template("404.html"), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error('Internal server error: %s', e)
        return render_template("500.html"), 500

    # blueprints
    app.register_blueprint(blog, url_prefix="/")
    app.register_blueprint(backstage, url_prefix="/backstage/")

    logger.info('APP INIT')

    return app
