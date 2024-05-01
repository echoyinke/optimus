import os
import json
project_abs_path = os.getcwd()
# print("project_abs_path:", project_abs_path)

import sys

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
from funclip_main.funclip.videoclipper import main as funclip_main
os.chdir(project_abs_path)
for env_path in env_path_list:
    sys.path.append(env_path)
# print("sys.path:", sys.path)
from pathlib import Path


# cd到子目录GPT_SoVITS_main下才能正确加载GPT_SoVITS模块
os.chdir(os.path.join(project_abs_path, 'GPT_SoVITS_main'))
# print(f"after change dir：{os.getcwd()}")
from GPT_SoVITS_main.book_to_chunk import split_book_into_chunk
from GPT_SoVITS_main.chunk_to_speech import chunk_to_speech
# 重新cd到项目根目录
os.chdir(project_abs_path)


# 0. 把小说兵临城下放到文件夹binglinchengxia
# 1. noval 2 chapter chunk


def split_novel_into_chunks(novel_file_path, output_dir):
    split_book_into_chunk(file_path=novel_file_path, output_dir=output_dir)

chunk_json_path_list=[]


# 2. chunk 2 speech
def produce_chunk_to_speech(chunk_path, ref_wav_path):
    directory_path = os.path.dirname(chunk_path)
    file_name_with_extension = os.path.basename(chunk_path)
    # 使用os.path.splitext去除文件扩展名，留下 'chunk_1'
    file_name = os.path.splitext(file_name_with_extension)[0]
    output_path = os.path.join(directory_path, file_name)
    chunk_to_speech(chunk_path, ref_wav_path, output_path, max_iter=600)
    return output_path

def speech2subtitle(curr_work_dir):
    speech_wav_path = Path(curr_work_dir)/"speech.wav"
    funclip_main(['--stage', '1', '--file', str(speech_wav_path), "--output_dir", curr_work_dir])
    return curr_work_dir

def gen_video_pub_txt(curr_work_dir, novel_name, chapter, chunk):
    with open(Path(curr_work_dir)/"video.txt", 'w', encoding='utf-8') as f:
        f.write(f'第 {chapter} 章 {chunk} \n#小说 #{novel_name}\n')


if __name__ == '__main__':
    novel_file_path = "D:/temp_medias/binglinchengxia/兵临城下.txt"
    output_dir = "D:/temp_medias/binglinchengxia/"
    split_novel_into_chunks(novel_file_path, output_dir)