import asyncio
from pathlib import Path
import argparse

from conf import BASE_DIR
from tencent_uploader.main import weixin_setup, TencentVideo
from utils.constant import TencentZoneTypes
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
parser.add_argument('--video-dir', default="/Users/wangzehao/project/optimus/social_auto_upload_main/videos", type=str,
                    help='video dir to upload')


def run_upload_video(cmd=None):
    args = parser.parse_args(cmd)
    upload_video(args)

def upload_video(args):
    # 获取视频文件参数路径
    filepath = args.video_dir
    account_file = Path(BASE_DIR / "tencent_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    cookie_setup = asyncio.run(weixin_setup(account_file, handle=True))
    category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = TencentVideo(title, file, tags, 0, account_file, category)
        asyncio.run(app.main(), debug=False)

if __name__ == '__main__':
    run_upload_video()
