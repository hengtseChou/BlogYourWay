from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_user, UserMixin, current_user
import bcrypt
import string 
import random
from datetime import datetime, timedelta
from urllib.parse import unquote
from math import ceil
from website.extensions.db_mongo import db_users, db_posts, db_comments
from website.extensions.db_redis import redis_method
from website.blog.utils import HTML_Formatter, all_user_tags, is_comment_verified, md
from website.config import ENV

blog = Blueprint('blog', __name__, template_folder='../templates/blog/')



class User(UserMixin):
    # user id is set as username    
    def __init__(self, user_data):
        for key, value in user_data.items():
            if key == 'username':
                self.id = value
                self.username = value
                continue
            setattr(self, key, value) 

@blog.route('/', methods=['GET'])
def landing_page():


    return render_template('landing_page.html')



@blog.route('/login', methods = ['GET', 'POST'])
def login():

    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('You are already logged in.')
            return redirect(url_for('backstage.panel'))
        return render_template('login.html')
    
    login_form = request.form.to_dict()
    # find user in db
    if not db_users.exists('email', login_form['email']):
        flash('Account not found. Please try again.', category='error')
        return render_template('login.html')

    user_data = db_users.find_one({'email': login_form['email']})
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
    # with unique email, username and blog name
    new_user = request.form.to_dict()
    # make sure username has no space character
    new_user['username'] = new_user['username'].strip().replace(' ', '-')
    if db_users.exists('email', new_user['email']):
        flash('Email is already used. Please try another one.', category='error')
        return render_template('register.html')
    
    if db_users.exists('username', new_user['username']):
        flash('Username is already used. Please try another one.', category='error')
        return render_template('register.html')
    
    if db_users.exists('blogname', new_user['blogname']):
        flash('Blog name is already used. Please try another one.')
        return render_template('register.html')      
    
    
    # create user in db
    hashed_pw = bcrypt.hashpw(new_user['password'].encode('utf-8'), bcrypt.gensalt(12))
    hashed_pw = hashed_pw.decode('utf-8')
    new_user['password'] = hashed_pw
    new_user['posts_count'] = 0
    new_user['banner_url'] = ""
    new_user['profile_img_url'] = ""
    new_user['short_bio'] = ""
    new_user['about'] = ""
    new_user['social_links'] = []
    if ENV == 'debug':            
        new_user['created_at']  = datetime.now()
    elif ENV == 'prod':
        new_user['created_at']  = datetime.now() + timedelta(hours=8)
    #  theme, social links
    del new_user['terms']
    db_users.create_user(new_user)

    # succeeded and return to login page
    flash('Registeration succeeded.', category='success')    
    return redirect(url_for('blog.login'))



@blog.route('/<username>/home', methods = ['GET'])
def home(username):
    # /{hank}/home
    # get data, post of hank from db
    if not db_users.exists('username', username):
        abort(404)

    user = db_users.find_one({'username': username})
    featured_posts = db_posts.find({
        'author': username, 
        'featured': True,
        'archived': False
    }).sort('created_at', -1).limit(10)
    featured_posts = list(featured_posts)
    feature_idx = 1
    for post in featured_posts:
        del post['content']
        post['idx'] = feature_idx
        feature_idx += 1            
        post['created_at'] = post['created_at'].strftime("%Y-%m-%d")

    # update visitor counts
    redis_method.increment_count(f"{username}_home", request)
    redis_method.increment_count(f"{username}_uv", request)    


    return render_template('home.html', 
                           user=user, 
                           posts=featured_posts, 
                           num_of_posts=len(featured_posts))


@blog.route('/<username>/tags', methods=['GET'])
def tag(username):

    if not db_users.exists('username', username):
        abort(404)
    user = db_users.find_one({'username': username})
    # currently no pagination for tag    

    tag = request.args.get('tag', default=None, type=str)
    if tag is None:
        return redirect(url_for('blog.blogpage', username=username))
    # decode form url
    tag_decoded = unquote(tag)

    # abort for unknown tag
    all_tags = all_user_tags(username)
    if tag_decoded not in all_tags.keys():
        abort(404)

    posts = db_posts.find({
        'author': username, 
        'archived': False
    }).sort('created_at', -1)

    posts = list(posts)
    posts_has_tag = []
    idx = 1
    for post in posts:
        if tag_decoded in post['tags']:
            del post['content']
            post['idx'] = idx
            idx += 1
            post['created_at'] = post['created_at'].strftime("%Y-%m-%d")
            posts_has_tag.append(post)


    # update visitor counts
    redis_method.increment_count(f"{username}_tag: {tag_decoded}", request)
    redis_method.increment_count(f"{username}_uv", request)


    return render_template('tag.html', 
                           user=user, 
                           posts=posts_has_tag, 
                           tag=tag_decoded,
                           num_of_posts=len(posts_has_tag))


