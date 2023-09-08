from markdown import Markdown
from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database
from application.config import MONGO_URL

class Extended_Mongo_Collection(Collection):

    def __init__(self, database: Database, name: str, create= False):
        super().__init__(database, name, create)

    def find(self, *args, **kwargs):
        return Extended_Mongo_Cursor(self, *args, **kwargs)

    def exists(self, key, value):

        if self.find_one({key: value}):
            return True
        return False
    
    def update_one(self, filter, update):
        return super().update_one(filter, update)
    
    def simple_update(self, filter, update):

        return self.update_one(
            filter=filter,
            update={"$set": update}
        )
    
class Extended_Mongo_Cursor(Cursor):

    def __init__(self, collection: Extended_Mongo_Collection, filter=None):        
        super().__init__(collection, filter)

    def __check_okay_to_chain(self):
        return super(Extended_Mongo_Cursor, self)._Cursor__check_okay_to_chain()  

    def as_list(self):

        self.__check_okay_to_chain()
        return list(self)

###################################################################

# DB objects

###################################################################

class DB_Users:

    def __init__(self):

        self.db = Database(
            client=MongoClient(MONGO_URL, connect=False), 
            name='users'
        )
        # collections
        self.login = Extended_Mongo_Collection(self.db, 'user-login')
        self.info = Extended_Mongo_Collection(self.db, 'user-info')
        self.about = Extended_Mongo_Collection(self.db, 'user-about')


class DB_Posts:

    def __init__(self):

        self.db = Database(
            client=MongoClient(MONGO_URL, connect=False), 
            name='posts'
        )
        # collections
        self.info = Extended_Mongo_Collection(self.db, 'post-info')
        self.content = Extended_Mongo_Collection(self.db, 'post-content')

    def find_featured_posts_info(self, username: str):

        result = (
            db_posts.info
            .find({"author": username, "featured": True, "archived": False})
            .sort("created_at", -1)
            .limit(10)
            .as_list()
        )
        return result
    
    def find_all_posts_info(self, username: str):

        result = (
            db_posts.info
            .find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result
    
    def find_all_archived_posts_info(self, username: str):

        result = (
            db_posts.info
            .find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result
    
    def get_full_post(self, post_uid: str):

        target_post = self.info.find_one({"post_uid": post_uid})
        target_post_content = self.content.find_one({"post_uid": post_uid})["content"]
        target_post['content'] = target_post_content

        return target_post

    
    def find_posts_with_pagination(self, username: str, page_number: int, posts_per_page: int):

        if page_number == 1: 

            result = (
                db_posts.info
                .find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(posts_per_page)
                .as_list()
            ) 
               
        elif page_number > 1:

            result = (
                db_posts.info
                .find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * posts_per_page)
                .limit(posts_per_page)
                .as_list()
            )

        return result






class DB_Comments:

    def __init__(self):

        self.db = Database(
            client=MongoClient(MONGO_URL, connect=False),
            name='comments'
        )
        # collections
        self.comment = Extended_Mongo_Collection(self.db, 'comment')

    def find_comments_by_post_uid(self, post_uid: str):

        result = (
            self.comment
            .find({"post_uid": post_uid})
            .sort("created_at", 1)
            .as_list()
        )
        return result


db_users = DB_Users()
db_posts = DB_Posts()
db_comments = DB_Comments()
