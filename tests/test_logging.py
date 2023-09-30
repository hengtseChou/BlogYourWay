import pytest
from unittest.mock import patch, MagicMock
from application.services.log import my_logger


@pytest.fixture
def mock_client_ip():
    with patch("application.services.log._return_client_ip") as mock:
        mock.return_value = '127.0.0.1'
        yield mock

def test_page_visited(mock_client_ip, caplog):
    mock_request = MagicMock()
    mock_request.environ = {"RAW_URI": "test.com"}
    my_logger.page_visited(mock_request)
    assert '127.0.0.1 - test.com was visited.' in caplog.text
        