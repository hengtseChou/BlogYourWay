from flask import Blueprint, render_template, request

blog = Blueprint('blog', __name__, template_folder='../templates/blog/')

@blog.route('/', methods = ['GET'])
def home():

    return render_template('home.html', nav=True)

@blog.route('/login', methods = ['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html', nav=False)

    # find user in db

    # login user

