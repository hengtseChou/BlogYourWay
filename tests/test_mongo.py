from mongomock import MongoClient
from application.services.mongo import MyDatabase, ExtendedCollection

mock_client = MongoClient()


class TestMyDatabase:
    def __init__(self) -> None:
        self.test_db = MyDatabase(mock_client)

    def test_user_login_type(self):
        assert isinstance(self.test_db.user_info, ExtendedCollection)
