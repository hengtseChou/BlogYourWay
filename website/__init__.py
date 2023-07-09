from flask import Flask
from flask_login import LoginManager, UserMixin
import os

# from src.customer.routes import customer
# from src.admin.routes import admin
# from src.extensions.logger import allLogger
from website.blog.routes import blog

class User(UserMixin):
    pass

def create_app():
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(16).hex()

    ## login 
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # blueprints
    app.register_blueprint(blog, url_prefix = '/')


    
    return app