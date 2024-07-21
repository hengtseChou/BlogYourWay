from flask_caching import Cache

from app.helpers.users import user_utils
from app.logging import logger

cache = Cache()


def update_user_cache(cache: Cache, username: str) -> None:

    logger.debug("Updating user cache from cache updater.")
    user = user_utils.get_user_info(username)
    cache.set(username, user)
