import unittest
from unittest.mock import patch

import jm_networking as jmn
from jm_networking import ObjectNetworking
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

    def get(self, url, params=None, **kwargs):
        self.get_calls += 1
        return self.response

    def post(self, url, json=None, params=None, **kwargs):
        self.post_calls += 1
        return self.response


class DummySchema:
    def __init__(self, many=False):
        self.many = many

    def load(self, data):
        return data

    def dump(self, obj):
        return {"dumped": True}


def dummy_class_schema(_cls):
    class Schema(DummySchema):
        pass

    return Schema


class TestSchemaCaching(unittest.TestCase):
    def setUp(self):
        if hasattr(jmn, "_schema_class_for"):
            jmn._schema_class_for.cache_clear()

    @patch("jm_networking._get_session")
    @patch("jm_networking.class_schema")
    def test_class_schema_cached_for_get(self, mock_class_schema, mock_get_session):
        mock_class_schema.side_effect = dummy_class_schema
        mock_get_session.return_value = FakeSession(FakeResponse(200, "ok", json_data={"id": 1}))

        ObjectNetworking.get("https://example.com", ExampleModel)
        ObjectNetworking.get("https://example.com", ExampleModel)

        self.assertEqual(mock_class_schema.call_count, 1)

    @patch("jm_networking._get_session")
    @patch("jm_networking.class_schema")
    def test_class_schema_cached_for_post(self, mock_class_schema, mock_get_session):
        mock_class_schema.side_effect = dummy_class_schema
        mock_get_session.return_value = FakeSession(FakeResponse(201, "ok"))

        obj = ExampleModel(id=1)
        ObjectNetworking.post(obj, "https://example.com", params=None)
        ObjectNetworking.post(obj, "https://example.com", params=None)

        self.assertEqual(mock_class_schema.call_count, 1)


if __name__ == "__main__":
    unittest.main()
