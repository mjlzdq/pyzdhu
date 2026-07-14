"""
HTTP 请求客户端模块 - 基于 Requests，支持自动重试与连接池复用
"""
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common.config_loader import config
from common.logger import logger


class HttpError(Exception):
    """HTTP 请求异常基类"""

    pass


class HttpTimeoutError(HttpError):
    """请求超时异常"""

    pass


class HttpMaxRetryError(HttpError):
    """达到最大重试次数异常"""

    pass


class HttpClient:
    """
    封装 Requests 的 HTTP 客户端

    特性：
    - Session 连接池复用
    - 自动重试（可配置次数和间隔）
    - 请求/响应日志
    - 超时控制
    """

    # 支持的重试状态码
    RETRYABLE_STATUS_CODES: set = frozenset({429, 500, 502, 503, 504})

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        retry: Optional[int] = None,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url or config.api_base_url
        self.timeout = timeout or config.get("api", "timeout", default=30)
        self.retry = retry or config.get("api", "retry", default=3)
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self._init_adapter()
        self._init_headers()

    def _init_adapter(self) -> None:
        """配置连接池和底层重试策略"""
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=0,  # 由上层逻辑控制重试，底层不额外重试
                connect=None,
                read=None,
                redirect=3,
                status=0,
                other=0,
            ),
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _init_headers(self) -> None:
        headers = config.get("api", "headers", default={})
        self.session.headers.update(headers)

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _should_retry(self, response: Optional[requests.Response] = None) -> bool:
        """判断是否应该重试"""
        if response is not None:
            return response.status_code in self.RETRYABLE_STATUS_CODES
        return True  # 连接异常应该重试

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """通用请求方法，支持所有 HTTP 动词与重试"""
        return self._request(method, path, **kwargs)

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        """统一请求方法，支持重试"""
        url = self._build_url(path)
        kwargs.setdefault("timeout", self.timeout)

        last_exception = None
        for attempt in range(1, self.retry + 1):
            try:
                logger.info(f"[HTTP] {method.upper()} {url} (attempt {attempt}/{self.retry})")
                start = time.time()
                response = self.session.request(method, url, **kwargs)
                elapsed = time.time() - start

                logger.info(
                    f"[HTTP] ← {response.status_code} "
                    f"({len(response.content)} bytes, {elapsed:.2f}s)"
                )

                # 服务端错误重试
                if self._should_retry(response):
                    if attempt < self.retry:
                        logger.warning(
                            f"[HTTP] 状态码 {response.status_code}，{self.retry_delay}s 后重试..."
                        )
                        time.sleep(self.retry_delay)
                        continue
                    # 最后一次重试仍返回可重试状态码，抛出异常而非返回错误响应
                    raise HttpMaxRetryError(
                        f"请求返回可重试状态码 {response.status_code}，"
                        f"已重试 {self.retry} 次: {url}"
                    )

                return response

            except requests.Timeout as e:
                last_exception = e
                logger.warning(f"[HTTP] 超时 (attempt {attempt}/{self.retry}): {e}")
                if attempt < self.retry:
                    time.sleep(self.retry_delay)

            except requests.ConnectionError as e:
                last_exception = e
                logger.warning(f"[HTTP] 连接失败 (attempt {attempt}/{self.retry}): {e}")
                if attempt < self.retry:
                    time.sleep(self.retry_delay)

            except requests.RequestException as e:
                # 非可重试异常直接抛出
                logger.error(f"[HTTP] 请求异常: {e}")
                raise HttpError(str(e)) from e

        # 所有重试耗尽
        if isinstance(last_exception, requests.Timeout):
            raise HttpTimeoutError(
                f"请求超时，已重试 {self.retry} 次: {url}"
            ) from last_exception
        raise HttpMaxRetryError(
            f"请求失败，已重试 {self.retry} 次: {url} - {last_exception}"
        ) from last_exception

    # ---- 便捷方法 ----

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("OPTIONS", path, **kwargs)

    def close(self) -> None:
        """关闭 Session，释放连接"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
