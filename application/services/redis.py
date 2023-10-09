import redis
from application.config import REDIS_HOST, REDIS_PORT, REDIS_PW, ENV


if ENV == "develop":
    my_redis = redis.from_url("redis://localhost:6379")
elif ENV == "prod":
    my_redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW)
