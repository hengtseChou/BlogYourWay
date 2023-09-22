from unittest.mock import patch
import pytest
from datetime import datetime
from application.utils.common import FormValidator, get_today

###################################################################

# testing form validator

###################################################################


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

        input_ = "username測試"
        assert self.validator.validate_username(input_) == False


###################################################################

# testing get_today()

###################################################################


@patch("application.utils.common.datetime")
def test_get_today_as_in_debug(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    today = get_today("debug")
    assert today == datetime(2023, 9, 22, 12, 0, 0)


@patch("application.utils.common.datetime")
def test_get_today_as_in_prod(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    today = get_today("prod")
    assert today == datetime(2023, 9, 22, 20, 0, 0)


@patch("application.utils.common.datetime")
def test_get_today_random_env_argument(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    with pytest.raises(ValueError):
        today = get_today("hello world")