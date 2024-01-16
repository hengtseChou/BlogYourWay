from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor

from blogyourway.config import MONGO_URL


class ExtendedCollection:
    def __init__(self, collection: Collection):
        self._col = collection

    def find(self, filter):
        return ExtendedCursor(self._col, filter)

    def insert_one(self, document: dict):
        self._col.insert_one(document)

    def count_documents(self, filter: dict):
        return self._col.count_documents(filter)

    def delete_one(self, filter: dict):
        self._col.delete_one(filter)

    def delete_many(self, filter: dict):
        self._col.delete_many(filter)

    # this application usually does not consider the case where records not found
    def find_one(self, filter) -> dict:
        result = self._col.find_one(filter)
        if result is None:
            return result
        return dict(result)

    def exists(self, key: str, value: str) -> bool:
        """check if the values exists for this key in this collection

        Args:
            key (str): the key to search from
            value (any): the value to look for

        Returns:
            bool: return True if exists
        """
        if self.find_one({key: value}):
            return True
        return False

    def update_one(self, filter, update, upsert=False):
        return self._col.update_one(filter, update, upsert=upsert)

    def update_values(self, filter: dict, update: dict):
        """This method wraps up the pymongo update_one method with "$set" operator.

        Args:
            filter (dict): A query that matches the document to update.
            update (dict): The modified fields. No need to pass "$set".

        """
        return self.update_one(filter=filter, update={"$set": update})

    def make_increments(self, filter: dict, increments: dict, upsert=False):
        """This method wraps up the pymongo update_one method with "$inc" operator.

        Args:
            filter (dict): A query that matches the document to update.
            increments (dict): The values of these fields will be add by the values passed in this argument.

        """
        return self.update_one(filter=filter, update={"$inc": increments}, upsert=upsert)


class ExtendedCursor(Cursor):
    def __init__(self, collection: ExtendedCollection, filter=None):
        super().__init__(collection, filter)

    def __check_okay_to_chain(self):
        return super(ExtendedCursor, self)._Cursor__check_okay_to_chain()

    def sort(self, key_or_list, direction):
        super().sort(key_or_list, direction)
        return self

    def skip(self, skip: int):
        super().skip(skip)
        return self

    def limit(self, limit: int):
        super().limit(limit)
        return self

    def as_list(self):
        self.__check_okay_to_chain()
        return list(self)


###################################################################

# my database handler
# the "interface" for mongo db

###################################################################


class Database:
    def __init__(self, client: MongoClient) -> None:
        self._client = client
        users_db = client["users"]
        posts_db = client["posts"]
        comments_db = client["comments"]
        metrics_db = client["metrics"]

        self._user_creds = ExtendedCollection(users_db["user-creds"])
        self._user_info = ExtendedCollection(users_db["user-info"])
        self._user_about = ExtendedCollection(users_db["user-about"])
        self._post_info = ExtendedCollection(posts_db["post-info"])
        self._post_content = ExtendedCollection(posts_db["post-content"])
        self._comment = ExtendedCollection(comments_db["comment"])
        self._metrics_log = ExtendedCollection(metrics_db["metrics-log"])

    @property
    def client(self):
        return self._client

    @property
    def user_creds(self):
        return self._user_creds

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


client = MongoClient(MONGO_URL, connect=False)
mongodb = Database(client=client)
