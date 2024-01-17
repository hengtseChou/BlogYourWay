from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime
from blogyourway.helpers.common import FormValidator, UIDGenerator, get_today

###################################################################

# testing form validator

###################################################################


class TestFormValidatorEmail:

    validator = FormValidator()

    def test_validate_email_valid(self):

        input_ = "test123@example.com"
        assert self.validator.validate_email(input_) is True

    def test_validate_email_empty(self):

        input_ = ""
        assert self.validator.validate_email(input_) is False

    def test_validate_email_missing_at(self):

        input_ = "johndoeexample.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_missing_tld(self):

        input_ = "johndoe@example"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_contains_space(self):

        input_ = "john doe@example.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_leading_space(self):

        input_ = " johndoe@example.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_trailing_space(self):

        input_ = "johndoe@example.com "
        assert self.validator.validate_email(input_) is False

    def test_validate_email_consecutive_dots_in_domain(self):

        input_ = "johndoe@example..com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_special_character_in_local(self):

        input_ = "john.doe@ex@mple.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_special_character_in_domain(self):

        input_ = "john&doe@example.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_missing_local(self):

        input_ = "@example.com"
        assert self.validator.validate_email(input_) is False

    def test_validate_email_missing_domain(self):

        input_ = "johndoe"
        assert self.validator.validate_email(input_) is False


class TestFormValidatorPassword:

    validator = FormValidator()

    def test_validate_password_valid(self):

        input_ = "Password1"
        assert self.validator.validate_password(input_) is True

    def test_validate_password_valid_with_special_character(self):

        input_ = "P@ssw0rd"
        assert self.validator.validate_password(input_) is True

    def test_validate_password_too_short(self):

        input_ = "P@w0rd"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_missing_uppercase(self):

        input_ = "password1"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_missing_lowercase(self):

        input_ = "PASSWORD1"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_missing_number(self):

        input_ = "Password"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_contains_space(self):

        input_ = "Pas4 word"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_leading_space(self):

        input_ = " Passwor1"
        assert self.validator.validate_password(input_) is False

    def test_validate_password_trailing_space(self):

        input_ = "Passwor1 "
        assert self.validator.validate_password(input_) is False


class TestFormValidatorUsername:

    validator = FormValidator()

    def test_validate_username_valid1(self):

        input_ = "johndoe123"
        assert self.validator.validate_username(input_) is True

    def test_validate_username_valid3(self):

        input_ = "123-username"
        assert self.validator.validate_username(input_) is True

    def test_validate_username_contains_at(self):

        input_ = "user@name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_hash(self):

        input_ = "user#name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_caret(self):

        input_ = "user^name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_tilde(self):

        input_ = "user~name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_space(self):

        input_ = "user name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_leading_space(self):

        input_ = " username"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_trailing_space(self):

        input_ = "username "
        assert self.validator.validate_username(input_) is False

    def test_validate_username_leading_hyphen(self):

        input_ = "-username"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_trailing_hyphen(self):

        input_ = "username-"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_dot(self):

        input_ = "user.name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_underscore(self):

        input_ = "user_name"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_mandarin(self):

        input_ = "username測試"
        assert self.validator.validate_username(input_) is False

    def test_validate_username_contains_uppercases(self):

        input_ = "Username123"
        assert self.validator.validate_username(input_) is False


class TestFormValidatorBlogname:

    validator = FormValidator()

    def test_validate_blogname_valid(self):

        input_ = "This is Hank"
        assert self.validator.validate_blogname(input_) is True

    def test_validate_blogname_mandarin(self):

        input_ = "小小部落格"
        assert self.validator.validate_blogname(input_) is True

    def test_validate_blogname_languages_combind(self):

        input_ = "This is 小小部落格"
        assert self.validator.validate_blogname(input_) is True

    def test_validate_blogname_too_long(self):

        input_ = "Hank's personal blogging website"
        assert self.validator.validate_blogname(input_) is False

    def test_validate_blogname_empty(self):

        input_ = ""
        assert self.validator.validate_blogname(input_) is False


###################################################################

# testing uid generator

###################################################################


class TestUIDGenerator:
    @patch("random.choices", side_effect=["postuid1"])
    def test_generate_post_uid(self, mock_random_choices):

        db_handler = MagicMock()
        db_handler.post_info.exists.side_effect = [False]
        uid_generator = UIDGenerator(db_handler)
        generated_uid = uid_generator.generate_post_uid()

        assert generated_uid == "postuid1"

    @patch("random.choices", side_effect=[["postuid1"], ["postuid2"]])
    def test_generate_another_post_uid_if_exists(self, mock_random_choices):

        db_handler = MagicMock()
        db_handler.post_info.exists.side_effect = [True, False]
        uid_generator = UIDGenerator(db_handler)
        generated_uid = uid_generator.generate_post_uid()

        assert generated_uid == "postuid2"

    @patch("random.choices", side_effect=["commentuid1"])
    def test_generate_comment_uid(self, mock_random_choices):

        db_handler = MagicMock()
        db_handler.comment.exists.side_effect = [False]
        uid_generator = UIDGenerator(db_handler)
        generated_uid = uid_generator.generate_comment_uid()

        assert generated_uid == "commentuid1"

    @patch("random.choices", side_effect=[["commentuid1"], ["commentuid2"]])
    def test_generate_another_comment_uid_if_exists(self, mock_random_choices):

        db_handler = MagicMock()
        db_handler.comment.exists.side_effect = [True, False]
        uid_generator = UIDGenerator(db_handler)
        generated_uid = uid_generator.generate_comment_uid()

        assert generated_uid == "commentuid2"


###################################################################

# testing get_today()

###################################################################


@patch("blogyourway.utils.common.datetime")
def test_get_today_as_in_develop(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    today = get_today(env="develop")
    assert today == datetime(2023, 9, 22, 12, 0, 0)


@patch("blogyourway.utils.common.datetime")
def test_get_today_as_in_prod(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    today = get_today(env="prod")
    assert today == datetime(2023, 9, 22, 20, 0, 0)


@patch("blogyourway.utils.common.datetime")
def test_get_today_random_env_argument(mock_datetime):

    mock_datetime.now.return_value = datetime(2023, 9, 22, 12, 0, 0)
    with pytest.raises(ValueError):
        get_today(env="wrong input")
