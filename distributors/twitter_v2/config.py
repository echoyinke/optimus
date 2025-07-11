#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 自动化脚本配置文件
包含账号信息、代理设置等配置项
"""

# Twitter 账号配置
TWITTER_CONFIG = {
    "USERNAME": "rkzsv53451283",
    "EMAIL": "sweetbrittny1980555@hotmail.com", 
    "PASSWORD": "6DNrmHtSRX0812",
    "TOTP_SECRET": "BUFU53PISNGHZMTS"  # 2FA后的TOTP秘钥
}

# 代理配置
PROXY_CONFIG = {
    "PROXY": "socks5://127.0.0.1:4781",  # 要挂代理，否则会出现`httpx.ConnectTimeout` 的问题
    "USE_PROXY": True  # 是否使用代理
}

# 浏览器配置
BROWSER_CONFIG = {
    "HEADLESS": True,  # 是否无头模式（服务器环境必须设置为True）
    "VIEWPORT": {'width': 1366, 'height': 768},
    "USER_AGENT": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

# 目录配置
DIRECTORIES = {
    "DATA_DIR": "inputs/twitter/data",           # 数据文件目录
    "PROGRESS_DIR": "outputs/twitter/progress",   # 进度文件目录（断点恢复）
    "RESULTS_DIR": "outputs/twitter/results",     # 结果文件目录
    "COOKIES_DIR": "outputs/twitter/cookies",     # Cookie文件目录
    "ERROR_HTML_DIR": "outputs/twitter/error_html"  # 错误页面保存目录
}

# 文件路径配置
FILE_CONFIG = {
    "USERS_FILE": "inputs/twitter/data/top_users.json",  # 用户列表文件
    "COMMENT_TEXT_FILE": "inputs/twitter/data/comment_text_list.json",  # 评论内容文件
    "TWEET_CONTENT_FILE": "inputs/twitter/data/tweet_content_list.json",  # 推文内容文件
    "TARGET_USERS_FILE": "inputs/twitter/data/target_users_follow.json",  # 目标用户列表文件（关注功能）
    "COMMENT_PROGRESS_FILE": "outputs/twitter/progress/comment_progress.json",  # 评论进度记录文件
    "TWEET_PROGRESS_FILE": "outputs/twitter/progress/tweet_progress.json",  # 推文进度记录文件
    "FOLLOW_PROGRESS_FILE": "outputs/twitter/progress/follow_progress.json",  # 关注进度记录文件
}

# 行为模拟配置
BEHAVIOR_CONFIG = {
    "MIN_WAIT": 2,  # 最小等待时间（秒）
    "MAX_WAIT": 5,  # 最大等待时间（秒）
    "COMMENT_DELAY_MIN": 20,  # 评论成功后最小延迟（秒）
    "COMMENT_DELAY_MAX": 40,  # 评论成功后最大延迟（秒）
    "USER_DELAY_MIN": 5,   # 用户间最小延迟（秒）
    "USER_DELAY_MAX": 15,  # 用户间最大延迟（秒）
    "TWEET_DELAY_MIN": 6,  # 推文间最小延迟（秒）
    "TWEET_DELAY_MAX": 18,  # 推文间最大延迟（秒）
    "FOLLOW_DELAY_MIN": 5,   # 关注成功后最小延迟（秒）
    "FOLLOW_DELAY_MAX": 15,  # 关注成功后最大延迟（秒）
    "TARGET_USER_DELAY_MIN": 30,  # 目标用户间最小延迟（秒）
    "TARGET_USER_DELAY_MAX": 60   # 目标用户间最大延迟（秒）
}

# 获取配置的便捷函数
def get_twitter_config():
    """获取Twitter账号配置"""
    return TWITTER_CONFIG

def get_proxy_config():
    """获取代理配置"""
    return PROXY_CONFIG

def get_browser_config():
    """获取浏览器配置"""
    return BROWSER_CONFIG

def get_directories():
    """获取目录配置"""
    return DIRECTORIES

def get_file_config():
    """获取文件路径配置"""
    return FILE_CONFIG

def get_behavior_config():
    """获取行为模拟配置"""
    return BEHAVIOR_CONFIG

def get_cookies_file_path(username=None):
    """获取Cookie文件路径，支持多账号"""
    if username is None:
        username = TWITTER_CONFIG["USERNAME"]
    
    directories = get_directories()
    cookies_dir = directories["COOKIES_DIR"]
    return f"{cookies_dir}/{username}_cookies.json" 