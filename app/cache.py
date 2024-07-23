from flask_caching import Cache

from app.helpers.users import user_utils
from app.logging import logger

cache = Cache()


def update_user_cache(cache: Cache, username: str) -> None:
    """Update the cache with user information.

    This function fetches user information using the `user_utils.get_user_info`
    function and updates the cache with the fetched data.

    Args:
        cache (Cache): The cache instance to update.
        username (str): The username for which to update the cache.

    Returns:
        None
    """
    logger.debug("Updating user cache from cache updater.")
    user = user_utils.get_user_info(username)
    cache.set(username, user)
