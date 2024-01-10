import pytest
from unittest.mock import MagicMock, patch
from blogyourway.services.log import my_logger


@pytest.fixture
def mock_client_ip():
    with patch("application.services.log.return_client_ip") as mock:
        mock.return_value = "127.0.0.1"
        yield mock


def test_page_visited(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}

    my_logger.page_viewed(mock_request)

    assert "127.0.0.1 - test.com was visited." in caplog.text


def test_invalid_username(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "invalid_user"

    my_logger.invalid_username(username, mock_request)

    assert f"127.0.0.1 - Invalid username {username} at test.com." in caplog.text


def test_invalid_post_uid(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "user"
    post_uid = "invalid_uid"

    my_logger.invalid_post_uid(username, post_uid, mock_request)

    assert (
        f"127.0.0.1 - Invalid post uid {post_uid} for user {username} was entered."
        in caplog.text
    )


def test_invalid_author_for_post(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "user"
    post_uid = "invalid_uid"

    my_logger.invalid_author_for_post(username, post_uid, mock_request)

    assert (
        f"127.0.0.1 - The author entered ({username}) was not the author of the post {post_uid}."
        in caplog.text
    )


def test_invalid_procedure(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "user"
    procedure = "invalid_procedure"

    my_logger.invalid_procedure(username, procedure, mock_request)

    assert f"127.0.0.1 - Invalid procedure to {procedure} for {username}." in caplog.text


def test_log_for_backstage_tab(mock_client_ip, caplog):
    # Arrange
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "user"
    tab = "testing"

    # Act
    my_logger.log_for_backstage_tab(username, tab, mock_request)

    # Assert
    assert f"127.0.0.1 - User {username} is now at the {tab} tab." in caplog.text


def test_log_for_pagination(mock_client_ip, caplog):
    # Arrange
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    username = "user"
    num_of_posts = 10

    # Act
    my_logger.log_for_pagination(username, num_of_posts, mock_request)

    # Assert
    assert (
        f"127.0.0.1 - Showing {num_of_posts} posts for user {username} at test.com."
        in caplog.text
    )


###########################################################################

# test user actions

###########################################################################


def test_login_failed(mock_client_ip, caplog):
    mock_request = MagicMock()
    msg = "Invalid username"

    my_logger.user.login_failed(msg, mock_request)

    assert "127.0.0.1 - Login failed. Msg: Invalid username." in caplog.text


def test_login_succeeded(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"

    my_logger.user.login_succeeded(username, mock_request)

    assert f"127.0.0.1 - User test has logged in." in caplog.text


def test_logout(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"

    my_logger.user.logout(username, mock_request)

    assert f"127.0.0.1 - User test has logged out and session data is cleared." in caplog.text


def test_registration_failed(mock_client_ip, caplog):
    mock_request = MagicMock()
    msg = "Registration failed"

    my_logger.user.registration_failed(msg, mock_request)

    assert "127.0.0.1 - Registration failed. Msg: Registration failed." in caplog.text


def test_registration_succeeded(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"

    my_logger.user.registration_succeeded(username, mock_request)

    assert f"127.0.0.1 - New user test has been created." in caplog.text


def test_deleted(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"

    my_logger.user.user_deleted(username, mock_request)

    assert f"127.0.0.1 - User test has been deleted." in caplog.text


def test_data_created(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"
    data_info = "new_data_info"

    my_logger.user.data_created(username, data_info, mock_request)

    # Assert
    assert f"127.0.0.1 - New_data_info for user test has been created." in caplog.text


def test_data_updated(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"
    data_info = "updated_data_info"

    # Act
    my_logger.user.data_updated(username, data_info, mock_request)

    # Assert
    assert f"127.0.0.1 - Updated_data_info for user test has been updated." in caplog.text


def test_data_deleted(mock_client_ip, caplog):
    mock_request = MagicMock()
    username = "test"
    data_info = "deleted_data_info"

    # Act
    my_logger.user.data_deleted(username, data_info, mock_request)

    # Assert
    assert f"127.0.0.1 - Deleted_data_info for user test has been deleted." in caplog.text
