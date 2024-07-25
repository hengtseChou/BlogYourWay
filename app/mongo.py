from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from typing_extensions import Self

from app.config import MONGO_URL


class ExtendedCollection:
    def __init__(self, collection: Collection) -> None:
        """Initialize the ExtendedCollection with a MongoDB collection.

        Args:
            collection (Collection): The MongoDB collection instance.
        """
        self._col = collection

    def find(self, filter: Dict[str, Any]) -> "ExtendedCursor":
        """Find documents in the collection based on a filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.

        Returns:
            ExtendedCursor: Custom cursor for further operations.
        """
        return ExtendedCursor(self._col, filter)

    def insert_one(self, document: Dict[str, Any]) -> None:
        """Insert a single document into the collection.

        Args:
            document (Dict[str, Any]): The document to insert.
        """
        self._col.insert_one(document)

    def count_documents(self, filter: Dict[str, Any]) -> int:
        """Count documents in the collection matching the filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.

        Returns:
            int: The count of matching documents.
        """
        return self._col.count_documents(filter)

    def delete_one(self, filter: Dict[str, Any]) -> None:
        """Delete a single document matching the filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.
        """
        self._col.delete_one(filter)

    def delete_many(self, filter: Dict[str, Any]) -> None:
        """Delete multiple documents matching the filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.
        """
        self._col.delete_many(filter)

    def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.

        Returns:
            Optional[Dict[str, Any]]: The found document or None if not found.
        """
        result = self._col.find_one(filter)
        return dict(result) if result else None

    def exists(self, key: str, value: Any) -> bool:
        """Check if a value exists for a given key in the collection.

        Args:
            key (str): The key to search for.
            value (Any): The value to look for.

        Returns:
            bool: True if the value exists, False otherwise.
        """
        return self.find_one({key: value}) is not None

    def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Any], upsert: bool = False
    ) -> None:
        """Update a single document matching the filter.

        Args:
            filter (Dict[str, Any]): The filter criteria.
            update (Dict[str, Any]): The update operations.
            upsert (bool): If True, create a new document if no document matches the filter.
        """
        self._col.update_one(filter, update, upsert=upsert)

    def update_values(self, filter: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Update fields in a document using the $set operator.

        Args:
            filter (Dict[str, Any]): The filter criteria.
            update (Dict[str, Any]): The fields to update.
        """
        self.update_one(filter=filter, update={"$set": update})

    def make_increments(
        self, filter: Dict[str, Any], increments: Dict[str, int], upsert: bool = False
    ) -> None:
        """Increment fields in a document using the $inc operator.

        Args:
            filter (Dict[str, Any]): The filter criteria.
            increments (Dict[str, int]): The fields to increment.
            upsert (bool): If True, create a new document if no document matches the filter.
        """
        self.update_one(filter=filter, update={"$inc": increments}, upsert=upsert)


class ExtendedCursor(Cursor):
    def __init__(self, collection: ExtendedCollection, filter: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the ExtendedCursor with a MongoDB collection and filter.

        Args:
            collection (Collection): The MongoDB collection instance.
            filter (Optional[Dict[str, Any]]): The filter criteria, if any.
        """
        super().__init__(collection, filter)

    def sort(self, key_or_list: Any, direction: int) -> Self:
        """Sort the cursor results.

        Args:
            key_or_list (Any): The key or list of keys to sort by.
            direction (int): The sort direction (1 for ascending, -1 for descending).

        Returns:
            ExtendedCursor: Self for method chaining.
        """
        super().sort(key_or_list, direction)
        return self

    def skip(self, skip: int) -> Self:
        """Skip a number of documents in the cursor.

        Args:
            skip (int): The number of documents to skip.

        Returns:
            ExtendedCursor: Self for method chaining.
        """
        super().skip(skip)
        return self

    def limit(self, limit: int) -> Self:
        """Limit the number of documents in the cursor.

        Args:
            limit (int): The maximum number of documents to return.

        Returns:
            ExtendedCursor: Self for method chaining.
        """
        super().limit(limit)
        return self

    def as_list(self) -> List[Dict[str, Any]]:
        """Convert the cursor to a list of documents.

        Returns:
            List[Dict[str, Any]]: List of documents from the cursor.
        """
        self.__check_okay_to_chain()
        return list(self)
    
    def __check_okay_to_chain(self) -> None:
        """Check if chaining operations is allowed."""
        return super(ExtendedCursor, self)._Cursor__check_okay_to_chain()


class Database:
    def __init__(self, client: MongoClient) -> None:
        """Initialize the Database object with MongoDB client.

        Args:
            client (MongoClient): The MongoDB client instance.
        """
        self._client = client
        users_db = client["users"]
        posts_db = client["posts"]
        comments_db = client["comments"]
        project_db = client["projects"]
        changelog_db = client["changelog"]

        self._user_creds = ExtendedCollection(users_db["user-creds"])
        self._user_info = ExtendedCollection(users_db["user-info"])
        self._user_about = ExtendedCollection(users_db["user-about"])
        self._post_info = ExtendedCollection(posts_db["posts-info"])
        self._post_content = ExtendedCollection(posts_db["posts-content"])
        self._comment = ExtendedCollection(comments_db["comment"])
        self._project_info = ExtendedCollection(project_db["project-info"])
        self._project_content = ExtendedCollection(project_db["project-content"])
        self._changelog = ExtendedCollection(changelog_db["changelog-entry"])

    @property
    def client(self) -> MongoClient:
        """Get the MongoDB client instance.

        Returns:
            MongoClient: The MongoDB client instance.
        """
        return self._client

    @property
    def user_creds(self) -> ExtendedCollection:
        """Get the ExtendedCollection for user credentials.

        Returns:
            ExtendedCollection: The collection for user credentials.
        """
        return self._user_creds

    @property
    def user_info(self) -> ExtendedCollection:
        """Get the ExtendedCollection for user information.

        Returns:
            ExtendedCollection: The collection for user information.
        """
        return self._user_info

    @property
    def user_about(self) -> ExtendedCollection:
        """Get the ExtendedCollection for user about information.

        Returns:
            ExtendedCollection: The collection for user about information.
        """
        return self._user_about

    @property
    def post_info(self) -> ExtendedCollection:
        """Get the ExtendedCollection for post information.

        Returns:
            ExtendedCollection: The collection for post information.
        """
        return self._post_info

    @property
    def post_content(self) -> ExtendedCollection:
        """Get the ExtendedCollection for post content.

        Returns:
            ExtendedCollection: The collection for post content.
        """
        return self._post_content

    @property
    def comment(self) -> ExtendedCollection:
        """Get the ExtendedCollection for comments.

        Returns:
            ExtendedCollection: The collection for comments.
        """
        return self._comment

    @property
    def project_info(self) -> ExtendedCollection:
        """Get the ExtendedCollection for project information.

        Returns:
            ExtendedCollection: The collection for project information.
        """
        return self._project_info

    @property
    def project_content(self) -> ExtendedCollection:
        """Get the ExtendedCollection for project content.

        Returns:
            ExtendedCollection: The collection for project content.
        """
        return self._project_content
    
    @property
    def changelog(self) -> ExtendedCollection:
        return self._changelog


client = MongoClient(MONGO_URL, connect=False)
mongodb = Database(client=client)
