from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, UserMixin
import bcrypt
from website.extensions.db import db_users

blog = Blueprint('blog', __name__, template_folder='../templates/blog/', static_folder='../static/')

class User(UserMixin):
    # user id is set as username    
    def __init__(self, user_data):
        for key, value in user_data.items():
            if key == 'username':
                self.id = value
                continue
            setattr(self, key, value)
        

@blog.route('/', methods = ['GET'])
def home():
    # /{hank}/home
    # get data, post of hank from db

    return render_template('home.html')

@blog.route('/login', methods = ['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html')
    
    login_form = request.form.to_dict()
    # find user in db
    if not db_users.exists('username', login_form['username']):
        flash('Username not found. Please try again.', category='error')
        return render_template('login.html')

    user_data = db_users.find_via('username', login_form['username'])
    # check pw
    if not bcrypt.checkpw(login_form['password'].encode('utf8'), user_data['password'].encode('utf8')):
        flash('Invalid password. Please try again.', category='error')
        return render_template('login.html') 
    # login user
    user = User(user_data)
    login_user(user)
    flash('Login Succeeded.', category='success')
    return redirect(url_for('backstage.panel'))



@blog.route('/register', methods = ['GET', 'POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')
    
    # registeration
    # check if user exists
    data = request.form.to_dict()    
    if db_users.exists('username', data['username']):
        flash('Username already exists. Please try another one.', category='error')
        return render_template('register.html')
    # create user in db

    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(12))
    hashed_pw = hashed_pw.decode('utf-8')
    data['password'] = hashed_pw
    del data['terms']
    db_users.create_user(data)

    # succeeded and return to login page
    flash('Registeration succeeded.', category='success')    
    return redirect(url_for('blog.login'))
    

