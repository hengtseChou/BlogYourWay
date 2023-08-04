from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
ENV = os.getenv("ENV")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PW = os.getenv("REDIS_PW")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET")
