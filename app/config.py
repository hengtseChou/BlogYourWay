import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

# Environment variables
ENV: str = os.getenv("ENV")  # Environment mode (dev or prod)
DOMAIN: str = os.getenv("DOMAIN")  # Website domain
APP_SECRET: str = os.getenv("APP_SECRET")  # Application secret key
MONGO_URL: str = os.getenv("MONGO_URL")  # MongoDB connection URL
RECAPTCHA_KEY: str = os.getenv("RECAPTCHA_KEY")  # reCAPTCHA public key
RECAPTCHA_SECRET: str = os.getenv("RECAPTCHA_SECRET")  # reCAPTCHA secret key
REDISHOST: str = os.getenv("REDISHOST")
REDISPORT: str = os.getenv("REDISPORT")
REDIS_URL: str = os.getenv("REDIS_URL")

# Application settings
TEMPLATE_FOLDER: pathlib.Path = (pathlib.Path(__file__).parent / "template").resolve()
CACHE_TIMEOUT: int = 5 * 60  # Cache timeout in seconds (5 minutes)
