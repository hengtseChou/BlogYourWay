import logging
from flask import Request
from application.config import ENV

def _return_client_ip(request: Request):
    if ENV == 'debug':
        return request.remote_addr
    elif ENV == 'prod':
        return request.headers.get('X-Forwarded-For')
    
class MyLogger:
    def __init__(self, logger: logging.Logger):

        self._logger = logger
        self.user = Log_for_User_Actions(self._logger)

    def debug(self, msg):
        
        self._logger.debug(msg)

    def info(self, msg):

        self._logger.info(msg)

    def warning(self, msg):

        self._logger.warning(msg)

    def error(self, msg):
        
        self._logger.error(msg)

    def page_visited(self, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(f"{request.path} was visited from {client_ip}.")

    def invalid_username(self, username: str, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"Invalid username {username} at {request.path}. IP: {client_ip}."
        )

    def invalid_post_uid(self, username: str, post_uid: str, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"Invalid post uid {post_uid} for user {username} was entered from {client_ip}"
        )

    def invalid_autor_for_post(self, username: str, post_uid: str, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"The author entered ({username}) was not the author of the post {post_uid}. IP: {client_ip}."
        )

    def invalid_procedure(self, username: str, procedure: str, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"Invalid procedure to {procedure} for {username} from {client_ip}."
        )

    def log_for_backstage_tab(self, username: str, tab: str, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"User {username} is now at the {tab} tab. IP: {client_ip}."
        )

    def log_for_pagination(self, username: str, num_of_posts: int, request: Request):

        client_ip = _return_client_ip(request)
        self.debug(
            f"Showing {num_of_posts} posts for user {username} at {request.full_path} from {client_ip}."
        )


class Log_for_User_Actions:
    def __init__(self, logger: logging.Logger):

        self._logger = logger

    def login_failed(self, msg: str, request: Request):

        msg = msg.strip().strip(".")
        client_ip = _return_client_ip(request)
        self._logger.debug(
            f"Login failed. Msg: {msg}. IP: {client_ip}."
        )

    def login_succeeded(self, username: str, request: Request):

        client_ip = _return_client_ip(request)
        self._logger.info(
            f"User {username} has logged in successfully from {client_ip}. "  
        )

    def registration_failed(self, msg: str, request: Request):

        msg = msg.strip().strip(".")
        client_ip = _return_client_ip(request)
        self._logger.debug(
            f"Registration failed. Msg: {msg}. IP: {client_ip}."
        )

    def registration_succeeded(self, username: str, request: Request):

        client_ip = _return_client_ip(request)
        self._logger.info(
            f"New user {username} has been created from {client_ip}"
        )

    def logout(self, username: str, request: Request):

        client_ip = _return_client_ip(request)
        self._logger.info(f"User {username} has logged out from {client_ip}.")

    def deleted(self, username: str, request: Request):

        client_ip = _return_client_ip(request)
        self._logger.info(
            f"User {username} has been deleted from {client_ip}."
        )

    def data_created(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        client_ip = _return_client_ip(request)
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been created from {client_ip}."
        )

    def data_updated(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        client_ip = _return_client_ip(request)
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been updated from {client_ip}."
        )

    def data_deleted(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        client_ip = _return_client_ip(request)
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been deleted from {client_ip}."
        )


def setup_prod_logger():

    gunicorn_logger = logging.getLogger("gunicorn.error")
    logger = gunicorn_logger

    return logger


def setup_debug_logger():

    # to stop showing https log
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.ERROR)

    stream_formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)s: %(message)s")

    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s in %(funcName)s, %(module)s: %(message)s"
    )

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler("app.log", "w", "utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger

if ENV == "prod":
    logger_initialized = setup_prod_logger()
elif ENV == "debug":
    logger_initialized = setup_debug_logger()

my_logger = MyLogger(logger=logger_initialized)
