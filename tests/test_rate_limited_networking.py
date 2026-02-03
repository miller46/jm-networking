import unittest
from unittest.mock import patch, call

from jm_networking import RateLimitedNetworking, RateLimitError


class FakeClock:
    def __init__(self):
        self.current = 0.0
        self.sleep_calls = []

    def monotonic(self):
        return self.current

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)
        self.current += seconds


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = "payload" if payload is None else str(payload)

    def json(self):
        return self._payload


class TestRateLimitedNetworking(unittest.TestCase):
    def test_per_host_token_bucket_independent(self):
        clock = FakeClock()
        response = FakeResponse(200, {"ok": True})

        with patch("jm_networking.requests.get", return_value=response) as mock_get, \
             patch("jm_networking.time.monotonic", clock.monotonic), \
             patch("jm_networking.time.sleep", clock.sleep):
            client = RateLimitedNetworking(max_retries=0, max_requests_per_second=1, timeout=1)
            client.get("https://a.example.com", is_json=True)
            client.get("https://b.example.com", is_json=True)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(clock.sleep_calls, [])

    def test_token_bucket_blocks_same_host(self):
        clock = FakeClock()
        response = FakeResponse(200, {"ok": True})

        with patch("jm_networking.requests.get", return_value=response) as mock_get, \
             patch("jm_networking.time.monotonic", clock.monotonic), \
             patch("jm_networking.time.sleep", clock.sleep):
            client = RateLimitedNetworking(max_retries=0, max_requests_per_second=1, timeout=1)
            client.get("https://a.example.com", is_json=True)
            client.get("https://a.example.com", is_json=True)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(clock.sleep_calls), 1)
        self.assertAlmostEqual(clock.sleep_calls[0], 1.0, places=6)

    def test_raises_after_max_retries_on_429(self):
        response = FakeResponse(429, {"error": "rate limited"})

        with patch("jm_networking.requests.get", return_value=response) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0):
            client = RateLimitedNetworking(max_retries=1, max_requests_per_second=1000, timeout=2)
            with self.assertRaises(RateLimitError):
                client.get("https://example.com", is_json=True)

        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(2)

    def test_fixed_backoff_uses_timeout(self):
        responses = [
            FakeResponse(429, {"error": "rate limited"}),
            FakeResponse(200, {"ok": True}),
        ]

        def fake_get(*args, **kwargs):
            return responses.pop(0)

        with patch("jm_networking.requests.get", side_effect=fake_get) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0):
            client = RateLimitedNetworking(
                max_retries=1,
                max_requests_per_second=1000,
                timeout=5,
                backoff_strategy="fixed",
                jitter=False,
            )
            status, payload = client.get("https://example.com", is_json=True)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    def test_exponential_backoff_with_jitter(self):
        responses = [
            FakeResponse(429, {"error": "rate limited"}),
            FakeResponse(429, {"error": "rate limited"}),
            FakeResponse(200, {"ok": True}),
        ]

        def fake_get(*args, **kwargs):
            return responses.pop(0)

        with patch("jm_networking.requests.get", side_effect=fake_get) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0), \
             patch("jm_networking.random.uniform", side_effect=[1.0, 3.0]):
            client = RateLimitedNetworking(
                max_retries=2,
                max_requests_per_second=1000,
                timeout=2,
                backoff_strategy="exponential",
                jitter=True,
            )
            status, payload = client.get("https://example.com", is_json=True)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mock_get.call_count, 3)
        mock_sleep.assert_has_calls([call(1.0), call(3.0)])

    def test_retry_after_header_overrides_backoff(self):
        responses = [
            FakeResponse(429, {"error": "rate limited"}, headers={"Retry-After": "7"}),
            FakeResponse(200, {"ok": True}),
        ]

        def fake_get(*args, **kwargs):
            return responses.pop(0)

        with patch("jm_networking.requests.get", side_effect=fake_get) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0):
            client = RateLimitedNetworking(
                max_retries=1,
                max_requests_per_second=1000,
                timeout=2,
                backoff_strategy="exponential",
                jitter=True,
                respect_retry_after=True,
            )
            status, payload = client.get("https://example.com", is_json=True)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(7.0)


if __name__ == "__main__":
    unittest.main()
