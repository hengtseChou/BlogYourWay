from redis import Redis

from application.config import REDIS_HOST, REDIS_PORT, REDIS_PW

my_redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW)
