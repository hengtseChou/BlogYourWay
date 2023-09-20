from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database
from application.config import MONGO_URL


class ExtendedCollection(Collection):
    def __init__(self, database: Database, name: str, create=False):
        super().__init__(database, name, create)

    def find(self, *args, **kwargs):
        return ExtendedCursor(self, *args, **kwargs)

    def exists(self, key, value):

        if self.find_one({key: value}):
            return True
        return False

    def update_one(self, filter, update):
        return super().update_one(filter, update)

    def simple_update(self, filter, update):

        return self.update_one(filter=filter, update={"$set": update})


class ExtendedCursor(Cursor):
    def __init__(self, collection: ExtendedCollection, filter=None):
        super().__init__(collection, filter)

    def __check_okay_to_chain(self):
        return super(ExtendedCursor, self)._Cursor__check_okay_to_chain()

    def as_list(self):

        self.__check_okay_to_chain()
        return list(self)


###################################################################

# my database handler

###################################################################

class MyDatabase:
    def __init__(self) -> None:
        self._users_db = Database(client=MongoClient(MONGO_URL, connect=False), name="users")
        self._posts_db = Database(client=MongoClient(MONGO_URL, connect=False), name="posts")
        self._comments_db = Database(client=MongoClient(MONGO_URL, connect=False), name="comments")  

        self._user_login = ExtendedCollection(self._users_db, "user-login")
        self._user_info = ExtendedCollection(self._users_db, "user-info")
        self._user_about = ExtendedCollection(self._users_db, "user-about")
        self._post_info = ExtendedCollection(self._posts_db, "post-info")
        self._post_content = ExtendedCollection(self._posts_db, "post-content")
        self._comment = ExtendedCollection(self._comments_db, "comment")
    
    @property
    def user_login(self):
        return self._user_login
    
    @property
    def user_info(self):
        return self._user_info
    
    @property
    def user_about(self):
        return self._user_about
    
    @property
    def post_info(self):
        return self._post_info
    
    @property
    def post_content(self):
        return self._post_content
    
    @property
    def comment(self):
        return self._comment 

my_database = MyDatabase()