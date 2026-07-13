"""
单元测试 - Logger 日志模块

测试：
- 基本日志输出
- 多个 logger 实例
- 日志级别
- Handler 不重复
"""
import logging

from common.logger import get_logger, logger


class TestLogger:
    """日志模块测试"""

    def test_default_logger_exists(self):
        """全局 logger 存在"""
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        """默认名称为 AutoTest"""
        assert logger.name == "AutoTest"

    def test_logger_has_handlers(self):
        """logger 至少有一个 handler"""
        assert len(logger.handlers) > 0

    def test_get_logger_returns_logger(self):
        """get_logger 返回 Logger 实例"""
        l = get_logger("TestLogger")
        assert isinstance(l, logging.Logger)
        assert l.name == "TestLogger"

    def test_get_logger_no_duplicate_handlers(self):
        """多次调用 get_logger 不会重复添加 handler"""
        l = get_logger("DedupTest")
        handler_count = len(l.handlers)
        l2 = get_logger("DedupTest")
        # 同一个名字应该返回同一个 logger，handler 数不变
        assert len(l2.handlers) == handler_count
        assert l is l2

    def test_logger_can_log(self):
        """logger 可以正常输出日志"""
        l = get_logger("FunctionalTest")
        # 不应抛出异常
        l.debug("debug message")
        l.info("info message")
        l.warning("warning message")
        l.error("error message")

    def test_different_names_get_different_loggers(self):
        """不同名称返回不同 logger"""
        l1 = get_logger("LoggerA")
        l2 = get_logger("LoggerB")
        assert l1 is not l2
        assert l1.name == "LoggerA"
        assert l2.name == "LoggerB"
