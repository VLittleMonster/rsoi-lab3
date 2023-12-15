import requests
from CurcuitBreaker import CustomCircuitBreaker
from ReqestQueue import RequestQueue
from fastapi.responses import Response


async def get(url: str, headers={}, data={}, params=None, timeout=5):
    try:
        return CustomCircuitBreaker.send_request(url, requests.get, headers, data, params, timeout)
    except Exception as e:
        print("Exception in GET method:", e)
        return None


async def post(url: str, headers={}, data={}, params=None, timeout=5):
    try:
        return requests.post(url, headers=headers, json=data, params=params, timeout=timeout)
    except Exception as e:
        print("Exception in POST method:", e)
        return Response(status_code=503)


async def patch(url: str, headers={}, data={}, params=None, timeout=5):
    try:
        return RequestQueue.add_http_request(url, requests.patch, headers=headers, data=data, params=params, timeout=timeout, repeat_num=1)
    except Exception as e:
        print("url:", url)
        print("headers", str(headers))
        print("data:", str(data))
        print("Exception in PATCH method:", e)
        return None


def rollback(url: str, http_method, headers={}, data={}, params=None, timeout=5):
    try:
        return RequestQueue.add_http_request(url, http_method, headers=headers, data=data, params=params, timeout=timeout)
    except Exception as e:
        print("url:", url)
        print("headers", str(headers))
        print("data:", str(data))
        print(f"Exception in Rollback {http_method.__name__} method:", e)
        return None
