import redis as r

from blogyourway.config import REDIS_HOST, REDIS_PORT, REDIS_PW

redis = r.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PW)
