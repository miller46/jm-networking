import json
from collections import deque

import requests
import logging
import time

from marshmallow_dataclass import class_schema


class JmNetwork:

    logger = logging.getLogger()

    @staticmethod
    def get(url, is_json=False, params=None, **kwargs):
        request = requests.get(url, params, **kwargs)
        status_code = request.status_code
        text = request.text
        if is_json is False or status_code != 200:
            return status_code, text
        else:
            payload = json.loads(text)
            return status_code, payload

    @staticmethod
    def post(url, data=None, json=None, **kwargs):
        request = requests.post(url, data, json, **kwargs)
        status_code = request.status_code
        text = request.text
        return status_code, text

    @staticmethod
    def put(url, data=None, **kwargs):
        request = requests.put(url, data, **kwargs)
        status_code = request.status_code
        text = request.text
        return status_code, text

    @staticmethod
    def delete(url, **kwargs):
        request = requests.delete(url, **kwargs)
        status_code = request.status_code
        text = request.text
        return status_code, text


class ObjectNetworking:

    @staticmethod
    def get(url, class_object, params=None, **kwargs):
        request = requests.get(url, params, **kwargs)
        status_code = request.status_code
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

        if method == "post":
            resp = requests.post(url, json=payload, params=params)
        elif method == "put":
            resp = requests.put(url, json=payload, params=params)
        elif method == "delete":
            resp = requests.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        return resp

class AsyncNetworking:

    logger = logging.getLogger()

    def __init__(self):
        self.on_success_callback = None
        self.on_failure_callback = None
        self.on_exception_callback = None
        self.headers = {}

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

    def get(self, url):
        self.log("Attempting GET " + url)
        req = requests.get(url, headers=self.headers)
        return self.finish(req)

    def put(self, url, data):
        self.log("Attempting PUT " + url)
        req = requests.put(url, data=data, headers=self.headers)
        return self.finish(req)

    def post(self, url, data):
        self.log("Attempting POST " + url)
        req = requests.post(url, data=data, json=None, headers=self.headers)
        return self.finish(req)

    def delete(self, url):
        self.log("Attempting DELETE " + url)
        req = requests.delete(url, headers=self.headers)
        return self.finish(req)

    def finish(self, result):
        if result.status_code < 400:
            if self.on_success_callback is not None:
                try:
                    return self.on_success_callback(result)
                except Exception as ex:
                    if self.on_exception_callback is not None:
                        return self.on_exception_callback(ex)
        else:
            self.log(str(result.status_code) + ": " + result.text, error=True)
            if self.on_failure_callback is not None:
                try:
                    return self.on_failure_callback(result)
                except Exception as ex:
                    if self.on_exception_callback is not None:
                        return self.on_exception_callback(ex)
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self

    def log(self, message, error=False):
        if self.logger:
            if error:
                self.logger.error(message)
            else:
                self.logger.info(message)

class RateLimitedNetworking:

    def __init__(self, max_retries=3, max_requests_per_second=10, timeout=10):
        self.max_tries = max_retries
        self.max_requests_per_second = max_requests_per_second if max_requests_per_second and max_requests_per_second > 0 else None
        self.timeout = timeout
        self.requests = deque()
        self.retries = 0

    def get(self, url, is_json=False, params=None, **kwargs):
        last_status = None
        last_payload = None
        for attempt in range(self.max_tries + 1):
            self.pre_process()
            status_code, payload = JmNetwork.get(url, is_json=is_json, params=params, **kwargs)
            last_status = status_code
            last_payload = payload
            if status_code != 429:
                self.retries = 0
                return status_code, payload

            self.retries += 1
            logging.info("429 Rate limit. Retrying in %s seconds...", self.timeout)
            if attempt < self.max_tries:
                time.sleep(self.timeout)

        logging.error("429 Rate limit. Max retries (%s) reached.", self.max_tries)
        return last_status, last_payload

    def process_response(self, status_code, payload):
        if status_code == 429:
            logging.error("429 Rate limit. Max retries (%s) reached.", self.max_tries)
        return status_code, payload

    def pre_process(self):
        if not self.max_requests_per_second:
            return

        now = time.monotonic()
        while self.requests and now - self.requests[0] >= 1.0:
            self.requests.popleft()

        while len(self.requests) >= self.max_requests_per_second:
            sleep_for = 1.0 - (now - self.requests[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            while self.requests and now - self.requests[0] >= 1.0:
                self.requests.popleft()

        self.requests.append(time.monotonic())
