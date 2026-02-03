import unittest
from unittest.mock import patch, call

from jm_networking import RateLimitedNetworking


class FakeClock:
    def __init__(self):
        self.current = 0.0
        self.sleep_calls = []

    def monotonic(self):
        return self.current

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)
        self.current += seconds


class TestRateLimitedNetworking(unittest.TestCase):
    def test_retries_on_429_then_succeeds(self):
        responses = [
            (429, {"error": "rate limited"}),
            (200, {"ok": True}),
        ]

        def fake_get(*args, **kwargs):
            return responses.pop(0)

        with patch("jm_networking.JmNetwork.get", side_effect=fake_get) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0):
            client = RateLimitedNetworking(max_retries=2, max_requests_per_second=1000, timeout=5)
            status, payload = client.get("https://example.com", is_json=True, params=None)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    def test_gives_up_after_max_retries(self):
        with patch("jm_networking.JmNetwork.get", return_value=(429, "limit")) as mock_get, \
             patch("jm_networking.time.sleep") as mock_sleep, \
             patch("jm_networking.time.monotonic", return_value=0.0):
            client = RateLimitedNetworking(max_retries=2, max_requests_per_second=1000, timeout=3)
            status, payload = client.get("https://example.com", is_json=False, params=None)

        self.assertEqual(status, 429)
        self.assertEqual(payload, "limit")
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(3), call(3)])

    def test_rate_limit_waits_when_over_capacity(self):
        clock = FakeClock()

        with patch("jm_networking.JmNetwork.get", return_value=(200, "ok")) as mock_get, \
             patch("jm_networking.time.monotonic", clock.monotonic), \
             patch("jm_networking.time.sleep", clock.sleep):
            client = RateLimitedNetworking(max_retries=0, max_requests_per_second=2, timeout=1)
            client.get("https://example.com")
            client.get("https://example.com")
            client.get("https://example.com")

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(len(clock.sleep_calls), 1)
        self.assertAlmostEqual(clock.sleep_calls[0], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
