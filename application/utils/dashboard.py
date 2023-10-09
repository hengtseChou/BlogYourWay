from datetime import timedelta

from application.config import ENV
from application.utils.common import get_today


def joined_for(user: dict) -> str:
    """Use the user_info dict to calculate how long this user has joined."""
    today = get_today(ENV)
    days_difference = today - user["created_at"]
    return format(days_difference.days + 1, ",")


def last_30_days_label():
    labels = []
    today = get_today(ENV)
    timestamp = today - timedelta(days=30)
    for i in range(30):
        timestamp = timestamp + timedelta(days=1)
        labels.append()
