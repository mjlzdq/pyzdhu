"""
工具模块 - 日志器
"""
import inspect
import logging
import sys


def get_logger(name: str = "AutoTest") -> logging.Logger:
    """获取指定名称的 Logger；若未指定名称，默认使用调用模块的 __name__。"""
    if name == "AutoTest":
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_name = frame.f_back.f_globals.get("__name__")
            if caller_name and caller_name != __name__:
                name = caller_name
            del frame

    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # 控制台 handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console.setFormatter(fmt)
        logger.addHandler(console)

    return logger


# 向后兼容：模块级默认 logger
logger = get_logger("AutoTest")
