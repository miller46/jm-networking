import unittest
from unittest.mock import patch

import jm_networking as jmn
from jm_networking import JmNetwork, ObjectNetworking, RateLimitedNetworking
from tests.example_model import ExampleModel


class FakeResponse:
    def __init__(self, status_code=200, text="ok", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.get_calls = 0
        self.post_calls = 0
        self.put_calls = 0
        self.delete_calls = 0

    def get(self, url, params=None, **kwargs):
        self.get_calls += 1
        return self.response

    def post(self, url, data=None, json=None, params=None, **kwargs):
        self.post_calls += 1
        return self.response

    def put(self, url, data=None, json=None, params=None, **kwargs):
        self.put_calls += 1
        return self.response

    def delete(self, url, params=None, **kwargs):
        self.delete_calls += 1
        return self.response


class TestConnectionPooling(unittest.TestCase):
    def setUp(self):
        jmn._SESSION = None

    @patch("jm_networking.requests.get", side_effect=AssertionError("requests.get should not be used"))
    @patch("jm_networking.requests.Session")
    def test_jmnetwork_uses_session_and_reuses(self, mock_session, _):
        fake = FakeSession(FakeResponse(200, "ok"))
        mock_session.return_value = fake

        status, payload = JmNetwork.get("https://example.com")
        status2, payload2 = JmNetwork.get("https://example.com")

        self.assertEqual(status, 200)
        self.assertEqual(payload, "ok")
        self.assertEqual(status2, 200)
        self.assertEqual(payload2, "ok")
        self.assertEqual(fake.get_calls, 2)
        self.assertEqual(mock_session.call_count, 1)

    @patch("jm_networking.requests.get", side_effect=AssertionError("requests.get should not be used"))
    @patch("jm_networking.requests.Session")
    def test_objectnetworking_uses_session(self, mock_session, _):
        fake = FakeSession(FakeResponse(200, "ok", json_data={"id": 1, "userId": 1, "title": "t", "completed": False}))
        mock_session.return_value = fake

        status, obj = ObjectNetworking.get("https://example.com", ExampleModel)

        self.assertEqual(status, 200)
        self.assertEqual(obj.id, 1)
        self.assertEqual(fake.get_calls, 1)
        self.assertEqual(mock_session.call_count, 1)

    @patch("jm_networking.requests.get", side_effect=AssertionError("requests.get should not be used"))
    @patch("jm_networking.requests.Session")
    def test_rate_limited_networking_uses_session(self, mock_session, _):
        fake = FakeSession(FakeResponse(200, "ok"))
        mock_session.return_value = fake

        client = RateLimitedNetworking(max_retries=0, max_requests_per_second=1000, timeout=1)
        status, payload = client.get("https://example.com")

        self.assertEqual(status, 200)
        self.assertEqual(payload, "ok")
        self.assertEqual(fake.get_calls, 1)
        self.assertEqual(mock_session.call_count, 1)


if __name__ == "__main__":
    unittest.main()
