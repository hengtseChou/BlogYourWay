from mongomock import MongoClient
from application.services.mongo import MyDatabase, ExtendedCollection, ExtendedCursor

mock_client = MongoClient()


class TestMyDatabase:
    test_db = MyDatabase(mock_client)

    def test_user_login_type(self):
        assert isinstance(self.test_db.user_login, ExtendedCollection)

    def test_user_info_type(self):
        assert isinstance(self.test_db.user_info, ExtendedCollection)


class TestExtendedCollection:
    test_db = mock_client["test_db"]
    test_documents = [
        {"email": "test@example.com", "username": "hello", "password": "pasw0rd"},
        {"email": "test2@example.com", "username": "hihi", "password": "pa33word"},
        {"email": "test@example.com", "username": "hello8787", "password": "passw0rd"},
    ]
    test_db["test_col"].insert_many(test_documents)
    test_col = ExtendedCollection(test_db["test_col"])

    def test_find(self):
        test_result = self.test_col.find({"email": "test@example.com"})
        assert isinstance(test_result, ExtendedCursor)

    def test_find_one_not_found(self):
        test_result = self.test_col.find_one({"username": "nono"})
        assert test_result is None

    def test_find_one_type(self):
        test_result = self.test_col.find_one({"username": "hello"})
        assert isinstance(test_result, dict)

    def test_find_one(self):
        test_result = self.test_col.find_one({"username": "hello"})
        del test_result["_id"]
        assert test_result == {
            "email": "test@example.com",
            "username": "hello",
            "password": "pasw0rd",
        }

    def test_exists_true(self):
        test_result = self.test_col.exists("username", "hello")
        assert test_result is True

    def test_exists_false(self):
        test_result = self.test_col.exists("username", "random name")
        assert test_result is False
