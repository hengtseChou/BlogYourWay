import pymongo
from website.config import MONGO_URL

class Database(object):
    def __init__(self):

        client = pymongo.MongoClient(MONGO_URL, connect=False)
        self.db = client['blog']

    def exists(self, collection, key, value):
        exists = collection.find_one({key: value})
        if exists:
            return True
        return False

class DB_Users(Database):

    def __init__(self):
        super().__init__()
        self.collection = self.db['users']

    def exists(self, key, value):
        return super().exists(self.collection, key, value)
    
    def create_user(self, data):
        
        x = self.collection.insert_one(data)
        return x
    
    def find_via(self, key, value, drop_id=True):

        record = self.collection.find_one({key: value})
        if drop_id:
            del record['_id']
        return record
    
    def update_values(self, username, key, value):
        # pass list to update multiple keys at once
        if isinstance(key, str):
            new_value = {"$set": { key: value}}
            self.collection.update_one({'username': username}, new_value)

        elif isinstance(key, list) and isinstance(value, list):
            new_values = {"$set": {}}
            for i in range(len(key)):
                new_values['$set'][key[i]] = value[i]
            self.collection.update_one({'username': username}, new_values)

class DB_Posts(Database):

    def __init__(self):
        super().__init__()
        self.collection = self.db['posts']

    def new_post(self, new_post):

        self.collection.insert_one(new_post)

    def exists(self, key, value):
        return super().exists(self.collection, key, value)
    






class DB_Comments(Database):

    def __init__(self):
        super().__init__()
        self.collection = self.db['comments']        




db_users = DB_Users()
db_posts = DB_Posts()
db_comments = DB_Comments()