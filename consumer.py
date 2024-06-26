import json
import os
import sys
import time

project_abs_path = os.getcwd()
env_path_list = [
    os.path.join(project_abs_path, 'funclip_main'),
    os.path.join(project_abs_path, 'funclip_main/funclip/'),
    os.path.join(project_abs_path, 'social_auto_upload_main'),
    os.path.join(project_abs_path, 'social_auto_upload_main/douyin_uploader')
]
for env_path in env_path_list:
    sys.path.append(env_path)
os.chdir(os.path.join(project_abs_path, 'funclip_main'))
# print(f"after change dir：{os.getcwd()}")
from GPT_SoVITS_main.book_to_chunk import split_book_into_chunk
from funclip_main.funclip.videoclipper import main as funclip_main
os.chdir(project_abs_path)
from optimus_tools.ffmpeg_utils import merge_video_audio_subtitle, win_dir_cvt
from social_auto_upload_main.cookie_setup import douyin_cookie_setup
from optimus_tools.http_utils import send_dingtalk

os.chdir(os.path.join(project_abs_path, 'social_auto_upload_main'))
from social_auto_upload_main.upload_video_to_douyin import run_upload_video
os.chdir(project_abs_path)

from optimus_tools.log_utils import get_logger
import subprocess
logger = get_logger(os.path.basename(__file__))



consum_dir = "D:\\temp_medias\\binglinchengxia\\兵临城下"
video_path = "D:/temp_medias/jieya_video/jieya.mp4"



speech_meta_file_paths=[]
def walk_directory(directory):
    """遍历指定目录及其子目录中的所有文件和子目录"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 构建文件的完整路径
            full_path = os.path.join(root, file)
            # 打印文件路径
            if len(full_path.split('\\')) == 7 and full_path.endswith("speech_meta.json"):
                speech_meta_file_paths.append(full_path)

walk_directory(consum_dir)

for speech_meta_file_path in speech_meta_file_paths:
    try:
        with open(speech_meta_file_path, 'r') as file:
            speech_meta = json.load(file)
        chapter=speech_meta_file_path.split("\\")[-3].split("_")[1]
        chunk=speech_meta_file_path.split("\\")[-2].split("_")[1]
        curr_work_dir=os.path.dirname(speech_meta_file_path)
        speech_wav_path= curr_work_dir + "\\speech.wav"
        # generate subtile use funclip
        funclip_main(['--stage', '1', '--file', speech_wav_path, "--output_dir", curr_work_dir])
        # merge video audio subtitle
        #merge_video_audio_subtitle(video_path, win_dir_cvt(speech_wav_path), win_dir_cvt(curr_work_dir + "\\total.srt"), win_dir_cvt(curr_work_dir + "\\video.mp4"))
        with open(curr_work_dir + "\\video.txt", 'w', encoding='utf-8') as f:
            # 写入内容到文件
            f.write(f'第 {chapter} 章 {chunk} \n#小说 #兵临城下\n')
        #douyin_cookie_setup()
        subprocess.run(['python', 'D:/PyProj/optimus/social_auto_upload_main/upload_video_to_douyin.py', '--video-dir', curr_work_dir],check=True)

    except Exception as e:
        # send_dingtalk("  Encounter exception, please check.")
        raise e




