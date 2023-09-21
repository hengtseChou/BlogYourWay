from unittest.mock import MagicMock
from application.blog.utils import (
    FormValidator, 
    NewUserSetup
)

class TestFormValidatorEmail:

    validator = FormValidator()

    def test_validate_email_valid(self):

        input_ = "test123@example.com"
        assert self.validator.validate_email(input_) == True

    def test_validate_email_empty(self):

        input_ = ""
        assert self.validator.validate_email(input_) == False

    def test_validate_email_missing_at(self):
        
        input_ = "johndoeexample.com"
        assert self.validator.validate_email(input_) == False
        
    def test_validate_email_missing_tld(self):

        input_ = "johndoe@example"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_contains_space(self):

        input_ = "john doe@example.com"
        assert self.validator.validate_email(input_) == False
        
    def test_validate_email_leading_space(self):

        input_ = " johndoe@example.com"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_trailing_space(self):

        input_ = "johndoe@example.com "
        assert self.validator.validate_email(input_) == False

    def test_validate_email_consecutive_dots_in_domain(self):

        input_ = "johndoe@example..com"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_special_character_in_local(self):

        input_ = "john.doe@ex@mple.com"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_special_character_in_domain(self):

        input_ = "john&doe@example.com"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_missing_local(self):

        input_ = "@example.com"
        assert self.validator.validate_email(input_) == False

    def test_validate_email_missing_domain(self):

        input_ = "johndoe"
        assert self.validator.validate_email(input_) == False


class TestFormValidatorPassword:

    validator = FormValidator()

    def test_validate_password_valid(self):

        input_ = "Password1"
        assert self.validator.validate_password(input_) == True

    def test_validate_password_valid_with_special_character(self):

        input_ = "P@ssw0rd"
        assert self.validator.validate_password(input_) == True

    def test_validate_password_too_short(self):
        
        input_ = "P@w0rd"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_missing_uppercase(self):
        
        input_ = "password1"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_missing_lowercase(self):
        
        input_ = "PASSWORD1"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_missing_number(self):
        
        input_ = "Password"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_contains_space(self):

        input_ = "Pas4 word"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_leading_space(self):

        input_ = " Passwor1"
        assert self.validator.validate_password(input_) == False

    def test_validate_password_trailing_space(self):

        input_ = "Passwor1 "
        assert self.validator.validate_password(input_) == False

class TestFormValidatorUsername:

    validator = FormValidator()

    def test_validate_username_valid1(self):

        input_ = "john_doe123"
        assert self.validator.validate_username(input_) == True

    def test_validate_username_valid2(self):

        input_ = "user.name"
        assert self.validator.validate_username(input_) == True

    def test_validate_username_valid3(self):

        input_ = "123-username"
        assert self.validator.validate_username(input_) == True

    def test_validate_username_contains_at(self):

        input_ = "user@name"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_contains_hash(self):

        input_ = "user#name"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_contains_caret(self):

        input_ = "user^name"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_contains_tilde(self):

        input_ = "user~name"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_contains_space(self):

        input_ = "user name"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_leading_space(self):

        input_ = " username"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_trailing_space(self):

        input_ = "username "
        assert self.validator.validate_username(input_) == False

    def test_validate_username_leading_dash(self):

        input_ = "-username"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_trailing_dash(self):

        input_ = "username-"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_leading_dot(self):

        input_ = ".username"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_trailing_dot(self):

        input_ = "username."
        assert self.validator.validate_username(input_) == False

    def test_validate_username_leading_underscore(self):

        input_ = "_username"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_trailing_underscore(self):

        input_ = "username_"
        assert self.validator.validate_username(input_) == False

    def test_validate_username_chinese(self):

        input_ = "測試"
        assert self.validator.validate_username(input_) == False   
    

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

