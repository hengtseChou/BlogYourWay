import re
from flask import Request
from urllib.parse import urlparse
from application.config import ENV
from application.services.mongo import my_database, MyDatabase
from application.services.log import return_client_ip
from application.utils.common import get_today


class MetricsRecorder:
    def __init__(self, db_handler: MyDatabase) -> None:

        self._db_handler = db_handler

    def _get_referrer(self, request: Request) -> str:

        full_path = request.full_path
        return urlparse(full_path).netloc

    def _extract_username(self, request: Request) -> str:

        url = request.environ["RAW_URI"]
        pattern = r"[@/]([^/]+)"

        match = re.search(pattern, url)
        username = match.group(1)
        return username[1:]

    def _extract_post_uid(self, request: Request):

        url = request.environ["RAW_URI"]
        post_uid = url.split("/")[-1]
        return post_uid

    def page_viewed(self, request: Request) -> dict:
        """Pass a temporily result for child classes to insert of update values when a page is visited.

        Args:
        - request (flask.Request): The incoming request to be parsed.
        """
        username = self._extract_username(request)
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent
        key = f"{address}_{user_agent}"
        today = get_today(ENV)

        mid_result = {"username": username, "log_key": key, "today": today}
        return mid_result

    def index_page_viewed(self, request: Request) -> dict:
        """Pass a temporily result for child classes to insert of update values when an index page is visited.

        Args:
        - request (flask.Request): The incoming request to be parsed.
        """
        username = self._extract_username(request)
        page = request.path
        today = get_today(ENV)

        mid_result = {"username": username, "page": page, "today": today}
        return mid_result


class LifeTimeMetricRecorder(MetricsRecorder):
    def __init__(self, db_handler: MyDatabase) -> None:
        super().__init__(db_handler)

    def page_viewed(self, request: Request):
        """Record total pv and total uv for user."""

        mid_result = super().page_viewed(request)
        self._db_handler.user_views.make_increments(
            filter={
                "username": mid_result["username"],
                "unique-visitors.key": mid_result["key"],
            },
            increments={"unique-visitors.value": 1},
            upsert=True,
        )


class TimelyMetricRecorder(MetricsRecorder):
    def __init__(self, db_handler: MyDatabase) -> None:
        super().__init__(db_handler)

    def page_viewed(self, request: Request):
        """Record which user has been visited, as we want to track the overall traffic."""

        mid_result = super().page_viewed(request)
        self._db_handler.metrics_log.insert_one(
            {
                "username": mid_result["username"],
                "type": "site_traffic",
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )

    def index_page_viewed(self, request: Request):
        """Record that an index page has been visited, as we want to track index pages' traffic."""

        mid_result = super().index_page_viewed(request)
        self._db_handler.metrics_log.insert_one(
            {
                "username": mid_result["username"],
                "type": "index_page_traffic",
                "page": mid_result["page"],
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )


lifetime_metrics = LifeTimeMetricRecorder(my_database)
timely_metrics = TimelyMetricRecorder(my_database)
