"""
工具模块 - HTTP 请求客户端（基于 Requests）
"""
import time
import requests
from common.config_loader import config
from common.logger import logger


class HttpClient:
    """封装 Requests 的 HTTP 客户端"""

    def __init__(self):
        self.base_url = config.api_base_url
        self.timeout = config.get("api", "timeout", default=30)
        self.retry = config.get("api", "retry", default=3)
        self.session = requests.Session()
        self._init_headers()

    def _init_headers(self):
        headers = config.get("api", "headers", default={})
        self.session.headers.update(headers)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """统一请求方法，支持重试"""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)

        last_exception = None
        for attempt in range(1, self.retry + 1):
            try:
                logger.info(f"[HTTP] {method.upper()} {url} (attempt {attempt})")
                start = time.time()
                response = self.session.request(method, url, **kwargs)
                elapsed = time.time() - start
                logger.info(
                    f"[HTTP] Response {response.status_code} "
                    f"in {elapsed:.2f}s"
                )
                return response
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"[HTTP] Retry {attempt}/{self.retry}: {e}")
                if attempt < self.retry:
                    time.sleep(1)
                else:
                    raise last_exception

    def get(self, path: str, **kwargs) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def close(self):
        self.session.close()
