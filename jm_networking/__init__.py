import json

import asyncio
import inspect
import random
import requests
import logging
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from marshmallow_dataclass import class_schema

try:
    import aiohttp
except ImportError:
    aiohttp = None

_SESSION = None
_SESSION_LOCK = threading.Lock()


def _get_session():
    global _SESSION
    if _SESSION is None:
        with _SESSION_LOCK:
            if _SESSION is None:
                _SESSION = requests.Session()
    return _SESSION


class NetworkError(Exception):
    """Base class for all networking errors raised by this library."""


class TransportError(NetworkError):
    """Errors where no HTTP response was received (DNS, connect, SSL, etc.)."""

    def __init__(self, message, url=None, original=None):
        self.url = url
        self.original = original
        super().__init__(message)


class NetworkTimeoutError(TransportError):
    """Request timed out."""


class HttpError(NetworkError):
    """HTTP response received but status was non-2xx."""

    def __init__(self, status_code, url, body=None, response=None):
        self.status_code = status_code
        self.url = url
        self.body = body
        self.response = response
        super().__init__(f"HTTP {status_code} for {url}")


class HttpRedirectError(HttpError):
    """3xx responses (only if redirects are disabled)."""


class HttpClientError(HttpError):
    """4xx responses."""


class HttpServerError(HttpError):
    """5xx responses."""


class BadRequestError(HttpClientError):
    """400 Bad Request."""


class UnauthorizedError(HttpClientError):
    """401 Unauthorized."""


class ForbiddenError(HttpClientError):
    """403 Forbidden."""


class NotFoundError(HttpClientError):
    """404 Not Found."""


class ConflictError(HttpClientError):
    """409 Conflict."""


class UnprocessableEntityError(HttpClientError):
    """422 Unprocessable Entity."""


class TooManyRequestsError(HttpClientError):
    """429 Too Many Requests."""

    def __init__(self, status_code, url, body=None, response=None, retries=None):
        self.retries = retries
        super().__init__(status_code, url, body=body, response=response)


class InternalServerError(HttpServerError):
    """500 Internal Server Error."""


class BadGatewayError(HttpServerError):
    """502 Bad Gateway."""


class ServiceUnavailableError(HttpServerError):
    """503 Service Unavailable."""


class GatewayTimeoutError(HttpServerError):
    """504 Gateway Timeout."""


def _is_success(status_code):
    return 200 <= status_code < 300


def _exception_for_status(status_code):
    if status_code == 400:
        return BadRequestError
    if status_code == 401:
        return UnauthorizedError
    if status_code == 403:
        return ForbiddenError
    if status_code == 404:
        return NotFoundError
    if status_code == 409:
        return ConflictError
    if status_code == 422:
        return UnprocessableEntityError
    if status_code == 429:
        return TooManyRequestsError
    if status_code == 500:
        return InternalServerError
    if status_code == 502:
        return BadGatewayError
    if status_code == 503:
        return ServiceUnavailableError
    if status_code == 504:
        return GatewayTimeoutError

    if 300 <= status_code < 400:
        return HttpRedirectError
    if 400 <= status_code < 500:
        return HttpClientError
    if 500 <= status_code < 600:
        return HttpServerError
    return HttpError


def _raise_for_status(status_code, url, body=None, response=None):
    if _is_success(status_code):
        return
    exc_cls = _exception_for_status(status_code)
    raise exc_cls(status_code, url, body=body, response=response)


class JmNetwork:

    logger = logging.getLogger()

    @staticmethod
    def get(url, is_json=False, params=None, **kwargs):
        try:
            session = _get_session()
            request = session.get(url, params=params, **kwargs)
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        status_code = request.status_code
        text = request.text
        _raise_for_status(status_code, url, text, response=request)
        if is_json is False:
            return status_code, text
        payload = json.loads(text)
        return status_code, payload

    @staticmethod
    def post(url, data=None, json=None, **kwargs):
        try:
            session = _get_session()
            request = session.post(url, data=data, json=json, **kwargs)
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        status_code = request.status_code
        text = request.text
        _raise_for_status(status_code, url, text, response=request)
        return status_code, text

    @staticmethod
    def put(url, data=None, **kwargs):
        try:
            session = _get_session()
            request = session.put(url, data=data, **kwargs)
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        status_code = request.status_code
        text = request.text
        _raise_for_status(status_code, url, text, response=request)
        return status_code, text

    @staticmethod
    def delete(url, **kwargs):
        try:
            session = _get_session()
            request = session.delete(url, **kwargs)
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        status_code = request.status_code
        text = request.text
        _raise_for_status(status_code, url, text, response=request)
        return status_code, text


