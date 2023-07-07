from flask import Flask
from flask_login import LoginManager, UserMixin
import os
from dotenv import load_dotenv

# from src.customer.routes import customer
# from src.admin.routes import admin
# from blog.extensions.db import 
# from src.extensions.email import mail
# from src.extensions.logger import allLogger

class User(UserMixin):
    pass

def create_app():
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(16).hex()
    ## login 
    


    
    return app