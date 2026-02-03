import unittest

from jm_networking import AsyncNetworking, InternalServerError


class FakeResponse:
    def __init__(self, status, text, json_data=None, headers=None):
        self.status = status
        self._text = text
        self._json = json_data
        self.headers = headers or {}

    async def text(self):
        return self._text

    async def json(self):
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

    async def test_get_raises_on_non_2xx(self):
        response = FakeResponse(500, "boom")
        session = FakeSession(response)
        client = AsyncNetworking(session=session)

        with self.assertRaises(InternalServerError) as ctx:
            await client.get("https://example.com")

        self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
