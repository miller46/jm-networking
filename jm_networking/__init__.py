import requests
import logging


class Network:

    logger = logging.getLogger()

    def __init__(self):
        self.on_success_callback = None
        self.on_failure_callback = None

    def on_success(self, callback):
        self.on_success_callback = callback

    def on_failure(self, callback):
        self.on_failure_callback = callback

    def get(self, url):
        self.log("Attempting GET " + url)
        req = requests.get(url)
        return self.finish(req)

    def put(self, url, data):
        self.log("Attempting PUT " + url)
        req = requests.put(url, data)
        return self.finish(req)

    def post(self, url, data):
        self.log("Attempting POST " + url)
        req = requests.post(url, data)
        return self.finish(req)

    def delete(self, url):
        self.log("Attempting DELETE " + url)
        req = requests.delete(url)
        return self.finish(req)

    def finish(self, result):
        if result.status_code < 400:
            return self.on_success_callback(result)
        else:
            self.log(result.status_code + ": " + result.text, error=True)
            return self.on_failure_callback(result)

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
