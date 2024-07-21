"""
This module load enviroment variables (from .env) and let them be accessed by other modules.
"""

import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV")  # debug or prod
APP_SECRET = os.getenv("APP_SECRET")
MONGO_URL = os.getenv("MONGO_URL")
RECAPTCHA_KEY = os.getenv("RECAPTCHA_KEY")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET")

TEMPLATE_FOLDER = (pathlib.Path(__file__).parent / "template").resolve()
CACHE_TIMEOUT = 5 * 60
