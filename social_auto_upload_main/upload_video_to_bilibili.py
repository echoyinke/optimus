import time
from pathlib import Path
import argparse

from bilibili_uploader.main import read_cookie_json_file, extract_keys_from_json, random_emoji, BilibiliUploader
from conf import BASE_DIR
from utils.constant import VideoZoneTypes
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

parser = argparse.ArgumentParser("upload_video_to_douyin")
parser.add_argument('--video-dir', default="D:/PyProj/optimus/social_auto_upload_main/videos", type=str,
                    help='video dir to upload')

def run_upload_video(cmd=None):
    args = parser.parse_args(cmd)
    upload_video(args)

def upload_video(args):
    # 获取视频文件参数路径
    filepath = args.video_dir
    # how to get cookie, see the file of get_bilibili_cookie.py.
    account_file = Path(BASE_DIR / "bilibili_uploader" / "account.json")
    if not account_file.exists():
        print(f"{account_file.name} 配置文件不存在")
        exit()
    cookie_data = read_cookie_json_file(account_file)
    cookie_data = extract_keys_from_json(cookie_data)

    tid = VideoZoneTypes.SPORTS_FOOTBALL.value  # 设置分区id
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    if file_num == 0:
        logger.info(f"No video found in {folder_path}...")
        return
    logger.info(f"Starting run run_upload_video {folder_path}")

    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        # just avoid error, bilibili don't allow same title of video.
        title += random_emoji()
        tags_str = ','.join([tag for tag in tags])
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        # I set desc same as title, do what u like.
        desc = title
        bili_uploader = BilibiliUploader(cookie_data, file, title, desc, tid, tags, None)
        bili_uploader.upload()

        # life is beautiful don't so rush. be kind be patience
        time.sleep(30)

if __name__ == '__main__':
    run_upload_video()
