import requests
from CurcuitBreaker import CustomCircuitBreaker
from ReqestQueue import RequestQueue
from fastapi.responses import Response


async def get(url: str, headers={}, data={}, timeout=5):
    try:
        return CustomCircuitBreaker.send_request(url, requests.get, headers, data, timeout)
    except Exception as e:
        print("Exception in GET method:", e)
        return None


async def post(url: str, headers={}, data={}, timeout=5):
    try:
        return requests.post(url, headers=headers, json=data, timeout=timeout)
    except Exception as e:
        print("Exception in POST method:", e)
        return Response(status_code=503)


async def patch(url: str, headers={}, data={}, timeout=5, is_get=False):
    try:
        if is_get:
            return CustomCircuitBreaker.send_request(url, requests.patch, headers, data, timeout)
        return RequestQueue.add_http_request(url, requests.patch, headers=headers, data=data, timeout=timeout, repeat_num=1)
    except Exception as e:
        print("url:", url)
        print("headers", str(headers))
        print("data:", str(data))
        print("Exception in PATCH method:", e)
        return None


def rollback(url: str, http_method, headers={}, data={}, timeout=5):
    try:
        return RequestQueue.add_http_request(url, http_method, headers=headers, data=data, timeout=timeout)
    except Exception as e:
        print("url:", url)
        print("headers", str(headers))
        print("data:", str(data))
        print(f"Exception in Rollback {http_method.__name__} method:", e)
        return None
