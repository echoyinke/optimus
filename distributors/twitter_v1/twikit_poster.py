from data_crawl.core.utils import *
import asyncio
import argparse
import datetime
import jsonlines
import os
from twikit import Client
import logging

USERNAME = "MisticWhisper"
PASSWORD = "YinKe@123"
EMAIL="kevinyinke5261@gmail.com"
PROXY = "http://127.0.0.1:4780"
client = Client('en-US', proxy=PROXY)

# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 主脚本 logger
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

def get_img_files(directory):
    """
    遍历目录，返回所有 .jpg 文件的绝对路径列表。
    """
    img_files = []
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path) and entry.lower().endswith(".jpg") or os.path.isfile(full_path) and entry.lower().endswith(".png"):
            img_files.append(full_path)
    return img_files

def load_metadata(meta_file):
    """
    读取 metadata.jsonl 文件，返回一个字典，key为图片文件名（不含后缀）。
    """
    try:
        meta_data = read_data(meta_file)
        meta = { m['image_url'].split("/")[-1].split(".")[0]: m for m in meta_data }
        logging.info(f"Loaded metadata for {len(meta)} images from {meta_file}.")
        return meta
    except Exception as e:
        logging.error(f"Error reading metadata file {meta_file}: {e}")
        return {}

def load_posted_images(posted_state_file):
    """
    从已发布状态文件中加载已发布图片的文件名集合。
    如果文件不存在则返回空集合。
    """
    posted_images = set()
    if os.path.exists(posted_state_file):
        try:
            with jsonlines.open(posted_state_file, mode='r') as reader:
                for entry in reader:
                    posted_images.add(entry["img_name"])
            logging.info(f"Loaded {len(posted_images)} previously posted images from {posted_state_file}.")
        except Exception as e:
            logging.error(f"Error reading posted state file: {e}")
    else:
        logging.info("No posted state file found, starting fresh.")
    return posted_images

async def ensure_login(cookies_path):
    """
    确保登录状态有效，尝试加载 cookies。
    如果 cookies 不存在或无效，则进行重新登录，并保存新的 cookies。
    """
    try:
        if os.path.exists(cookies_path):
            client.load_cookies(cookies_path)
            logging.info("Reloaded cookies before posting.")

            # 检测 cookies 是否有效
            try:
                await client.get_trends('trending')
                logging.info("Cookies are valid after loading.")
                return
            except Exception as e:
                logging.warning(f"Cookie authentication failed: {e}. Attempting fresh login.")

        # 如果 cookies 无效或不存在，重新登录
        await client.login(auth_info_1=USERNAME, password=PASSWORD)
        client.save_cookies(cookies_path)
        logging.info("Successfully logged in and saved cookies.")
    except Exception as e:
        logging.error(f"Login process failed: {e}")

def configure_logging(logs_folder):
    """
    配置日志记录到文件，同时保留控制台输出，日志文件将存放在 logs_folder 下。
    """
    log_file_path = os.path.join(logs_folder, "log.txt")
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(file_handler)

async def post_tweets(images_folder, interval):
    meta_file = os.path.join(images_folder, "metadata.jsonl")
    posted_state_file = os.path.join(images_folder, "posted_state.jsonl")
    cookies_path = os.path.join(images_folder, "cookies.json")

    configure_logging(images_folder)

    meta = load_metadata(meta_file)
    img_files = get_img_files(images_folder)
    logging.info(f"Found {len(img_files)} image files in {images_folder}.")

    posted_images = load_posted_images(posted_state_file)

    # 打开状态文件，追加模式记录每次发布的信息
    with jsonlines.open(posted_state_file, mode='a') as writer:
        for img_file in img_files:
            img_name = os.path.splitext(os.path.basename(img_file))[0]

            if img_name in posted_images:
                logging.info(f"Skipping already posted image: {img_name}")
                continue

            # 跳过超过 5MB 的图片
            if os.path.getsize(img_file) > 5242880:
                logging.warning(f"Skipping {img_file}, as it exceeds 5MB limit.")
                continue

            # 每次发布前调用登录验证函数，确保 cookies 有效
            await ensure_login(cookies_path)

            meta_info = meta.get(img_name, {"title": "", "description": ""})
            title = f"{meta_info['title']}"
            logging.info(f"Preparing to post tweet for {img_name}, tweet_text: {title}")

            media_id = await client.upload_media(img_file)
            logging.info(f"Uploaded media: {img_file} (Media ID: {media_id})")

            await client.create_tweet(text=title, media_ids=[media_id])
            logging.info(f"Tweet posted successfully for {img_file}.")

            # 记录发布状态：图片名称、UTC时间、发布文本
            post_details = {
                "img_name": img_name,
                "img_file": img_file,
                "title": f"{meta_info['title']}",
                "description": f"{meta_info['description']}"
            }
            writer.write(post_details)

            logging.info(f"Waiting for {interval} seconds before next tweet...")
            await asyncio.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Automatically post images as tweets from a given directory.")
    parser.add_argument("--path", type=str, required=True, help="Path to the directory containing images.")
    parser.add_argument("--interval", type=int, default=300, help="Interval between tweets in seconds (default: 300).")
    args = parser.parse_args()

    images_folder = args.path
    
    asyncio.run(post_tweets(images_folder, args.interval))

if __name__ == '__main__':
    main()