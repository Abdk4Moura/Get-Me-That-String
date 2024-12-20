import pytest
from client import client_query, ClientConfig


def test_client_query_success():
    config = ClientConfig(server="127.0.0.1", port=44445, query="test string 1")
    response = client_query(config)
    assert "STRING" in response


def test_client_query_string_not_found():
    config = ClientConfig(server="127.0.0.1", port=44445, query="non existing query")
    response = client_query(config)
    assert response == "STRING NOT FOUND"


def test_client_query_server_error():
    config = ClientConfig(server="127.0.0.1", port=44446, query="test query")
    response = client_query(config)
    assert "Error" in response


def test_client_ssl_no_certificate():
    config = ClientConfig(
        server="127.0.0.1", port=44445, query="test string 1", ssl_enabled=True
    )
    response = client_query(config)
    assert "Error" in response
