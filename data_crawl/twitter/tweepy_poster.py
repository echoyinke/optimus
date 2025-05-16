import tweepy
from optimus_tools.data_utils import read_data
import argparse
import datetime
import jsonlines
import os
import logging
import time

consumer_key = "ttIsoieImpph9gTf6Z0mZO1Fx"
consumer_secret = "4yHz519Gkl10hJcAIQT734JOsVG1AF3MPOVOWoekaxFbOn6ZzP"
access_token = "1729145294607032320-kPYch64Gpbr1vbUZz1rDH4UUTvEbX6"
access_token_secret = "D60VpJUYZnr6MQKe7gV2NxXjSohkLMEfZILqMfl6sjriD"
PROXY={
        'http': 'http://127.0.0.1:4780',
        'https': 'http://127.0.0.1:4780',
    }

# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 主脚本 logger
logger = logging.getLogger(__name__)
def config_log_path(logs_folder):
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

    logger.info("\n\n" + "#" * 160)
    logger.info(f"New tweet run started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Shanghai Time)")
    logger.info(f"Logging to: {log_file_path}\n")
    logger.info("#" * 80 + "\n\n")

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
        logger.info(f"Loaded metadata for {len(meta)} images from {meta_file}.")
        return meta
    except Exception as e:
        logger.error(f"Error reading metadata file {meta_file}: {e}")
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
            logger.info(f"Loaded {len(posted_images)} previously posted images from {posted_state_file}.")
        except Exception as e:
            logger.error(f"Error reading posted state file: {e}")
    else:
        logger.info("No posted state file found, starting fresh.")
    return posted_images
def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret) -> tweepy.API:
    """Get twitter conn 1.1"""

    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(
        access_token,
        access_token_secret,
    )
    api = tweepy.API(auth)
    api.session.proxies = PROXY
    return api

def get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret) -> tweepy.Client:
    """Get twitter conn 2.0"""

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    client.session.proxies = PROXY

    return client

# client_v1 = get_twitter_conn_v1(consumer_key, consumer_secret, access_token, access_token_secret)
# client_v2 = get_twitter_conn_v2(consumer_key, consumer_key, access_token, access_token_secret)

# media_path = "path_to_media"
# media = client_v1.media_upload(filename=media_path)
# media_id = media.media_id

# client_v2.create_tweet(text="Tweet text", media_ids=[media_id])

    

def post_tweets(images_folder, interval):
    config_log_path(images_folder)
    img_files = get_img_files(images_folder)
    logger.info(f"Found {len(img_files)} image files in {images_folder}.")

    pic_meta_all = load_metadata(os.path.join(images_folder, "metadata.jsonl"))
    post_offset=os.path.join(images_folder, "post_offset.jsonl")
    posted_images = load_posted_images(post_offset)


    client_v1 = get_twitter_conn_v1(consumer_key, consumer_secret, access_token, access_token_secret)
    client_v2 = get_twitter_conn_v2(consumer_key, consumer_secret, access_token, access_token_secret)

    # 打开状态文件，追加模式记录每次发布的信息
    with jsonlines.open(post_offset, mode='a') as writer:
        for img_file in img_files:
            img_name = os.path.splitext(os.path.basename(img_file))[0]

            if img_name in posted_images:
                logger.info(f"Skipping already posted image: {img_name}")
                continue

            # 跳过超过 5MB 的图片
            if os.path.getsize(img_file) > 5242880:
                logger.warning(f"Skipping {img_file}, as it exceeds 5MB limit.")
                continue

            meta_info = pic_meta_all.get(img_name, {"title": "", "description": ""})
            title = f"{meta_info['title']}"
            logger.info(f"Preparing to post tweet for {img_file}, \ntweet_text: {title}")

            media = client_v1.media_upload(filename=img_file)
            media_id = media.media_id
            logger.info(f"Uploaded media: {img_file} (Media ID: {media_id})")

            response=client_v2.create_tweet(text=title, media_ids=[media_id])
            tweet_id=response.data['id']
            logger.info(f"Tweet: {tweet_id} posted successfully for {img_file}.")

            # 记录发布状态：图片名称、UTC时间、发布文本
            post_details = {
                "tweet_id": tweet_id,
                "img_name": img_name,
                "img_file": img_file,
                "title": f"{meta_info['title']}",
                "description": f"{meta_info['description']}",
                "post_date": (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            }
            writer.write(post_details)

            logger.info(f"Waiting for {interval} seconds before next tweet...")
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Automatically post images as tweets from a given directory.")
    parser.add_argument("--path", type=str, required=True, help="Path to the directory containing images.")
    parser.add_argument("--interval", type=int, default=6120, help="Interval between tweets in seconds (post rate limit is 17 requests / 24 hours(about 1.4 hour one request).")
    args = parser.parse_args()

    images_folder = args.path
    
    post_tweets(images_folder, args.interval)

if __name__ == '__main__':
    main()