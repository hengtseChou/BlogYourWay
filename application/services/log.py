import logging
from flask import Request
from application.config import ENV

class MyLogger:
    def __init__(self):
        
        if ENV == "prod":
            self._logger = setup_prod_logger()
        elif ENV == "debug":
            self._logger = setup_debug_logger()

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

        self.debug(f"{request.path} was visited from {request.remote_addr}.")

    def invalid_username(self, username: str, request: Request):

        self.debug(
            f"Invalid username {username} at {request.path}. IP: {request.remote_addr}."
        )

    def invalid_post_uid(self, username: str, post_uid: str, request: Request):

        self.debug(
            f"Invalid post uid {post_uid} for user {username} was entered from {request.remote_addr}"
        )

    def invalid_autor_for_post(self, username: str, post_uid: str, request: Request):

        self.debug(
            f"The author entered ({username}) was not the author of the post {post_uid}. IP: {request.remote_addr}."
        )

    def invalid_procedure(self, username: str, procedure: str, request: Request):

        self.debug(
            f"Invalid procedure to {procedure} for {username} from {request.remote_addr}."
        )

    def log_for_backstage_tab(self, username: str, tab: str, request: Request):

        self.debug(
            f"User {username} is now at the {tab} tab. IP: {request.remote_addr}."
        )

    def log_for_pagination(self, username: str, num_of_posts: int, request: Request):

        self.debug(
            f"Showing {num_of_posts} posts for user {username} at {request.full_path} from {request.remote_addr}."
        )


class Log_for_User_Actions:
    def __init__(self, logger: MyLogger):

        self._logger = logger

    def login_failed(self, username: str, msg: str, request: Request):

        msg = msg.strip().strip(".")
        self._logger.debug(
            f"User {username} login failed. Msg: {msg}. IP: {request.remote_addr}."
        )

    def login_succeeded(self, username: str, request: Request):

        self._logger.info(
            f"User {username} has logged in successflly from {request.remote_addr}. "
        )

    def registration_failed(self, msg: str, request: Request):

        msg = msg.strip().strip(".")
        self._logger.debug(
            f"Registration failed. Msg: {msg}. IP: {request.remote_addr}."
        )

    def registration_succeeded(self, username: str, request: Request):

        self._logger.info(
            f"New user {username} has been created from {request.remote_addr}"
        )

    def logout(self, username: str, request: Request):

        self._logger.info(f"User {username} has logged out from {request.remote_addr}.")

    def deleted(self, username: str, request: Request):

        self._logger.info(
            f"User {username} has been deleted from {request.remote_addr}."
        )

    def data_created(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been created from {request.remote_addr}."
        )

    def data_updated(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been updated from {request.remote_addr}."
        )

    def data_deleted(self, username: str, data_info: str, request: Request):

        data_info_capitalized = data_info.capitalize().strip()
        self._logger.info(
            f"{data_info_capitalized} for user {username} has been deleted from {request.remote_addr}."
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


my_logger = MyLogger()
