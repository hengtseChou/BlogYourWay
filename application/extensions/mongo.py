from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from application.config import MONGO_URL


class Client:

    def __init__(self):
        self.client = MongoClient(MONGO_URL, connect=False)

class Database(Client):

    def __init__(self, database):
        super().__init__()
        self.db = self.client[database]

class Custom_Collection(Collection):

    def __init__(self, database: Database, name: str, create=False):
        super().__init__(database, name, create)



class DB_Users(Database):
    def __init__(self):
        super().__init__(database='users')
        # collections
        self.login = Collection(self.db, 'user-login')
        self.info = self.db["user-info"]
        self.about = self.db["user-about"]

    def exists(self, key, value):
        if key in ["email", "username"]:
            if self.login.find_one({key: value}):
                return True
            return False

        elif key in ["blogname"]:
            if self.info.find_one({key: value}):
                return True
            return False


class DB_Posts(Database):
    def __init__(self):
        super().__init__()
        self.db = self.client["posts"]
        # collections
        self.content = self.db["post-content"]
        self.info = self.db["post-info"]

    def exists(self, key, value):
        if key in ["author", "post_uid"]:
            if self.info.find_one({key: value}):
                return True
            return False


class DB_Comments(Database):
    def __init__(self):
        super().__init__()
        self.db = self.client["comments"]
        # collections
        self.comment = self.db["comment"]

    def exists(self, key, value):
        if self.comment.find_one({key: value}):
            return True
        return False


db_users = DB_Users()
db_posts = DB_Posts()
db_comments = DB_Comments()
