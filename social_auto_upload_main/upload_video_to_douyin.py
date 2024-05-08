import asyncio
from pathlib import Path
import sys
import argparse

from conf import BASE_DIR
from douyin_uploader.main import douyin_setup, DouYinVideo
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags
import logging
logger = logging.getLogger(__name__)
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
# import os
# os.environ['EDR_BLOCK_PATH'] = "D:\playwright_browser\chromium-1112\chrome-win\chrome.exe"
parser = argparse.ArgumentParser("upload_video_to_douyin")
parser.add_argument('--video-dir', default="D:/PyProj/optimus/social_auto_upload_main/videos", type=str,
                    help='video dir to upload')
def run_upload_video(cmd=None):
    args = parser.parse_args(cmd)
    upload_video(args)

def upload_video(args):
    # 获取视频文件参数路径
    filepath = args.video_dir
    account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    if file_num == 0:
        logger.info(f"No video found in {folder_path}...")
        return
    logger.info(f"Starting run run_upload_video {folder_path}")
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
    # cookie_setup = asyncio.run(douyin_setup(account_file, handle=False))
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        cover_file_path = str(file).replace(".mp4",".jpg")
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file, cover_file_path)
        asyncio.run(app.main(), debug=False)

if __name__ == '__main__':

    run_upload_video()