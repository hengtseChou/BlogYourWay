from flask import Request
from urllib.parse import urlparse
from redis.client import Redis
from application.config import ENV
from application.services.mongo import my_database, MyDatabase
from application.services.redis import my_redis
from application.services.log import return_client_ip
from application.utils.common import get_today

class MetricsRecorderSetup:

    def __init__(self, db_handler: MyDatabase) -> None:
        
        self._db_handler = db_handler

    def _get_referrer(self, request: Request) -> str:

        full_path = request.full_path
        return urlparse(full_path).netloc
    
    def page_viewed(self, username: str, request: Request):

        address = return_client_ip(request, ENV)
        user_agent = request.user_agent

        self._db_handler.user_views.make_increments(
            filter={"username": username}, increments={f"{address}_{user_agent}": 1}, upsert=True
        )
