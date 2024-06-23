import logging

from flask import Request

from blogyourway.config import ENV


def return_client_ip(request: Request, env: str):
    if env == "debug":
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


class Logger:
    def __init__(self, env: str):
        """Initialize the my logger instance based on the current enviroment.

        Args:
            env (str): Specify the developement enviroment. Possible values: debug, prod.
        """

        if env == "prod":
            self._logger = _setup_prod_logger()
        elif env == "debug":
            self._logger = _setup_debug_logger()

    def debug(self, msg):
        self._logger.debug(msg)

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)


class LoggerUtils:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def page_visited(self, request: Request):
        client_ip = return_client_ip(request, ENV)
        page_url = request.environ.get("RAW_URI")
        self._logger.debug(f"{client_ip} - {page_url} was visited.")

    def login_failed(self, request: Request, msg: str):
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Login failed. Msg: {msg}. ")

    def login_succeeded(self, request: Request, username: str):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has logged in. ")

    def logout(self, request: Request, username: str):
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has logged out.")

    def registration_failed(self, request: Request, msg: str):
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Registration failed. Msg: {msg}. ")

    def registration_succeeded(self, request: Request):
        regist_form = request.form.to_dict()
        username = regist_form.get("username")
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - New user {username} has been created. ")

    def backstage(self, username: str, tab: str):
        self._logger.debug(f"User {username} switched to {tab} tab.")

    def pagination(self, tab: str, num_of_posts: int):
        self._logger.debug(f"Showing {num_of_posts} posts at {tab} tab.")


logger = Logger(env=ENV)
logger_utils = LoggerUtils(logger)
