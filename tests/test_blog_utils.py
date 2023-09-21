from unittest.mock import MagicMock
from application.blog.utils import NewUserSetup

class TestNewUserSetup:

    mock_request = MagicMock()
    mock_db_handler = MagicMock()
    mock_logger = MagicMock()

    def test_form_validate1(self):

        self.mock_request.form.to_dict.return_value = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'blogname': 'myblog'
        }

        user_registration = NewUserSetup(
            request=self.mock_request, 
            db_handler=self.mock_db_handler,
            logger=self.mock_logger
        )

        assert user_registration._form_validated() == True