@blog.route('/<username>/posts/<post_uid>', methods=['GET', 'POST'])
def post(username, post_uid):

    if not db_users.exists('username', username):
        abort(404)
    if not db_posts.exists('uid', post_uid):
        abort(404)

    author = db_users.find_one({'username': username})
    target_post = dict(db_posts.find_one({'uid': post_uid}))

    # to verify the post is linked to the user
    if author['username'] != target_post['author']:
        abort(404)

    # add comments
    if request.method == 'POST':

        token = request.form.get('g-recaptcha-response')

        if is_comment_verified(token):

            new_comment = {}
            if ENV == 'debug':
                new_comment['created_at'] = datetime.now()
            elif ENV == 'prod':
                new_comment['created_at'] = datetime.now() + timedelta(hours=8)
            new_comment['post_uid'] = post_uid
            new_comment['profile_pic'] = '/static/img/visitor.png'
            new_comment['profile_link'] = ''
            new_comment['comment'] = request.form.get('comment')
            alphabet = string.ascii_lowercase + string.digits
            uid = ''.join(random.choices(alphabet, k=8))
            while db_comments.exists('comment_uid', uid):
                uid = ''.join(random.choices(alphabet, k=8))
            new_comment['comment_uid'] = uid

            if current_user.is_authenticated:
                commenter = dict(db_users.find_one({'username': current_user.username}))
                new_comment['name'] = current_user.username
                new_comment['email'] = commenter['email']
                new_comment['profile_link'] = f'/{current_user.username}/about'
                if commenter['profile_img_url']:
                    new_comment['profile_pic'] = commenter['profile_img_url']
            else:
                new_comment['name'] = request.form.get('name')
                new_comment['email'] = request.form.get('email')

            db_comments.new_comment(new_comment)
            db_posts.update_one(
                {'uid': post_uid}, 
                {'comments': target_post['comments'] + 1}
            )
            flash('Comment published!', category='success')
                



    target_post['content'] = md.convert(target_post['content'])
    target_post['content'] = HTML_Formatter(target_post['content']).to_blogpost()
    target_post['last_updated'] = target_post['last_updated'].strftime("%Y-%m-%d")

    # find comments
    comments = db_comments.find({'post_uid': post_uid}).sort('created_at', 1)# oldest to newest comment
    comments = list(comments)
    for comment in comments:
        comment['created_at'] = comment['created_at'].strftime("%Y-%m-%d %H:%M:%S")

    # update visitor counts
    redis_method.increment_count(f"post_uid_{target_post['uid']}", request)
    redis_method.increment_count(f"{username}_uv", request)


    return render_template('blogpost.html', 
                           user=author,
                           post=target_post, 
                           comments=comments)

@blog.route('/<username>/about', methods=['GET'])
def about(username):

    if not db_users.exists('username', username):
        abort(404)
    user = db_users.find_one({'username': username}) 
    about_content = md.convert(user['about'])
    about_content = HTML_Formatter(about_content).to_about()

    # update visitor counts
    redis_method.increment_count(f"{username}_about", request)
    redis_method.increment_count(f"{username}_uv", request)

    return render_template('about.html', 
                           user=user,
                           about=about_content)


@blog.route('/<username>/blog', methods=['GET'])
def blogpage(username):

    if not db_users.exists('username', username):
        abort(404)
    user = db_users.find_one({'username': username})
    page = request.args.get('page', default = 1, type = int)
    POSTS_EACH_PAGE = 10
    
    # create a tag dict
    tags_dict = all_user_tags(username)

    # set up for pagination
    num_not_archieved = db_posts.count_documents({
        'author': username,
        'archived': False
    })
    if num_not_archieved == 0:
        max_page = 1
    else:
        max_page = ceil(num_not_archieved / POSTS_EACH_PAGE)

    if page > max_page:
        # not a legal page number
        abort(404)    

    enable_older_post = False
    if page * POSTS_EACH_PAGE < num_not_archieved:
        enable_older_post = True

    enable_newer_post = False
    if page > 1:
        enable_newer_post = True

    # skip and limit posts with given page
    if page == 1:
        posts = db_posts.find({
            'author': username,
            'archived': False
        }).sort('created_at', -1).limit(POSTS_EACH_PAGE) # descending: newest
    elif page > 1:        
        posts = db_posts.find({
            'author': username,
            'archived': False
        }).sort('created_at', -1).\
            skip((page - 1) * POSTS_EACH_PAGE).\
            limit(POSTS_EACH_PAGE)   

    idx = 1
    posts = list(posts)
    for post in posts:
        del post['content']
        post['idx'] = idx
        idx += 1            
        post['created_at'] = post['created_at'].strftime("%Y-%m-%d")
    num_of_posts = len(posts)

    # update visitor counts
    redis_method.increment_count(f"{username}_uv", request)    
    
    return render_template('blog.html', 
                           user = user,
                           posts = posts,
                           num_of_posts = num_of_posts,
                           tags = tags_dict, 
                           current_page = page, 
                           newer_posts = enable_newer_post, 
                           older_posts = enable_older_post)