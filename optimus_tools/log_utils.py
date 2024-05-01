# log_utils.py

import logging
import os


def get_logger(name):
    """配置并返回一个日志记录器，记录器名为给定的 name 或当前执行文件的名称。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 创建流处理器
        handler = logging.StreamHandler()
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        handler.setFormatter(formatter)
        # 添加处理器到日志记录器
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    return logger