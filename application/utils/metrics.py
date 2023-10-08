import re
from urllib.parse import urlparse

from flask import Request

from application.config import ENV
from application.services.log import return_client_ip
from application.services.mongo import MyDatabase, my_database
from application.utils.common import get_today


def _get_referrer(request: Request) -> str:
    full_path = request.full_path
    return urlparse(full_path).netloc


def _extract_username(request: Request) -> str:
    url = request.environ["RAW_URI"]
    pattern = r"[@/]([^/]+)"

    match = re.search(pattern, url)
    username = match.group(1)
    return username[1:]


def _extract_post_uid(request: Request):
    url = request.environ["RAW_URI"]
    post_uid = url.split("/")[-1]
    return post_uid


class MetricsRecorder:
    def __init__(self, db_handler: MyDatabase) -> None:
        self._db_handler = db_handler

    def page_viewed(self, request: Request) -> dict:
        """Data prep. for metric recorders to insert of update values when a page is visited.

        Args:
        - request (flask.Request): The incoming request to be parsed.

        Returns:
        - username, address, user_agent, today
        """
        username = _extract_username(request)
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)

        mid_result = {
            "username": username,
            "address": address,
            "user_agent": user_agent,
            "today": today,
        }
        return mid_result

    def index_page_viewed(self, request: Request) -> dict:
        """Data prep. for metric recorders to insert of update values when an index page is visited.

        Args:
        - request (flask.Request): The incoming request to be parsed.

        Returns:
        - username, path (of index page), address, user_agent, today
        """
        username = _extract_username(request)
        page = request.path
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)

        mid_result = {
            "username": username,
            "page": page,
            "address": address,
            "user_agent": user_agent,
            "today": today,
        }
        return mid_result

    def post_viewed(self, request: Request) -> dict:
        """Data prep. for metric recorders to update values when a post is viewed.

        Args:
            request (Request): _description_

        Returns:
            dict: _description_
        """
        username = _extract_username(request)
        post_uid = _extract_post_uid(request)
        referrer = _get_referrer(request)
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)

        mid_result = {
            "username": username,
            "post_uid": post_uid,
            "referrer": referrer,
            "address": address,
            "user_agent": user_agent,
            "today": today,
        }
        return mid_result

    def post_read(self, request: Request) -> dict:
        post_uid = request.args.get("post_uid", type=str)
        target_post = self._db_handler.post_info.find_one({"post_uid": post_uid})
        username = target_post.get("author")

        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)

        mid_result = {
            "username": username,
            "post_uid": post_uid,
            "address": address,
            "user_agent": user_agent,
            "today": today,
        }
        return mid_result

    def social_link_fired(self, request: Request):
        username = _extract_username
        user = my_database.user_info.find_one({"username": username})
        link_idx = request.args.get("idx", type=int)
        platform = user["social_links"][link_idx - 1]["platform"]
        url = user["social_links"][link_idx - 1]["url"]
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)

        mid_result = {
            "username": username,
            "platform": platform,
            "url": url,
            "address": address,
            "user_agent": user_agent,
            "today": today,
        }
        return mid_result


class LifeTimeMetricRecorder(MetricsRecorder):
    """Lifetime recorder will make increment to user or post themselves."""

    def __init__(self, db_handler: MyDatabase) -> None:
        super().__init__(db_handler)

    def page_viewed(self, request: Request):
        """Record total pv and total uv for user.

        This should be called whenever any page under an user is visited.
        """

        mid_result = super().page_viewed(request)
        self._db_handler.user_views.make_increments(
            filter={
                "username": mid_result["username"],
                "unique-visitor": f"{mid_result['address']}_{mid_result['user_agent']}",
            },
            increments={"count": 1},
            upsert=True,
        )

    def post_viewed(self, request: Request):
        mid_result = super().post_viewed(request)
        if not mid_result["referrer"]:
            mid_result["referrer"] = "internal"
        self._db_handler.post_info.make_increments(
            filter={"post_uid": mid_result["post_uid"]}, increments={"views": 1}
        )
        self._db_handler.post_view_sources.make_increments(
            filter={"post_uid": mid_result["post_uid"], "referrer": mid_result["referrer"]},
            increments={"count": 1},
            upsert=True,
        )

    def post_read(self, request: Request) -> dict:
        mid_result = super().post_read(request)
        self._db_handler.post_info.make_increments(
            filter={"post_uid": mid_result["post_uid"]}, increments={"reads": 1}
        )


class TimelyMetricRecorder(MetricsRecorder):
    """Timely recorder will add log to the metric log database."""

    def __init__(self, db_handler: MyDatabase) -> None:
        super().__init__(db_handler)

    def page_viewed(self, request: Request):
        """Record which user has been visited, as we want to track the overall traffic.

        This should be called whenever any page under an user is visited.
        """

        mid_result = super().page_viewed(request)
        self._db_handler.metrics_log.insert_one(
            {
                "username": mid_result["username"],
                "type": "site_traffic",
                "address": mid_result["address"],
                "user_agent": mid_result["user_agent"],
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
                "address": mid_result["address"],
                "user_agent": mid_result["user_agent"],
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )

    def post_viewed(self, request: Request):
        mid_result = super().post_viewed(request)
        self._db_handler.metrics_log.insert_one(
            {
                "post_uid": mid_result["post_uid"],
                "type": "post_view",
                "username": mid_result["username"],
                "address": mid_result["address"],
                "user_agent": mid_result["user_agent"],
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )

    def post_read(self, request: Request):
        mid_result = super().post_read(request)
        self._db_handler.metrics_log.insert_one(
            {
                "post_uid": mid_result["post_uid"],
                "type": "post_read",
                "username": mid_result["username"],
                "address": mid_result["address"],
                "user_agent": mid_result["user_agent"],
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )

    def social_link_fired(self, request: Request):
        mid_result = super().social_link_fired(request)
        self._db_handler.metrics_log.insert_one(
            {
                "username": mid_result["username"],
                "type": "social_links_track",
                "platform": mid_result["platform"],
                "url": mid_result["url"],
                "address": mid_result["address"],
                "user_agent": mid_result["user_agent"],
                "timestamp": mid_result["today"],
                "timestamp_str": mid_result["today"].strftime("%Y-%m-%d"),
            }
        )


class AdminMetricsRedorder(MetricsRecorder):
    def __init__(self, db_handler: MyDatabase) -> None:
        super().__init__(db_handler)

    def page_viewed(self, request: Request, page: str):
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent.string
        today = get_today(ENV)
        self._db_handler.metrics_log.insert_one(
            {
                "type": "administration",
                "page": page,
                "address": address,
                "user_agent": user_agent,
                "timestamp": today,
                "timestamp_str": today.strftime("%Y-%m-%d"),
            }
        )


lifetime_metrics = LifeTimeMetricRecorder(my_database)
timely_metrics = TimelyMetricRecorder(my_database)
admin_metrics = AdminMetricsRedorder(my_database)
