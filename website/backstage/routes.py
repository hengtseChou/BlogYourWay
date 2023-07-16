from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, logout_user
from website.extensions.db import db_users, db_posts
from website.config import ENV

backstage = Blueprint('backstage', __name__, template_folder='../templates/backstage/', static_folder='../static/')


@backstage.route('/', methods=['GET', 'POST'])
@login_required
def panel():

    return render_template('panel.html')

@backstage.route('/posts', methods=['GET', 'POST'])
@login_required
def posts():

    if request.method == 'GET':
        return render_template('posts.html')
    
    return request.form
    

@backstage.route('/theme', methods=['GET', 'POST'])
@login_required
def theme():

    return render_template('theme.html')

@backstage.route('/logout', methods=['GET'])
@login_required
def logout():

    logout_user()
    return redirect(url_for('blog.home'))


