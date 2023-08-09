from datetime import datetime, timedelta
from website.config import ENV
from website.extensions.db_redis import redis_method



def daily_visitor_data(username):

    if ENV == 'debug':
        start_time = datetime.now() - timedelta(days=30)
    elif ENV == 'prod':
        start_time = datetime.now() + timedelta(hours=8) - timedelta(days=30)

    current_time  = start_time

    dates = []
    daily_visitor_count = []

    for i in range(30):

        current_time += timedelta(days=1)
        current_date = current_time.strftime('%Y%m%d')
        count_of_the_day = redis_method.get_count(f"{username}_uv_{current_date}")

        dates.append(current_time.strftime('%Y-%m-%d'))
        daily_visitor_count.append(count_of_the_day)

    data = {'labels': dates, 'data': daily_visitor_count}
    
    return data

def get_visitor_count(username):

    visitor = {}
    visitor['home'] = redis_method.get_count(f"{username}_home")
    visitor['blog'] = redis_method.get_count(f"{username}_blog")
    visitor['about'] = redis_method.get_count(f"{username}_about")
    visitor['total'] = redis_method.get_count_with_prefix(f"{username}_uv")

    return visitor

