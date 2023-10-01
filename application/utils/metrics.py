import re
from flask import Request
from urllib.parse import urlparse
from application.config import ENV
from application.services.mongo import my_database, MyDatabase
from application.services.log import return_client_ip
from application.utils.common import get_today


class MetricsRecorderSetup:
    def __init__(self, db_handler: MyDatabase) -> None:

        self._db_handler = db_handler

    def _get_referrer(self, request: Request) -> str:

        full_path = request.full_path
        return urlparse(full_path).netloc
    
    def _extract_username(self, request: Request) -> str:

        url = request.environ["RAW_URI"]
        pattern = r'[@/]([^/]+)'

        # Use re.search to find the match
        match = re.search(pattern, url)

        # Check if a match was found
        if match:
            username = match.group(1)
            return username[1:]
        else:
            return None

    def page_viewed(self, request: Request):
        """When this function is called, it does: 
        
        1. Add counts for total pv and total uv. 

        2. Add a log with timestamp for calculating monthly site traffic.

        Args:
            username (str): _description_
            request (Request): _description_
        """
        username = self._extract_username(request)
        address = return_client_ip(request, ENV)
        user_agent = request.user_agent
        key = f"{address}_{user_agent}"
        today = get_today(ENV)

        self._db_handler.user_views.make_increments(
            filter={"username": username, "unique-visitors.key": key},
            increments={"unique-visitors.value": 1},
            upsert=True,
        )
        self._db_handler.metrics_log.insert_one({
            "username": username, 
            "type": "site_traffic", 
            "timestamp": today, 
            "timestamp_str": today.strftime("%Y-%m-%d")
        })

    def track_index_pageviews(self, request: Request):
        """When this function is called, it does:

        1. Add a log with timestamp for calculating monthly index page traffic.

        Index pages are home, blog, about, (portfolio, changelog).

        Args:
            username (str): a string for user that was visited.
            page (str): a string to specify which page was visited.
        """
        username = self._extract_username(request)
        page = request.path
        today = get_today(ENV)
        self._db_handler.metrics_log.insert_one({
            "username": username,
            "type": "index_page_traffic", 
            "page": page,
            "timestamp": today, 
            "timestamp_str": today.strftime("%Y-%m-%d")
        })


metrics_recorder = MetricsRecorderSetup(my_database)
