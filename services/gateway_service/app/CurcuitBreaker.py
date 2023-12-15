import requests
import time
from threading import Thread
from config.config import get_settings

GENERAL_CONFIGS = get_settings(service_config_name='general_configs')


class CustomCircuitBreaker:
    FAILURE_THRESHOLD = GENERAL_CONFIGS['max_num_of_fails']
    RECOVERY_TIMEOUT = GENERAL_CONFIGS['timeout']

    _fail_statistic = {}
    _service_state = {}
    _waiter: Thread = None

    @staticmethod
    def send_request(url: str, http_method, headers={}, data={}, params=None, timeout=5):
        resp = requests.Response()
        resp.status_code = 503
        if http_method is None:
            return resp

        host_url = url[url.find('://') + 3:]
        host_url = host_url[:host_url.find('/')]

        state = CustomCircuitBreaker._service_state.get(host_url)
        if state == "unavailable":
            print(f"Service {host_url} is unavailable")
            return resp

        for i in range(CustomCircuitBreaker.FAILURE_THRESHOLD + 1):
            try:
                resp = http_method(url, headers=headers, json=data, params=params, timeout=timeout)
            except Exception:
                pass

            if resp is not None and resp.status_code < 500:
                return resp

            fail_num = CustomCircuitBreaker._fail_statistic.get(host_url)
            if fail_num is None:
                CustomCircuitBreaker._fail_statistic[host_url] = 1
            else:
                CustomCircuitBreaker._fail_statistic[host_url] += 1

        fail_num = CustomCircuitBreaker._fail_statistic.get(host_url)
        if fail_num is not None and fail_num > CustomCircuitBreaker.FAILURE_THRESHOLD:
            CustomCircuitBreaker._fail_statistic[host_url] = 0
            CustomCircuitBreaker._service_state[host_url] = "unavailable"
            if CustomCircuitBreaker._waiter is None:
                CustomCircuitBreaker._waiter = Thread(target=CustomCircuitBreaker._wait_for_available)
                CustomCircuitBreaker._waiter.start()
            print(f"CustomCircuitBreaker: num of fails for {host_url} is overflow")
            return resp

        return resp

    @staticmethod
    def _wait_for_available():
        is_end = False
        while not is_end:
            time.sleep(CustomCircuitBreaker.RECOVERY_TIMEOUT)
            is_end = True
            for host_url in CustomCircuitBreaker._service_state.keys():
                if CustomCircuitBreaker._service_state[host_url] == "unavailable":
                    is_end = False
                    Thread(target=CustomCircuitBreaker._check_service_health, args=(host_url,)).start()
        CustomCircuitBreaker._waiter = None

    @staticmethod
    def _check_service_health(host_url):
        resp = None
        url = 'http://' + host_url + '/manage/health'
        try:
            resp = requests.get(url, timeout=5)
        except Exception:
            print("error health:", url)
        if resp is not None and resp.status_code == 200:
            CustomCircuitBreaker._service_state[host_url] = "available"
