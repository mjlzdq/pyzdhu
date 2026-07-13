"""
单元测试 - HttpClient HTTP 客户端

测试：
- 请求方法（GET/POST/PUT/PATCH/DELETE）
- 重试逻辑
- 超时处理
- 异常场景
- URL 构建
- Session 管理
"""
from unittest.mock import patch, MagicMock

import pytest
import requests

from common.http_client import (
    HttpClient, HttpError, HttpTimeoutError, HttpMaxRetryError,
)


pytestmark = pytest.mark.unit


class TestHttpClientInit:
    """初始化测试"""

    def test_default_init(self):
        client = HttpClient()
        assert client.base_url is not None
        assert client.timeout == 30
        assert client.retry == 3
        client.close()

    def test_custom_init(self):
        client = HttpClient(
            base_url="https://example.com",
            timeout=10,
            retry=2,
            retry_delay=0.5,
        )
        assert client.base_url == "https://example.com"
        assert client.timeout == 10
        assert client.retry == 2
        assert client.retry_delay == 0.5
        client.close()

    def test_context_manager(self):
        with HttpClient() as client:
            assert client.base_url is not None
        # 确保 __exit__ 不会报错


class TestHttpClientUrlBuilding:
    """URL 构建测试"""

    def test_build_url_simple_path(self):
        client = HttpClient(base_url="https://api.example.com")
        url = client._build_url("/posts")
        assert url == "https://api.example.com/posts"
        client.close()

    def test_build_url_trailing_slash_in_base(self):
        client = HttpClient(base_url="https://api.example.com/")
        url = client._build_url("/posts")
        assert url == "https://api.example.com/posts"
        client.close()

    def test_build_url_no_leading_slash(self):
        client = HttpClient(base_url="https://api.example.com")
        url = client._build_url("posts/1")
        assert url == "https://api.example.com/posts/1"
        client.close()

    def test_build_url_full_url_passthrough(self):
        client = HttpClient(base_url="https://api.example.com")
        url = client._build_url("https://other.com/api")
        assert url == "https://other.com/api"
        client.close()


class TestHttpClientMethods:
    """HTTP 方法测试（mocked）"""

    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://test.example.com", timeout=5)

    @pytest.fixture
    def mock_response(self):
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.content = b'{"ok": true}'
        resp.json.return_value = {"ok": True}
        return resp

    def test_get(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response) as mock_req:
            resp = client.get("/posts")
            mock_req.assert_called_once()
            assert resp.status_code == 200
            assert resp.json() == {"ok": True}

    def test_post_with_json(self, client, mock_response):
        mock_response.status_code = 201
        with patch.object(client.session, "request", return_value=mock_response) as mock_req:
            resp = client.post("/posts", json={"title": "test"})
            call_kwargs = mock_req.call_args.kwargs
            assert call_kwargs["json"] == {"title": "test"}
            assert resp.status_code == 201

    def test_put(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response):
            resp = client.put("/posts/1", json={"title": "updated"})
            assert resp.status_code == 200

    def test_patch(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response):
            resp = client.patch("/posts/1", json={"title": "patched"})
            assert resp.status_code == 200

    def test_delete(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response):
            resp = client.delete("/posts/1")
            assert resp.status_code == 200

    def test_head(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response):
            resp = client.head("/posts")
            assert resp.status_code == 200

    def test_options(self, client, mock_response):
        with patch.object(client.session, "request", return_value=mock_response):
            resp = client.options("/posts")
            assert resp.status_code == 200


class TestHttpClientRetry:
    """重试逻辑测试"""

    def test_retry_on_server_error(self):
        """服务端 500 错误应触发重试"""
        client = HttpClient(base_url="https://test.example.com", timeout=5, retry=3, retry_delay=0.01)

        error_resp = MagicMock(spec=requests.Response)
        error_resp.status_code = 500
        error_resp.content = b"Internal Server Error"

        success_resp = MagicMock(spec=requests.Response)
        success_resp.status_code = 200
        success_resp.content = b'{"ok": true}'

        with patch.object(client.session, "request", side_effect=[error_resp, success_resp]) as mock_req:
            resp = client.get("/test")
            assert mock_req.call_count == 2
            assert resp.status_code == 200

        client.close()

    def test_retry_on_connection_error(self):
        """连接错误应触发重试"""
        client = HttpClient(base_url="https://test.example.com", timeout=5, retry=3, retry_delay=0.01)

        success_resp = MagicMock(spec=requests.Response)
        success_resp.status_code = 200
        success_resp.content = b"ok"

        with patch.object(
            client.session, "request",
            side_effect=[requests.ConnectionError("fail"), success_resp],
        ) as mock_req:
            resp = client.get("/test")
            assert mock_req.call_count == 2
            assert resp.status_code == 200

        client.close()

    def test_max_retry_exceeded(self):
        """超过最大重试次数应抛出异常"""
        client = HttpClient(base_url="https://test.example.com", timeout=5, retry=2, retry_delay=0.01)

        with patch.object(
            client.session, "request",
            side_effect=requests.ConnectionError("always fail"),
        ):
            with pytest.raises(HttpMaxRetryError, match="已重试"):
                client.get("/test")

        client.close()

    def test_timeout_retry(self):
        """超时应触发重试"""
        client = HttpClient(base_url="https://test.example.com", timeout=5, retry=3, retry_delay=0.01)

        success_resp = MagicMock(spec=requests.Response)
        success_resp.status_code = 200
        success_resp.content = b"ok"

        with patch.object(
            client.session, "request",
            side_effect=[requests.Timeout("timeout"), success_resp],
        ) as mock_req:
            resp = client.get("/test")
            assert mock_req.call_count == 2
            assert resp.status_code == 200

        client.close()

    def test_non_retryable_exception(self):
        """非可重试异常应直接抛出"""
        client = HttpClient(base_url="https://test.example.com", timeout=5, retry=3, retry_delay=0.01)

        with patch.object(
            client.session, "request",
            side_effect=requests.TooManyRedirects("redirect loop"),
        ):
            with pytest.raises(HttpError):
                client.get("/test")

        client.close()


class TestHttpClientShouldRetry:
    """_should_retry 方法测试"""

    def test_should_retry_500(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 500
        assert client._should_retry(resp) is True
        client.close()

    def test_should_retry_502(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 502
        assert client._should_retry(resp) is True
        client.close()

    def test_should_retry_503(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 503
        assert client._should_retry(resp) is True
        client.close()

    def test_should_not_retry_200(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        assert client._should_retry(resp) is False
        client.close()

    def test_should_not_retry_404(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 404
        assert client._should_retry(resp) is False
        client.close()

    def test_should_retry_429(self):
        client = HttpClient()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 429
        assert client._should_retry(resp) is True
        client.close()
