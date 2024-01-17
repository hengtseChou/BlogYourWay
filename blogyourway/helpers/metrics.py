import re
from urllib.parse import urlparse

from flask import Request

from blogyourway.config import ENV
from blogyourway.services.logging import return_client_ip
from blogyourway.services.mongo import Database, mongodb
from blogyourway.helpers.common import get_today


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
