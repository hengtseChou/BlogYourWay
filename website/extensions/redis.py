from redis import Redis
from datetime import timedelta
from functools import lru_cache
from website.config import REDIS_HOST, REDIS_PORT, REDIS_PW
from website.blog.utils import get_today


class Redis_method:
    
    def __init__(self):
        self.r = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW)

    def increment_count(self, key, request):
        # f"post_uid_{post.post_uid}"
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
    
    @lru_cache(maxsize=None)  # Caching to optimize repeated calls
    def get_daily_visitor_data(self, username):


        start_time = get_today() - timedelta(days=30)

        keys = []
        dates = []
        daily_visitor_count = []

        for i in range(1, 31):
            keys.append(f"{username}_uv_{(start_time + timedelta(days=i)).strftime('%Y%m%d')}")
            dates.append((start_time + timedelta(days=i)).strftime('%Y-%m-%d'))   

        daily_visitor_count = [self.get_count(key) for key in keys]
        data = {'labels': dates, 'data': daily_visitor_count}
        return data
    
    def get_visitor_stats(self, username):

        data = {}
        for view in ['home', 'blog', 'portfolio', 'about']:
            data[view] = self.get_count(f"{username}_{view}")
        
        total = 0
        for key in self.r.scan_iter(f"{username}_uv_*"):
            total += self.get_count(key)        
        data['total'] = total

        return data

    
    def delete(self, key):
        
        self.r.delete(key)

    def delete_with_prefix(self, prefix):

        for key in self.r.scan_iter(f"{prefix}*"):
            self.r.delete(key)


redis_method = Redis_method()
