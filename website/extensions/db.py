import pymongo
from website.config import MONGO_URL

class Database(object):
    def __init__(self):

        client = pymongo.MongoClient(MONGO_URL, connect=False)
        self.db = client['blog']

class DB_Users(Database):

    def __init__(self):
        super().__init__()
        self.collection = self.db['users']

    def exists(self, key, value):

        exists = self.collection.find_one({key: value})
        if exists:
            return True
        return False
    
    def create_user(self, data):
        
        x = self.collection.insert_one(data)
        return x

class DB_Posts(Database):

    def __init__(self):
        super().__init__()
        self.collections = self.db['posts']



db_users = DB_Users()
db_posts = DB_Posts()