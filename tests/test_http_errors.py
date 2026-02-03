import unittest
from unittest.mock import patch

from jm_networking import (
    JmNetwork,
    ObjectNetworking,
    NotFoundError,
    InternalServerError,
)
from tests.example_model import ExampleModel


class FakeResponse:
    def __init__(self, status_code, text, json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def json(self):
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class TestHttpErrors(unittest.TestCase):
    @patch("jm_networking.requests.get")
    def test_jmnetwork_raises_on_non_2xx(self, mock_get):
        mock_get.return_value = FakeResponse(404, "not found")

        with self.assertRaises(NotFoundError) as ctx:
            JmNetwork.get("https://example.com")

        self.assertEqual(ctx.exception.status_code, 404)

    @patch("jm_networking.requests.get")
    def test_objectnetworking_raises_before_json(self, mock_get):
        mock_get.return_value = FakeResponse(500, "server error")

        with self.assertRaises(InternalServerError) as ctx:
            ObjectNetworking.get("https://example.com", ExampleModel)

        self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
