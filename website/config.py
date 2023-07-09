from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv('MONGO_URL')
ENV = os.getenv('ENV')