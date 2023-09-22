from unittest.mock import MagicMock
from application.utils.users import NewUserSetup

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
