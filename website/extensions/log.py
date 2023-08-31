import logging
from website.config import ENV
   
stream_formatter = logging.Formatter(
    fmt='[%(asctime)s] %(levelname)s: %(message)s'
)

file_formatter = logging.Formatter(
    fmt='[%(asctime)s] %(levelname)s in %(funcName)s, %(module)s: %(message)s'
)

if ENV == 'prod':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logger = gunicorn_logger

else:
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    # to stop showing https log

    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    file_handler = logging.FileHandler('app.log', 'w', 'utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
