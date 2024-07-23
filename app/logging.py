import logging
from typing import Optional

from flask import Request

from app.config import ENV


def return_client_ip(request: Request, env: str) -> Optional[str]:
    """Returns the client's IP address based on the environment.

    Args:
        request (Request): The Flask request object.
        env (str): The environment in which the application is running. Can be "debug" or "prod".

    Returns:
        Optional[str]: The client's IP address or None if not found.
    """
    if env == "debug":
        return request.remote_addr
    elif env == "prod":
        return request.headers.get("X-Forwarded-For")
    return None


def _setup_prod_logger() -> logging.Logger:
    """Sets up the production logger.

    Returns:
        logging.Logger: Configured production logger.
    """
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


def _setup_dev_logger() -> logging.Logger:
    """Sets up the development logger.

    Returns:
        logging.Logger: Configured development logger.
    """
    # To stop showing CLF in the logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.ERROR)

    stream_formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)s: %(message)s")
    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s in %(funcName)s, %(module)s: %(message)s"
    )

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

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
    def __init__(self, env: str) -> None:
        """Initializes the logger instance based on the current environment.

        Args:
            env (str): The environment in which the application is running. Possible values: "debug", "prod".
        """
        if env == "prod":
            self._logger = _setup_prod_logger()
        elif env == "dev":
            self._logger = _setup_dev_logger()
        else:
            raise ValueError("Invalid environment specified. Use 'dev' or 'prod'.")

    def debug(self, msg: str) -> None:
        """Logs a debug message.

        Args:
            msg (str): The message to log.
        """
        self._logger.debug(msg)

    def info(self, msg: str) -> None:
        """Logs an informational message.

        Args:
            msg (str): The message to log.
        """
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        """Logs a warning message.

        Args:
            msg (str): The message to log.
        """
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        """Logs an error message.

        Args:
            msg (str): The message to log.
        """
        self._logger.error(msg)


class LoggerUtils:
    def __init__(self, logger: logging.Logger) -> None:
        """Initializes LoggerUtils with a logger instance.

        Args:
            logger (logging.Logger): The logger instance to use.
        """
        self._logger = logger

    def page_visited(self, request: Request) -> None:
        """Logs a page visit event.

        Args:
            request (Request): The Flask request object.
        """
        client_ip = return_client_ip(request, ENV)
        page_url = request.environ.get("RAW_URI", "unknown")
        self._logger.debug(f"{client_ip} - {page_url} was visited.")

    def login_failed(self, request: Request, msg: str) -> None:
        """Logs a failed login attempt.

        Args:
            request (Request): The Flask request object.
            msg (str): The failure message.
        """
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Login failed. Msg: {msg}.")

    def login_succeeded(self, request: Request, username: str) -> None:
        """Logs a successful login event.

        Args:
            request (Request): The Flask request object.
            username (str): The username of the logged-in user.
        """
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has logged in.")

    def logout(self, request: Request, username: str) -> None:
        """Logs a user logout event.

        Args:
            request (Request): The Flask request object.
            username (str): The username of the logged-out user.
        """
        client_ip = return_client_ip(request, ENV)
        self._logger.info(f"{client_ip} - User {username} has logged out.")

    def registration_failed(self, request: Request, msg: str) -> None:
        """Logs a failed registration attempt.

        Args:
            request (Request): The Flask request object.
            msg (str): The failure message.
        """
        msg = msg.strip().strip(".")
        client_ip = return_client_ip(request, ENV)
        self._logger.debug(f"{client_ip} - Registration failed. Msg: {msg}.")

    def registration_succeeded(self, username: str) -> None:
        """Logs a successful registration event.

        Args:
            username (str): The username of the newly created user.
        """
        self._logger.info(f"New user {username} has been created.")

    def backstage(self, username: str, panel: str) -> None:
        """Logs a user switching to a different panel.

        Args:
            username (str): The username of the user.
            panel (str): The name of the panel the user switched to.
        """
        self._logger.debug(f"User {username} switched to {panel} panel.")

    def pagination(self, panel: str, num: int) -> None:
        """Logs pagination events.

        Args:
            panel (str): The name of the panel being paginated.
            num (int): Number of records shown.
        """
        self._logger.debug(f"Showing {num} records at {panel} panel.")


logger = Logger(env=ENV)
logger_utils = LoggerUtils(logger)
