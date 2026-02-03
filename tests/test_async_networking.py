import unittest

from jm_networking import AsyncNetworking, InternalServerError


class FakeResponse:
    def __init__(self, status, text, json_data=None, headers=None, json_error=False):
        self.status = status
        self._text = text
        self._json = json_data
        self._json_error = json_error
        self.headers = headers or {}
        self.text_calls = 0
        self.json_calls = 0

    async def text(self):
        self.text_calls += 1
        return self._text

    async def json(self):
        self.json_calls += 1
        if self._json_error:
            raise ValueError("invalid json")
        return self._json


class FakeRequestContext:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return FakeRequestContext(self.response)

    async def close(self):
        self.closed = True


class TestAsyncNetworking(unittest.IsolatedAsyncioTestCase):
    async def test_get_returns_json(self):
        response = FakeResponse(200, "{\"ok\": true}", json_data={"ok": True})
        session = FakeSession(response)
        client = AsyncNetworking(session=session)

        status, payload = await client.get("https://example.com", is_json=True)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(session.requests[0][0], "GET")
        self.assertEqual(response.json_calls, 1)
        self.assertEqual(response.text_calls, 0)

    async def test_get_raises_on_non_2xx(self):
        response = FakeResponse(500, "boom")
        session = FakeSession(response)
        client = AsyncNetworking(session=session)

        with self.assertRaises(InternalServerError) as ctx:
            await client.get("https://example.com")

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(response.text_calls, 1)

    async def test_get_json_falls_back_to_text(self):
        response = FakeResponse(200, "not json", json_data=None, json_error=True)
        session = FakeSession(response)
        client = AsyncNetworking(session=session)

        status, payload = await client.get("https://example.com", is_json=True)

        self.assertEqual(status, 200)
        self.assertEqual(payload, "not json")
        self.assertEqual(response.json_calls, 1)
        self.assertEqual(response.text_calls, 1)


if __name__ == "__main__":
    unittest.main()
