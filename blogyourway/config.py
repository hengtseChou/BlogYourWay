"""
This module load enviroment variables (from .env) and let them be accessed by other modules.
"""

import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV")
APP_SECRET = os.getenv("APP_SECRET")
MONGO_URL = os.getenv("MONGO_URL")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET")
