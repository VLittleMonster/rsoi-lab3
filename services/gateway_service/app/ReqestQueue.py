import requests
import time
from threading import Thread
from typing import Dict
from config.config import get_settings

GENERAL_CONFIGS = get_settings(service_config_name='general_configs')


class Request:
    def __init__(self, url, http_method, headers, data, timeout):
        self._url = url
        self._http_method = http_method
        self._headers = headers
        self._data = data
        self._timeout = timeout

    def url(self):
        return self._url

    def http_method(self):
        return self._http_method

    def headers(self):
        return self._headers

    def data(self):
        return self._data

    def timeout(self):
        return self._timeout


class RequestQueue:
    TIMEOUT = GENERAL_CONFIGS['timeout']
    _req_queue: Dict[str, Request] = {}
    _req_sender: Thread = None

    @staticmethod
    def add_http_request(url: str, http_method, headers={}, data={}, params=None, timeout=5, repeat_num=0):
        resp = requests.Response()
        resp.status_code = 503
        if repeat_num > 0:
            for i in range(repeat_num):
                try:
                    resp = http_method(url, headers=headers, json=data, params=params, timeout=timeout)
                except Exception:
                    pass
                if resp is not None and resp.status_code <= 500:
                    return resp
            resp = requests.Response()
            resp.status_code = 503
            return resp

        RequestQueue._req_queue[url + http_method.__name__] = Request(url=url, http_method=http_method, headers=headers,
                                                                      data=data, timeout=timeout)
        if RequestQueue._req_sender is None:
            RequestQueue._req_sender = Thread(target=RequestQueue._req_sending)
            RequestQueue._req_sender.start()

    @staticmethod
    def _req_sending():
        while len(RequestQueue._req_queue.keys()) > 0:
            for req_key in RequestQueue._req_queue.keys():
                Thread(target=RequestQueue._req_send, args=(req_key,)).start()
            time.sleep(RequestQueue.TIMEOUT)

        RequestQueue._req_sender = None

    @staticmethod
    def _req_send(key: str):
        req = RequestQueue._req_queue.get(key)
        if req is None:
            return

        resp = None
        try:
            resp = req.http_method()(req.url(), headers=req.headers(), json=req.data(), timeout=req.timeout())
        except Exception:
            print(f"error {req.http_method().__name__}:", req.url())
        if resp is not None and resp.status_code <= 500:
            del RequestQueue._req_queue[key]
