from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from flask_login import login_required, logout_user, current_user
from datetime import datetime, timedelta
import random
import string
import bcrypt
from math import ceil
from website.extensions.db_mongo import db_users, db_posts
from website.extensions.db_redis import redis_method
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

    now = datetime.now()
    user = db_users.find_one({'username': current_user.username})  

    time_difference = now - user['created_at']
    days_difference = time_difference.days + 1
    print(time_difference)

    return render_template('overview.html', user=user)

@backstage.route('/posts', methods=['GET', 'POST'])
@login_required
def post_control():

    session['user_status'] = 'posts'
    page = request.args.get('page', default = 1, type = int)
    user = db_users.find_one({'username': current_user.username})  


    if request.method == 'POST':
        # create a new post in db
        new_post = request.form.to_dict()
        # set posting time  
        if ENV == 'debug':            
            new_post['created_at'] = new_post['last_updated'] = datetime.now()
        elif ENV == 'prod':
            new_post['created_at'] = new_post['last_updated'] = datetime.now() + timedelta(hours=8)
        # set other attributes
        new_post['author'] = current_user.username
        # process tags
        if new_post['tags'] == '':
            new_post['tags'] = []
        else:
            new_post['tags'] = [tag.strip() for tag in new_post['tags'].split(',')]
        for tag in new_post['tags']:
            tag = tag.replace(" ", "-")
        db_users.update_one(
            {'username': current_user.username}, 
            {'posts_count': user['posts_count'] + 1}
        )
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
    POSTS_EACH_PAGE = 20

    num_not_archieved = db_posts.count_documents({
        'author': current_user.username,
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

    if page == 1:
        posts = db_posts.find({
            'author': current_user.username,
            'archived': False
        }).sort('created_at', -1).limit(POSTS_EACH_PAGE) # descending: newest
    elif page > 1:
        
        posts = db_posts.find({
            'author': current_user.username,
            'archived': False
        }).sort('created_at', -1).skip((page - 1) * POSTS_EACH_PAGE).limit(POSTS_EACH_PAGE)
    

    posts = list(posts)
    for post in posts:
        del post['content']            
        post['created_at'] = post['created_at'].strftime("%Y/%m/%d %H:%M:%S")
        post['clicks'] = redis_method.get_count(f"post_uid_{post['uid']}")
        post['clicks'] = format(post['clicks'], ',')
        post['comments'] = format(post['comments'], ',')

    return render_template('posts.html', 
                           posts=posts, 
                           current_page=page,
                           newer_posts=enable_newer_post, 
                           older_posts=enable_older_post)

@backstage.route('/about', methods=['GET', 'POST'])
@login_required
def about_control():

    session['user_status'] = 'about'
    user = db_users.find_one({'username': current_user.username})  

    if request.method == 'POST':  

        updated_about = request.form.to_dict()
        db_users.update_one(
            filter={'username': current_user.username},
            update=updated_about
        )
        flash('Information updated!', category='success')


    return render_template('edit_about.html', user=user)

@backstage.route('/archive', methods=['GET'])
@login_required
def archive_control():

    session['user_status'] = 'archive'

    # query through posts
    posts = db_posts.find({
        'author': current_user.username,
        'archived': True
    }).sort('created_at', -1) # descending: newest

    return render_template('archive.html', posts=posts)

@backstage.route('/theme', methods=['GET', 'POST'])
@login_required
def theme():

    return render_template('theme.html')

@backstage.route('/settings', methods=['GET', "POST"])
@login_required
def settings():

    session['user_status'] = 'settings'

    if request.method == 'POST':

        general = request.form.get('general')
        change_pw = request.form.get('changepw')
        delete_account = request.form.get('delete-account')

        if general is not None:

            banner_url = request.form.get('banner_url')
            db_users.update_one(
                {'username': current_user.username}, 
                {'banner_url': banner_url}
            )
            flash('Update succeeded!', category='success')

        elif change_pw is not None:

            current_pw = request.form.get('current')
            new_pw = request.form.get('new')

            user = db_users.find_one({'username': current_user.username})

            # check pw
            if not bcrypt.checkpw(current_pw.encode('utf8'), user['password'].encode('utf8')):
                flash('Current password is invalid. Please try again.', category='error')
                return render_template('settings.html', user=user)

            # update new password
            hashed_pw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt(12))
            hashed_pw = hashed_pw.decode('utf-8')
            db_users.update_one(
                {'username': current_user.username},
                {'password': hashed_pw}
            )
            flash('Password update succeeded!', category='success')
        
        elif delete_account is not None:

            # get all post id, because we want to also remove relevant comments
            # remove all posts
            # remove postfolio
            # logout user
            # remove user
            confirm_pw = request.form.get('delete-confirm-pw')
            user = db_users.find_one({'username': current_user.username})  


            if not bcrypt.checkpw(confirm_pw.encode('utf8'), user['password'].encode('utf8')):
                flash('Access denied, bacause password is invalid.', category='error')
                return render_template('settings.html', user=user)
            
            # deletion procedure

            posts_id_to_delete = []
            posts_to_delete = list(db_posts.find({'author': current_user.username}))
            for post in posts_to_delete: 
                posts_id_to_delete.append(post['uid'])

            db_posts.delete_many({'author': user['username']})
            logout_user()

            db_users.delete_one({'username': user['username']})
            flash("Account deleted successfully!", category='success')

            return redirect(url_for('blog.register'))

            
            


    user = db_users.find_one({'username': current_user.username})  


    return render_template('settings.html', user=user)

@backstage.route('/posts/edit/<post_uid>', methods=['GET', 'POST'])
@login_required
def edit_post(post_uid):  

    if session['user_status'] != 'posts':
        flash('Access Denied!', category='error')
        return redirect(url_for('backstage.post_control'))  

    if request.method == 'GET':

        target_post = db_posts.find_one({'uid': post_uid})
        target_post = dict(target_post)
        target_post['tags'] = ', '.join(target_post['tags'])

        return render_template('edit_blogpost.html', post=target_post)
    
    updated_post = request.form.to_dict()
    # set last update time  
    if ENV == 'debug':            
        updated_post['last_updated'] = datetime.now()
    elif ENV == 'prod':
        updated_post['last_updated'] = datetime.now() + timedelta(hours=8)
    # process tags
    if updated_post['tags'] == '':
        updated_post['tags'] = []
    else:
        updated_post['tags'] = [tag.strip() for tag in updated_post['tags'].split(',')]
    for tag in updated_post['tags']:
        tag = tag.replace(" ", "-")

    db_posts.update_one(
        filter={'uid': post_uid}, 
        update=updated_post
    )

    flash(f'Post <{post_uid}> update succeeded!', category='success')
    return redirect(url_for('backstage.post_control'))
        


### actions

@backstage.route('/edit-featured', methods=['GET'])
@login_required
def edit_featured():

    if session['user_status'] == 'posts':

        if request.args.get('featured') == 'to_true':
            featured_status_new = True
        else:
            featured_status_new = False
        post_uid = request.args.get('uid')

        db_posts.update_one(filter={'uid': post_uid}, 
                            update={'featured': featured_status_new})
    
    else: 
        flash('Access Denied. ', category='error')
    return redirect(url_for('backstage.post_control'))

@backstage.route('/edit-archived', methods=['GET'])
@login_required
def edit_archived():

    if session['user_status'] == 'posts':        
        post_uid = request.args.get('uid')

        db_posts.update_one(filter={'uid': post_uid}, 
                            update={'archived': True})
        return redirect(url_for('backstage.post_control'))
    
    elif session['user_status'] == 'archive':
        post_uid = request.args.get('uid')

        db_posts.update_one(filter={'uid': post_uid}, 
                            update={'archived': False})
        return redirect(url_for('backstage.archive_control'))

    
    flash('Access Denied. ', category='error')
    return redirect(url_for('backstage.archive_control'))
    
@backstage.route('/delete', methods=['GET'])
@login_required
def delete():

    target = request.args.get('type')
    uid = request.args.get('uid')

    if session['user_status'] == 'archive':

        if target == 'post':
            db_posts.delete_one({'uid': uid})
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


