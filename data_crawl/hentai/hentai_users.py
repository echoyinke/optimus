import re
import requests
import logging
from bs4 import BeautifulSoup
from tqdm import tqdm
import jsonlines
from time import sleep

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 创建 Session 并设置通用请求头
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def get_all_users_data(output_file):
    """ 获取 Hentai-Foundry 网站上的所有用户数据 """
    base_user_url = "https://www.hentai-foundry.com/users/byletter/"
    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["0"]  # '0'代表数字或符号
    
    with jsonlines.open(output_file, mode='a') as writer:
        for letter in letters:
            page = 1
            while True:
                page_url = f"{base_user_url}{letter}?page={page}&enterAgree=1"
                resp = session.get(page_url)
                if resp.status_code != 200:
                    logger.warning(f"请求失败: {resp.status_code}，跳过 {letter} 页 {page}")
                    break
                
                soup = BeautifulSoup(resp.text, "html.parser")
                user_links = soup.find_all('a', href=re.compile(r'/user/'))
                if not user_links:
                    logger.info(f"字母 {letter} 的第 {page} 页没有用户数据，结束该字母爬取")
                    break

                logger.info(f"开始爬取字母 {letter}，分页 {page} 的用户列表（共 {len(user_links)}）...")
                
                for a in user_links:
                    username = a.get_text(strip=True)
                    href = a['href']
                    if href.startswith("/user/") and username and href.split("/user/")[1].startswith(username):
                        user_info = get_user_info(username)
                        if user_info:
                            writer.write(user_info)  # 逐行写入 JSONLines
                        else:
                            logger.warning(f"用户 {username} 爬取失败")

                nav_text = soup.get_text()
                if re.search(r'Next\s*>', nav_text) is None:
                    logger.info(f"字母 {letter} 的第 {page} 页没有更多分页，结束该字母爬取")
                    break
                page += 1

    logger.info(f"成功爬取用户数据")

def get_user_info(username):
    """ 爬取单个用户的详细信息 """
    profile_url = f"https://www.hentai-foundry.com/user/{username}/profile?enterAgree=1"
    logger.debug(f"正在获取用户 {username} 的信息: {profile_url}")
    resp = session.get(profile_url)
    if resp.status_code != 200:
        logger.warning(f"用户 {username} 访问失败，状态码: {resp.status_code}")
        return None

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
        label_tag = soup.find("b", text=label)
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

    # 解析包含 "Fave Users" 和 "Fans" 相关信息的文本
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
output_file = "hentai_users.jsonl"
get_all_users_data(output_file)