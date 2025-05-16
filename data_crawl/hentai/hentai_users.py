import re
import requests
import logging
from bs4 import BeautifulSoup
from tqdm import tqdm
import jsonlines
import json
from time import sleep
import os
import concurrent.futures
import traceback
import time
import sys
import random
from fake_useragent import UserAgent

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 创建 Session 并设置通用请求头
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# 增大连接池，防止 "Connection pool is full"
# 配置 Session 进行重试
retry_strategy = Retry(
    total=3,  # 最大重试次数
    backoff_factor=30,  # 重试间隔：1秒，2秒，4秒...
    status_forcelist=[500, 502, 503, 504],  # 只在服务器错误时重试
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)



def get_existing_users_for_letter(data_file):
    """ 获取已爬取的用户列表 """
    os.makedirs(os.path.dirname(data_file), exist_ok=True)  # 确保路径存在
    if not os.path.exists(data_file):
        os.makedirs(os.path.dirname(data_file), exist_ok=True)  # 确保路径存在
        return set(), 1
    
    existing_users = set()
    with jsonlines.open(data_file, mode='r') as reader:
        last_page=1
        for obj in reader:
            if "username" in obj:
                existing_users.add(obj["username"])
                last_page=obj["page"]
    return existing_users, last_page

def crawl_letter_data(letter):
    """ 爬取指定字母的用户数据，并记录到独立的日志文件 """
    base_user_url = f"https://www.hentai-foundry.com/users/byletter/{letter}"
    data_file = f"./outputs/user_info/letter_{letter}.jsonl"
    log_file = f"./outputs/logs/letter_{letter}.log"
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 配置该线程的日志文件
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    thread_logger = logging.getLogger(f"logger_{letter}")
    thread_logger.setLevel(logging.INFO)
    thread_logger.addHandler(file_handler)

    existing_users, last_page = get_existing_users_for_letter(data_file)

    with jsonlines.open(data_file, mode='a') as writer:
        page = last_page
        thread_logger.info(f"letter {letter} resume from page: {page}")
        while page < 500: # 只爬去前500页
            page_url = f"{base_user_url}?page={page}&enterAgree=1"
            resp = session.get(page_url, headers={"User-Agent": UserAgent().random, "Accept-Language": "en-US,en;q=0.9"})  # 使用通用重试机制
            soup = BeautifulSoup(resp.text, "html.parser")
            user_links = soup.find_all('a', href=re.compile(r'/user/'))
            thread_logger.info(f"开始爬取字母 {letter}，分页 {page} 的用户列表（共 {len(user_links)}）...")

            for a in user_links:
                username = a.get_text(strip=True)
                href = a['href']
                if href.startswith("/user/") and username and href.split("/user/")[1].startswith(username) and username != 'Sticky':
                    if username in existing_users:
                        thread_logger.info(f"bypass existing username {username} ...")
                        continue
                    user_info = get_user_info(username)
                    if user_info:
                        user_info['page']=page
                        writer.write(user_info)
                        existing_users.add(username)  # 逐行写入 JSONLines
                    else:
                        thread_logger.warning(f"用户 {username} 爬取失败")


            next_page = soup.find("a", string="Next >")

            if next_page:
                next_href = next_page.get("href")
                match = re.search(r'/page/(\d+)', next_href)                
                if match:
                    next_page_number = int(match.group(1))
                    if next_page_number <= page:  # "Next >" 指向当前页或更小，说明是最后一页
                        next_page = None

            if not next_page:
                thread_logger.info(f"结束爬取到字母 {letter}，在最后分页 {page} 的，共爬取{len(existing_users)}...")
                break
            else:
                page += 1  # 进入下一页

    # 释放日志 handler，防止重复日志
    thread_logger.removeHandler(file_handler)
    file_handler.close()

def get_all_users_data():
    """ 使用多线程并行爬取不同字母的用户数据 """
    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["0"]
    # letters = ["A"]

    # max_workers = len(letters)
    max_workers = 8

    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_letter_data, letter): letter for letter in letters}

        for future in concurrent.futures.as_completed(futures):
            letter = futures[future]
            try:
                future.result()  # 获取执行结果，如果有异常会抛出
            except Exception as e:
                logger.exception(f"字母 {letter} 爬取过程中出现异常")  # 自动记录 traceback

    logger.info("所有字母数据爬取完成")

def get_user_info(username):
    """ 随机睡眠，减小压力 """
    time.sleep(random.uniform(0, 3))
    profile_url = f"https://www.hentai-foundry.com/user/{username}/profile?enterAgree=1"
    logger.debug(f"正在获取用户 {username} 的信息: {profile_url}")
    resp = session.get(profile_url, headers={"User-Agent": UserAgent().random, "Accept-Language": "en-US,en;q=0.9"})

    soup = BeautifulSoup(resp.text, "html.parser")
    
    user_data = {}

    # 用户名
    profile_name = soup.find('h1')
    user_data['username'] = profile_name.get_text(strip=True) if profile_name else username

    # 解析基本信息字段
    info_labels = {
        "Date Joined": "date_joined",
        "Last Updated": "last_updated",
        "Last visit": "last_visit",
        "Gender": "gender",
        "Occupation": "occupation",
        "# Pictures": "pictures_count",
        "# Comments Given": "comments_given"
    }

    for label, key in info_labels.items():
        label_tag = soup.find("b", string=label)
        user_data[key] = ""
        if label_tag:
            parent_td = label_tag.find_parent("td")
            if parent_td:
                next_td = parent_td.find_next_sibling("td")
                if next_td:
                    user_data[key] = next_td.get_text(strip=True)

    # 提取 Fave Users 和 Fans 的数量
    user_data['fans_count'] = 0
    user_data['fave_count'] = 0

    count_texts = [text for text in soup.stripped_strings if "Fave Users" in text or "Fans" in text]

    for text in count_texts:
        if "Fave Users" in text:
            match = re.search(r'Fave Users \((\d+)\)', text)
            if match:
                user_data['fave_count'] = int(match.group(1))
        elif "Fans" in text:
            match = re.search(r'Fans \((\d+)\)', text)
            if match:
                user_data['fans_count'] = int(match.group(1))

    # 个人简介
    user_data['bio'] = ""
    bio_section = soup.find("div", class_="user-bio")
    if bio_section:
        user_data['bio'] = bio_section.get_text(strip=True)
    else:
        profile_text = soup.get_text(separator=" ", strip=True)
        match = re.search(r'Member Info\s*(.*?)\s*Recent Pictures', profile_text)
        if match:
            user_data['bio'] = match.group(1).strip()

    # 社交链接/联系方式
    user_data['social_links'] = []
    profile_links = soup.find_all('a', href=True)
    for a in profile_links:
        href = a['href']
        if href.startswith("http") and "hentai-foundry.com" not in href:
            user_data['social_links'].append(href.strip())

    user_data['social_links'] = list(set(user_data['social_links']))  # 去重
    
    return user_data

# 执行爬取任务
logger.info("开始获取所有用户数据...")
get_all_users_data()