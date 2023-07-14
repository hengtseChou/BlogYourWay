from flask import Flask
from flask_login import LoginManager, UserMixin
import os

# from src.customer.routes import customer
# from src.admin.routes import admin
# from src.extensions.logger import allLogger
from website.blog.routes import blog, User
from website.backstage.routes import backstage
from website.extensions.db import db_users



def create_app():
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(16).hex()

    ## login 
    login_manager = LoginManager()
    login_manager.login_view = 'blog.login'
    login_manager.login_message = 'Please login to proceed.'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(username):
        user_data = db_users.find_via('username', username)
        user = User(user_data)
        # return none if the ID is not valid
        return user
    
    # blueprints
    app.register_blueprint(blog, url_prefix = '/')
    app.register_blueprint(backstage, url_prefix = '/backstage/')


    
    return app