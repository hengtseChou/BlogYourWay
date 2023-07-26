from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, logout_user, current_user
from datetime import datetime, timedelta
import random
import string
from website.extensions.db import db_users, db_posts
from website.config import ENV

backstage = Blueprint('backstage', __name__, template_folder='../templates/backstage/')


# @backstage.route('/', methods=['GET', 'POST'])
# @login_required
# def panel():

#     return render_template('panel.html')

### tabs

@backstage.route('/overview', methods=['GET', 'POST'])
@login_required
def overview():

    return render_template('overview.html')

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
            new_post['created_at'] = new_post['last_updated'] = datetime.now()
        elif ENV == 'prod':
            new_post['created_at'] = new_post['last_updated'] = datetime.now() + timedelta(hours=8)
        # set other attributes
        author = db_users.find_via('username', current_user.username)
        new_post['author'] = current_user.username
        # process tags
        if new_post['tags'] == '':
            new_post['tags'] = []
        else:
            new_post['tags'] = [tag.strip() for tag in new_post['tags'].split(',')]
        for tag in new_post['tags']:
            tag = tag.replace(" ", "-")
        db_users.update_values(current_user.username, 'posts_count', current_user.posts_count + 1)
        new_post['clicks'] = 0
        new_post['comments'] = 0
        new_post['archived'] = False
        new_post['featured'] = False
        # uid is used to link posts and comments
        alphabet = string.ascii_lowercase + string.digits
        uid = ''.join(random.choices(alphabet, k=8))
        while db_posts.exists('uid', uid):
            uid = ''.join(random.choices(alphabet, k=8))
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
            'archived': False
        }).sort('created_at', -1).limit(20) # descending: newest
    elif page > 1:
        posts = db_posts.collection.find({
            'author': current_user.username,
            'archived': False
        }).sort('created_at', -1).skip(min(page*20, max_skip)).limit(20)


    return render_template('posts.html', posts=posts)

@backstage.route('/archive', methods=['GET'])
@login_required
def archive_control():

    session['at'] = 'archive'

    # query through posts
    posts = db_posts.collection.find({
            'author': current_user.username,
            'archived': True
    }).sort('created_at', -1) # descending: newest

    return render_template('archive.html', posts=posts)

@backstage.route('/theme', methods=['GET', 'POST'])
@login_required
def theme():

    return render_template('theme.html')


### actions

@backstage.route('/edit-featured', methods=['GET'])
@login_required
def edit_featured():

    if session['at'] == 'posts':

        if request.args.get('featured') == 'to_true':
            featured_status_new = True
        else:
            featured_status_new = False
        post_uid = request.args.get('uid')

        db_posts.collection.update_one(filter={'uid': post_uid}, 
                                    update={'$set': {'featured': featured_status_new}})
    
    else: 
        flash('Access Denied. ', category='error')
    return redirect(url_for('backstage.post_control'))

@backstage.route('/edit-archived', methods=['GET'])
@login_required
def edit_archived():

    if session['at'] == 'posts':        
        post_uid = request.args.get('uid')

        db_posts.collection.update_one(filter={'uid': post_uid}, 
                                    update={'$set': {'archived': True}})
        return redirect(url_for('backstage.post_control'))
    
    elif session['at'] == 'archive':
        post_uid = request.args.get('uid')

        db_posts.collection.update_one(filter={'uid': post_uid}, 
                                    update={'$set': {'archived': False}})
        return redirect(url_for('backstage.archive_control'))

    
    flash('Access Denied. ', category='error')
    return redirect(url_for('backstage.archive_control'))
    
@backstage.route('/delete', methods=['GET'])
@login_required
def delete():

    target = request.args.get('type')
    uid = request.args.get('uid')

    if session['at'] == 'archive':

        if target == 'post':
            db_posts.collection.delete_one({'uid': uid})
            flash('Post deleted!', category='success')
            return redirect(url_for('backstage.archive_control'))
        elif target == 'work':
            # delete work
            return redirect(url_for('backstage.archive_control'))
    
    flash('Access Denied. ', category='error')
    return redirect(url_for('backstage.archive_control'))


@backstage.route('/logout', methods=['GET'])
@login_required
def logout():

    username = current_user.username
    logout_user()
    return redirect(url_for('blog.home', username=username))


