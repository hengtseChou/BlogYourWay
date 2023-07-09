from flask import Blueprint, render_template

blog = Blueprint('blog', __name__, template_folder='../templates/blog/')

@blog.route('/', methods = ['GET'])
def home():

    return render_template('home.html')

