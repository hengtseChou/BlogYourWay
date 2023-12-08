import logging

from flask import Request

from blogging_gallery.config import ENV


def return_client_ip(request: Request, env: str):
    if env == "develop":
        return request.remote_addr
    elif env == "prod":
        return request.headers.get("X-Forwarded-For")


def _setup_prod_logger():
    gunicorn_logger = logging.getLogger("gunicorn.error")
    logger = gunicorn_logger

    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s in %(funcName)s, %(module)s: %(message)s"
    )
    file_handler = logging.FileHandler("prod.log", "w", "utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger


def _setup_debug_logger():
    # to stop showing CLF in my logger
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

    file_handler = logging.FileHandler("develop.log", "w", "utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger


class MyLogger:
    def __init__(self, env: str):
        """Initialize the my logger instance based on the current enviroment.

        Args:
            env (str): Specify the developement enviroment. Possible values: debug, prod.
        """

        if env == "prod":
            self._logger = _setup_prod_logger()
        elif env == "develop":
            self._logger = _setup_debug_logger()

        self.user = Log_for_User_Actions(self._logger)

    def debug(self, msg):
        self._logger.debug(msg)

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)

    def page_viewed(self, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(f"{client_ip} - {request.environ.get('RAW_URI')} was visited.")

    def invalid_username(self, username: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(
            f"{client_ip} - Invalid username {username} at {request.environ.get('RAW_URI')}."
        )

    def invalid_post_uid(self, username: str, post_uid: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(
            f"{client_ip} - Invalid post uid {post_uid} for user {username} was entered. "
        )

    def invalid_author_for_post(self, username: str, post_uid: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(
            f"{client_ip} - The author entered ({username}) was not the author of the post {post_uid}. "
        )

    def invalid_procedure(self, username: str, procedure: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(f"{client_ip} - Invalid procedure to {procedure} for {username}.")

    def log_for_backstage_tab(self, username: str, tab: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(f"{client_ip} - User {username} is now at the {tab} tab. ")

    def log_for_pagination(self, username: str, num_of_posts: int, request: Request):
        client_ip = return_client_ip(request, ENV)
        self.debug(
            f"{client_ip} - Showing {num_of_posts} posts for user {username} at {request.environ.get('RAW_URI')}. "
        )


class Log_for_User_Actions:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def login_failed(self, msg: str, request: Request):
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Login failed. Msg: {msg}. ")

    def login_succeeded(self, username: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has logged in. ")

    def logout(self, username: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(
            f"{client_ip} - User {username} has logged out and session data is cleared."
        )

    def registration_failed(self, msg: str, request: Request):
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Registration failed. Msg: {msg}. ")

    def registration_succeeded(self, username: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - New user {username} has been created. ")

    def user_deleted(self, username: str, request: Request):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has been deleted.")

    def data_created(self, username: str, data_info: str, request: Request):
        data_info_capitalized = data_info.capitalize().strip()
        client_ip = return_client_ip(request, ENV)
        self._logger.info(
            f"{client_ip} - {data_info_capitalized} for user {username} has been created."
        )

    def data_updated(self, username: str, data_info: str, request: Request):
        data_info_capitalized = data_info.capitalize().strip()
        client_ip = return_client_ip(request, ENV)
        self._logger.info(
            f"{client_ip} - {data_info_capitalized} for user {username} has been updated."
        )

    def data_deleted(self, username: str, data_info: str, request: Request):
        data_info_capitalized = data_info.capitalize().strip()
        client_ip = return_client_ip(request, ENV)
        self._logger.info(
            f"{client_ip} - {data_info_capitalized} for user {username} has been deleted."
        )


my_logger = MyLogger(env=ENV)
