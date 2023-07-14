from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from website.extensions.db import db_users

backstage = Blueprint('backstage', __name__, template_folder='../templates/backstage/', static_folder='../static/')


@backstage.route('/', methods=['GET', 'POST'])
@login_required
def panel():

    return render_template('panel.html')

