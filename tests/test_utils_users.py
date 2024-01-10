from unittest.mock import MagicMock
import pytest
from flask_login import login_user, current_user
from blogyourway import create_app
from blogyourway.utils.users import User, NewUserSetup

###################################################################

# testing user class

###################################################################


def test_user_setup():

    user_creds = {
        "username": "hank",
        "email": "hank@test.com",
        "paswword": "3456somehasedthing789",
    }
    user = User(user_creds)
    assert user.id == "hank"
    assert user.username == "hank"


@pytest.fixture
def app():

    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture
def test_current_user_property(app):

    with app.test_request_context():

        user_creds = {
            "username": "hank",
            "email": "hank@test.com",
            "password": "3456somehashedthing789",
        }
        user = User(user_creds)
        login_user(user)
        assert current_user.username == "hank"


###################################################################

# testing new user setup

###################################################################


class TestNewUserSetup:

    mock_request = MagicMock()
    mock_db_handler = MagicMock()
    mock_logger = MagicMock()

    def test_form_validate_valid(self):

        mock_validator = MagicMock()
        mock_validator.validate_email.return_value = True
        mock_validator.validate_password.return_value = True
        mock_validator.validate_username.return_value = True
        mock_validator.validate_blogname.return_value = True

        user_registration = NewUserSetup(
            request=self.mock_request,
            db_handler=self.mock_db_handler,
            logger=self.mock_logger,
        )
        validate_result = user_registration._form_validated(validator=mock_validator)

        assert validate_result == True

    def test_form_validate_invalid_email(self):

        mock_validator = MagicMock()
        mock_validator.validate_email.return_value = False
        mock_validator.validate_password.return_value = True
        mock_validator.validate_username.return_value = True
        mock_validator.validate_blogname.return_value = True

        user_registration = NewUserSetup(
            request=self.mock_request,
            db_handler=self.mock_db_handler,
            logger=self.mock_logger,
        )
        validate_result = user_registration._form_validated(validator=mock_validator)

        assert validate_result == False

    def test_form_validate_invalid_password(self):

        mock_validator = MagicMock()
        mock_validator.validate_email.return_value = True
        mock_validator.validate_password.return_value = False
        mock_validator.validate_username.return_value = True
        mock_validator.validate_blogname.return_value = True

        user_registration = NewUserSetup(
            request=self.mock_request,
            db_handler=self.mock_db_handler,
            logger=self.mock_logger,
        )
        validate_result = user_registration._form_validated(validator=mock_validator)

        assert validate_result == False

    def test_form_validate_invalid_username(self):

        mock_validator = MagicMock()
        mock_validator.validate_email.return_value = True
        mock_validator.validate_password.return_value = True
        mock_validator.validate_username.return_value = False
        mock_validator.validate_blogname.return_value = True

        user_registration = NewUserSetup(
            request=self.mock_request,
            db_handler=self.mock_db_handler,
            logger=self.mock_logger,
        )
        validate_result = user_registration._form_validated(validator=mock_validator)

        assert validate_result == False

    def test_form_validate_invalid_blogname(self):

        mock_validator = MagicMock()
        mock_validator.validate_email.return_value = True
        mock_validator.validate_password.return_value = True
        mock_validator.validate_username.return_value = True
        mock_validator.validate_blogname.return_value = False

        user_registration = NewUserSetup(
            request=self.mock_request,
            db_handler=self.mock_db_handler,
            logger=self.mock_logger,
        )
        validate_result = user_registration._form_validated(validator=mock_validator)

        assert validate_result == False
