from website import create_app
from website.config import ENV
import os


if ENV == 'debug':
    DEBUG = True
else:
    DEBUG = False

app = create_app()

if __name__ == '__main__':
    if DEBUG:
        app.run(debug=True, port=5000)
    else:
        app.run(port=5000)