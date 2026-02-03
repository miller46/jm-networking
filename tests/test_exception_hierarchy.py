import unittest
from unittest.mock import patch

import requests

from jm_networking import (
    JmNetwork,
    NetworkError,
    TransportError,
    NetworkTimeoutError,
    HttpError,
    HttpClientError,
    HttpServerError,
    HttpRedirectError,
    BadRequestError,
    TooManyRequestsError,
    InternalServerError,
)


class FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        raise ValueError("no json")


class TestExceptionHierarchy(unittest.TestCase):
    def test_hierarchy(self):
        self.assertTrue(issubclass(TransportError, NetworkError))
        self.assertTrue(issubclass(NetworkTimeoutError, TransportError))
        self.assertTrue(issubclass(HttpError, NetworkError))
        self.assertTrue(issubclass(HttpClientError, HttpError))
        self.assertTrue(issubclass(HttpServerError, HttpError))
        self.assertTrue(issubclass(HttpRedirectError, HttpError))
        self.assertTrue(issubclass(BadRequestError, HttpClientError))
        self.assertTrue(issubclass(TooManyRequestsError, HttpClientError))
        self.assertTrue(issubclass(InternalServerError, HttpServerError))

    @patch("jm_networking.requests.get")
    def test_status_400_maps_to_bad_request(self, mock_get):
        mock_get.return_value = FakeResponse(400, "bad request")

        with self.assertRaises(BadRequestError):
            JmNetwork.get("https://example.com")

    @patch("jm_networking.requests.get")
    def test_status_429_maps_to_too_many_requests(self, mock_get):
        mock_get.return_value = FakeResponse(429, "rate limited")

        with self.assertRaises(TooManyRequestsError):
            JmNetwork.get("https://example.com")

    @patch("jm_networking.requests.get")
    def test_status_500_maps_to_internal_server_error(self, mock_get):
        mock_get.return_value = FakeResponse(500, "server error")

        with self.assertRaises(InternalServerError):
            JmNetwork.get("https://example.com")

    @patch("jm_networking.requests.get", side_effect=requests.exceptions.Timeout())
    def test_timeout_maps_to_network_timeout_error(self, mock_get):
        with self.assertRaises(NetworkTimeoutError):
            JmNetwork.get("https://example.com")

    @patch("jm_networking.requests.get", side_effect=requests.exceptions.RequestException("boom"))
    def test_transport_error_maps_to_transport_error(self, mock_get):
        with self.assertRaises(TransportError):
            JmNetwork.get("https://example.com")


if __name__ == "__main__":
    unittest.main()
