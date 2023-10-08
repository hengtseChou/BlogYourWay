"""
This module load enviroment variables (from .env) and let them be accessed by other modules.
"""
import os

from dotenv import load_dotenv

if not load_dotenv():
    raise Exception(".env file not found.")

ENV = os.getenv("ENV")
APP_SECRET = os.getenv("APP_SECRET")
MONGO_URL = os.getenv("MONGO_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PW = os.getenv("REDIS_PW")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET")
