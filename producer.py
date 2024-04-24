import os
import json
project_abs_path = os.getcwd()
# print("project_abs_path:", project_abs_path)

import sys
env_path_list = [
    os.path.join(project_abs_path, 'GPT_SoVITS_main'),
    os.path.join(project_abs_path, 'GPT_SoVITS_main/GPT_SoVITS/'),
]
for env_path in env_path_list:
    sys.path.append(env_path)
# print("sys.path:", sys.path)


# cd到子目录GPT_SoVITS_main下才能正确加载GPT_SoVITS模块
os.chdir(os.path.join(project_abs_path, 'GPT_SoVITS_main'))
# print(f"after change dir：{os.getcwd()}")
from GPT_SoVITS_main.book_to_chunk import split_book_into_chunk


# 0. 把小说兵临城下放到文件夹binglinchengxia
# 1. noval 2 chapter chunk
novel_file_path="D:/temp_medias/binglinchengxia/兵临城下.txt"
chunk_output_dir="D:/temp_medias/binglinchengxia/"

chunk_json_path_list=split_book_into_chunk(file_path=novel_file_path, output_dir=chunk_output_dir)





from GPT_SoVITS_main.chunk_to_speech import chunk_to_speech
# 重新cd到项目根目录
os.chdir(project_abs_path)
# 2. chunk 2 speech
for chunk_path in chunk_json_path_list:
    chunk_json = json.load(open(chunk_path, 'r', encoding='utf-8'))
    directory_path = os.path.dirname(chunk_path)
    file_name_with_extension = os.path.basename(chunk_path)
    # 使用os.path.splitext去除文件扩展名，留下 'chunk_1'
    file_name = os.path.splitext(file_name_with_extension)[0]
    output_path = os.path.join(directory_path, file_name)
    ref_wav_path = 'D:/PyProj\optimus/ref_wav/疑问—哇，这个，还有这个…只是和史莱姆打了一场，就有这么多结论吗？.wav'
    chunk_to_speech(chunk_path, ref_wav_path, output_path , max_iter=600)
