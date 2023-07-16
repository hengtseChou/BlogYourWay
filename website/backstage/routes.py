from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, logout_user, current_user
from datetime import datetime, timedelta
from uuid import uuid4
from website.extensions.db import db_users, db_posts
from website.config import ENV

backstage = Blueprint('backstage', __name__, template_folder='../templates/backstage/', static_folder='../static/')


@backstage.route('/', methods=['GET', 'POST'])
@login_required
def panel():

    return render_template('panel.html')

@backstage.route('/posts', methods=['GET', 'POST'])
@login_required
def post_control():

    session['at'] = 'posts'
    page = request.args.get('page', default = 1, type = int)

    if request.method == 'POST':
        # create a new post in db
        new_post = request.form.to_dict()
        # set posting time  
        if ENV == 'debug':
            new_post['created_at'] = datetime.now()
        elif ENV == 'prod':
            new_post['created_at'] = datetime.now() + timedelta(hours=8)
        # set other attributes
        author = db_users.find_via('username', current_user.username)
        new_post['author'] = current_user.username
        new_post['post_id'] = author['posts_count'] + 1
        new_post['tags'] = [tag.strip() for tag in new_post['tags'].split(',')]
        db_users.update_values(current_user.username, 'posts_count', current_user.posts_count + 1)
        new_post['clicks'] = 0
        new_post['comments'] = 0
        new_post['archieved'] = False
        new_post['featured'] = False
        # uid is used to link posts and comments
        uid = str(uuid4())
        if not db_posts.exists('uid', uid):
            new_post['uid'] = uid
        db_posts.new_post(new_post)
        flash('New post published successfully!', category='success')


    # query through posts
    # 20 posts for each page  

    posts_not_archieved = db_posts.collection.count_documents({'author':current_user.username,
                                                               'archieved': False})
    max_skip = (posts_not_archieved // 20 - 1) * 20

    if page == 1:
        posts = db_posts.collection.find({
            'author': current_user.username,
            'archieved': False
        }).limit(20).sort('created_at', -1) # descending: newest
    elif page > 1:
        posts = db_posts.collection.find({
            'author': current_user.username,
            'archieved': False
        }).skip(min(page*20, max_skip)).limit(20).sort('created_at', -1)


    return render_template('posts.html', posts=posts)
    

@backstage.route('/theme', methods=['GET', 'POST'])
@login_required
def theme():

    return render_template('theme.html')

@backstage.route('/logout', methods=['GET'])
@login_required
def logout():

    logout_user()
    return redirect(url_for('blog.home'))


