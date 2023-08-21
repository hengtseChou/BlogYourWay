from redis import Redis
from datetime import datetime, timedelta
from functools import lru_cache
from website.config import REDIS_HOST, REDIS_PORT, REDIS_PW
from website.blog.utils import get_today


class Redis_method:
    def __init__(self):
        self.r = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW)

    def increment_count(self, key, request):
        # f"post_uid_{post.uid}"
        # f"{username}_{page}" as in home, blog, about
        # f"{username}_tag: {tag}""
        # f"{username}_uv_{date}" as in unique visitor for each user
        # f"landing_page_{date}""

        host = request.remote_addr
        ua = request.headers.get("User-Agent")

        hit_value = f"{host}_{ua}"

        self.r.pfadd(key, hit_value)

    def get_count(self, key):

        return self.r.pfcount(key)
    
    def get_counts(self, keys):

        return [self.r.pfcount(key) for key in keys]
    
    @lru_cache(maxsize=None)  # Caching to optimize repeated calls
    def get_daily_visitor_data(self, username):


        start_time = get_today() - timedelta(days=30)

        keys = []
        dates = []
        daily_visitor_count = []

        for i in range(1, 31):
            keys.append(f"{username}_uv_{(start_time + timedelta(days=i)).strftime('%Y%m%d')}")
            dates.append((start_time + timedelta(days=i)).strftime('%Y-%m-%d'))   

        daily_visitor_count = self.get_counts(keys)
        data = {'labels': dates, 'data': daily_visitor_count}
        return data
    
    def get_visitor_stats(self, username):

        data = {}
        for page in ['home', 'blog', 'portfolio', 'about']:
            data[page] = self.get_count(f"{username}_{page}")
        total = 0
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.r.scan(cursor, match=f"{username}_uv_*", count=1000)  # Adjust count as needed
            total += sum(self.get_counts(keys))
        data['total'] = total

        return data

    
    def remove_all(self, user):
        pass


redis_method = Redis_method()