class ObjectNetworking:

    @staticmethod
    def get(url, class_object, params=None, **kwargs):
        try:
            request = requests.get(url, params, **kwargs)
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        status_code = request.status_code
        _raise_for_status(status_code, url, request.text, response=request)
        data = request.json()

        try:
            is_list = isinstance(data, list)
            my_class_schema = class_schema(class_object)(many=is_list)
            deserialized = my_class_schema.load(data)
            return status_code, deserialized
        except Exception as ex:
            logging.error("Error deserializing object  %s", url)
            raise ex

    @staticmethod
    def post(class_object, url, params, **kwargs):
        return ObjectNetworking._req(class_object=class_object, url=url, params=params, method="POST", **kwargs)

    @staticmethod
    def put(class_object, url, params, **kwargs):
        return ObjectNetworking._req(class_object=class_object, url=url, params=params, method="PUT", **kwargs)

    @staticmethod
    def delete(class_object, url, params, **kwargs):
        return ObjectNetworking._req(class_object=class_object, url=url, params=params, method="DELETE", **kwargs)

    @staticmethod
    def _req(class_object, url, params, method, **kwargs):
        method = method.lower()
        cls = class_object.__class__
        class_name = cls.__name__

        schema_cls = class_schema(cls)
        schema = schema_cls()
        payload = schema.dump(class_object)

        try:
            if method == "post":
                resp = requests.post(url, json=payload, params=params)
            elif method == "put":
                resp = requests.put(url, json=payload, params=params)
            elif method == "delete":
                resp = requests.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
        except requests.exceptions.Timeout as ex:
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except requests.exceptions.RequestException as ex:
            raise TransportError("Network error", url=url, original=ex) from ex
        _raise_for_status(resp.status_code, url, resp.text, response=resp)
        return resp

class AsyncNetworking:

    logger = logging.getLogger()

    def __init__(self, session=None, headers=None, timeout=None, raise_on_non_2xx=True):
        self.on_success_callback = None
        self.on_failure_callback = None
        self.on_exception_callback = None
        self.headers = headers or {}
        self.timeout = timeout
        self.raise_on_non_2xx = raise_on_non_2xx
        self._session = session
        self._owns_session = False

    def set_headers(self, headers):
        self.headers = headers

    def on_success(self, callback):
        self.on_success_callback = callback

    def on_failure(self, callback):
        self.on_failure_callback = callback

    def on_exception(self, callback):
        self.on_exception_callback = callback

    def default_exception_callback(self, exception):
        self.log(exception, error=True)

    async def get(self, url, is_json=False, params=None, **kwargs):
        return await self._request("GET", url, is_json=is_json, params=params, **kwargs)

    async def put(self, url, data=None, json=None, **kwargs):
        return await self._request("PUT", url, data=data, json=json, **kwargs)

    async def post(self, url, data=None, json=None, **kwargs):
        return await self._request("POST", url, data=data, json=json, **kwargs)

    async def delete(self, url, **kwargs):
        return await self._request("DELETE", url, **kwargs)

    async def close(self):
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._owns_session = False

    async def __aenter__(self):
        if self._session is None:
            self._session = self._create_session()
            self._owns_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    def _create_session(self):
        if aiohttp is None:
            raise RuntimeError("aiohttp is required for AsyncNetworking. Install aiohttp to use async requests.")
        timeout = aiohttp.ClientTimeout(total=self.timeout) if self.timeout is not None else None
        return aiohttp.ClientSession(headers=self.headers or None, timeout=timeout)

    async def _request(self, method, url, is_json=False, params=None, data=None, json=None, **kwargs):
        if self._session is None:
            self._session = self._create_session()
            self._owns_session = True

        headers = {}
        if self.headers:
            headers.update(self.headers)
        if "headers" in kwargs and kwargs["headers"]:
            headers.update(kwargs["headers"])
        if headers:
            kwargs["headers"] = headers
        else:
            kwargs.pop("headers", None)

        if params is not None:
            kwargs["params"] = params
        if data is not None:
            kwargs["data"] = data
        if json is not None:
            kwargs["json"] = json

        try:
            async with self._session.request(method, url, **kwargs) as resp:
                text = None
                if not _is_success(resp.status):
                    text = await resp.text()
                    if self.on_failure_callback is not None:
                        await self._maybe_await(self.on_failure_callback(resp))
                    if self.raise_on_non_2xx:
                        _raise_for_status(resp.status, url, body=text, response=resp)

                if is_json:
                    try:
                        payload = await resp.json()
                    except Exception:
                        if text is None:
                            text = await resp.text()
                        payload = text
                else:
                    if text is None:
                        text = await resp.text()
                    payload = text

                if self.on_success_callback is not None:
                    return await self._maybe_await(self.on_success_callback(resp))
                return resp.status, payload
        except HttpError:
            raise
        except asyncio.TimeoutError as ex:
            if self.on_exception_callback is not None:
                return await self._maybe_await(self.on_exception_callback(ex))
            raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
        except Exception as ex:
            if aiohttp is not None and isinstance(ex, aiohttp.ClientError):
                if self.on_exception_callback is not None:
                    return await self._maybe_await(self.on_exception_callback(ex))
                raise TransportError("Network error", url=url, original=ex) from ex
            if self.on_exception_callback is not None:
                return await self._maybe_await(self.on_exception_callback(ex))
            raise

    async def _maybe_await(self, result):
        if inspect.isawaitable(result):
            return await result
        return result

    def log(self, message, error=False):
        if self.logger:
            if error:
                self.logger.error(message)
            else:
                self.logger.info(message)

