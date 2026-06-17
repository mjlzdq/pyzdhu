"""
工具模块 - 日志器
"""
import logging
import sys


def get_logger(name: str = "AutoTest") -> logging.Logger:
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


logger = get_logger()
