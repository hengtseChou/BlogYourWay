from flask import Blueprint, render_template, request, flash, redirect, url_for
import bcrypt
from website.extensions.db import db_users

blog = Blueprint('blog', __name__, template_folder='../templates/blog/')

@blog.route('/', methods = ['GET'])
def home():
    # /{hank}/home
    # get data, post of hank from db

    return render_template('home.html', nav=True)

@blog.route('/login', methods = ['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html', nav=False)

    # find user in db

    # login user

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
    