class _TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.updated_at = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.updated_at
                if elapsed > 0:
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                    self.updated_at = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                if self.rate <= 0:
                    return

                wait = (1 - self.tokens) / self.rate

            if wait > 0:
                time.sleep(wait)


def _retry_after_seconds(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (parsed - now).total_seconds())
    except Exception:
        return None


class RateLimitedNetworking:

    def __init__(
        self,
        max_retries=3,
        max_requests_per_second=10,
        timeout=10,
        backoff_strategy="fixed",
        jitter=False,
        max_burst=None,
        respect_retry_after=True,
        raise_on_429=True,
    ):
        self.max_tries = max_retries
        self.max_requests_per_second = max_requests_per_second if max_requests_per_second and max_requests_per_second > 0 else None
        self.timeout = timeout
        self.backoff_strategy = backoff_strategy
        self.jitter = jitter
        self.max_burst = max_burst
        self.respect_retry_after = respect_retry_after
        self.raise_on_429 = raise_on_429
        self.retries = 0
        self._buckets = {}
        self._buckets_lock = threading.Lock()

    def get(self, url, is_json=False, params=None, **kwargs):
        last_status = None
        last_payload = None
        last_response = None

        for attempt in range(self.max_tries + 1):
            self.pre_process(url)
            try:
                response = requests.get(url, params=params, **kwargs)
            except requests.exceptions.Timeout as ex:
                raise NetworkTimeoutError("Request timed out", url=url, original=ex) from ex
            except requests.exceptions.RequestException as ex:
                raise TransportError("Network error", url=url, original=ex) from ex
            last_response = response
            last_status = response.status_code
            last_payload = response.text

            if is_json and response.status_code == 200:
                try:
                    last_payload = response.json()
                except ValueError:
                    last_payload = response.text

            if response.status_code != 429:
                self.retries = 0
                _raise_for_status(response.status_code, url, last_payload, response=response)
                return last_status, last_payload

            self.retries += 1
            if attempt >= self.max_tries:
                logging.error("429 Rate limit. Max retries (%s) reached.", self.max_tries)
                if self.raise_on_429:
                    raise TooManyRequestsError(
                        response.status_code,
                        url,
                        body=last_payload,
                        response=response,
                        retries=self.max_tries,
                    )
                return last_status, last_payload

            delay = self._compute_backoff_delay(attempt, response)
            logging.info("429 Rate limit. Retrying in %s seconds...", delay)
            if delay > 0:
                time.sleep(delay)

        return last_status, last_payload

    def process_response(self, status_code, payload):
        if status_code == 429:
            logging.error("429 Rate limit. Max retries (%s) reached.", self.max_tries)
        return status_code, payload

    def pre_process(self, url):
        if not self.max_requests_per_second:
            return

        host = urlsplit(url).netloc or ""
        bucket = self._get_bucket(host)
        if bucket is not None:
            bucket.acquire()

    def _get_bucket(self, host):
        with self._buckets_lock:
            bucket = self._buckets.get(host)
            if bucket is None:
                capacity = self.max_burst if self.max_burst is not None else self.max_requests_per_second
                bucket = _TokenBucket(self.max_requests_per_second, capacity)
                self._buckets[host] = bucket
            return bucket

    def _compute_backoff_delay(self, attempt, response):
        retry_after = None
        if self.respect_retry_after and response is not None:
            retry_after = _retry_after_seconds(response.headers.get("Retry-After"))

        if retry_after is not None:
            return retry_after

        if self.backoff_strategy == "fixed":
            delay = self.timeout
        elif self.backoff_strategy == "exponential":
            delay = self.timeout * (2 ** attempt)
        else:
            raise ValueError(f"Unsupported backoff strategy: {self.backoff_strategy}")

        if self.jitter:
            delay = random.uniform(0, delay)
        return delay
