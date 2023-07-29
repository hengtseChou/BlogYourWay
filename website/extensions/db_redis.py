from redis import Redis
from website.config import REDIS_HOST, REDIS_PORT, REDIS_PW

r = Redis(
    host = REDIS_HOST, 
    port = REDIS_PORT, 
    password = REDIS_PW
)

class Redis_method:

    def __init__(self):
        self.r = Redis(
            host = REDIS_HOST, 
            port = REDIS_PORT, 
            password = REDIS_PW
        )

    def increment_count(self, key, request):

        # f"post_id_{post.uid}"
        # f"{username}_{page}"

        host = request.remote_addr
        ua = request.headers.get('User-Agent')

        hit_value = f"{host}_{ua}"

        self.r.pfadd(key, hit_value)

    def get_count(self, key):

        return self.r.pfcount(key)
    

redis_method = Redis_method()