from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_user, UserMixin, current_user
import bcrypt
from datetime import datetime
from urllib.parse import unquote
import markdown
from website.extensions.db import db_users, db_posts
from website.blog.utils import modify_post_format

blog = Blueprint('blog', __name__, template_folder='../templates/blog/')

md = markdown.Markdown(
    extensions=[
        'markdown_captions'
    ]
)

class User(UserMixin):
    # user id is set as username    
    def __init__(self, user_data):
        for key, value in user_data.items():
            if key == 'username':
                self.id = value
                self.username = value
                continue
            setattr(self, key, value)
        

@blog.route('/<username>/home', methods = ['GET'])
def home(username):
    # /{hank}/home
    # get data, post of hank from db

    if db_users.exists('username', username):
        user = db_users.find_one({'username': username})
        featured_posts = db_posts.find({
            'author': username, 
            'featured': True,
            'archived': False
        }).sort('created_at', -1).limit(8)
        featured_posts = list(featured_posts)
        feature_idx = 1
        for post in featured_posts:
            del post['content']
            post['idx'] = feature_idx
            feature_idx += 1            
            post['created_at'] = post['created_at'].strftime("%Y-%m-%d")

        return render_template('home.html', user=user, posts=featured_posts, num_of_posts=len(featured_posts))
    

    else:
        abort(404)
    

@blog.route('/login', methods = ['GET', 'POST'])
def login():

    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('You are already logged in.')
            return redirect(url_for('backstage.panel'))
        return render_template('login.html')
    
    login_form = request.form.to_dict()
    # find user in db
    if not db_users.exists('username', login_form['username']):
        flash('Username not found. Please try again.', category='error')
        return render_template('login.html')

    user_data = db_users.find_one({'username': login_form['username']})
    # check pw
    if not bcrypt.checkpw(login_form['password'].encode('utf8'), user_data['password'].encode('utf8')):
        flash('Invalid password. Please try again.', category='error')
        return render_template('login.html') 
    # login user
    user = User(user_data)
    login_user(user)
    flash('Login Succeeded.', category='success')
    return redirect(url_for('backstage.overview'))



@blog.route('/register', methods = ['GET', 'POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')
    
    # registeration
    # check if user exists
    new_user = request.form.to_dict()    
    if db_users.exists('username', new_user['username']):
        flash('Username already exists. Please try another one.', category='error')
        return render_template('register.html')
    
    # create user in db
    hashed_pw = bcrypt.hashpw(new_user['password'].encode('utf-8'), bcrypt.gensalt(12))
    hashed_pw = hashed_pw.decode('utf-8')
    new_user['password'] = hashed_pw
    new_user['posts_count'] = 0
    new_user['clicks'] = {'total':0, 'home':0, 'blog':0, 'portfolio':0, 'about':0}
    # about(bio, profile pic, about), theme, social links
    del new_user['terms']
    db_users.create_user(new_user)

    # succeeded and return to login page
    flash('Registeration succeeded.', category='success')    
    return redirect(url_for('blog.login'))


@blog.route('/<username>/tags/<tag>', methods=['GET'])
def tag(username, tag):

    tag = request.args.get('tag')
    tag_decoded = unquote(tag)

    # ... main: posts with tags; side: recent post titles

    return tag_decoded


@blog.route('/<username>/posts/<post_uid>', methods=['GET'])
def post(username, post_uid):

    author = db_users.find_one({'username': username})

    target_post = dict(db_posts.find_one({'uid': post_uid}))
    target_post['content'] = md.convert(target_post['content'])
    target_post['content'] = modify_post_format(target_post['content'])
    target_post['last_updated'] = target_post['last_updated'].strftime("%Y-%m-%d")
    print(target_post['content'])
    db_posts.update_one(
        {'uid': post_uid},
        {'clicks': target_post['clicks'] + 1}
    )

    return render_template('blogpost.html', 
                           user=author,
                           post=target_post)
    

