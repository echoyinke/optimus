import os
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
from GPT_SoVITS_main.chunk_to_speech import text_to_speech, chunk_to_speech

# 重新cd到项目根目录
os.chdir(project_abs_path)


# book_into_chunk接口示例
file_path = 'novel_material/天下第一掌柜.txt'
output_dir = 'chunks_outputs/'
# 如果想按照line切分，chunk_size设为-1即可
# 想按line推理，请设sep='\n'；如果为其他，则整句话一次推理
split_book_into_chunk(file_path, chunk_size=300, output_dir=output_dir, sep='')


# text_to_speech接口示例
text = """基本上在健身房一泡就是一整天，明显感觉这次续航改善了不少，之前音量高的话耗电会比较快，但现在正常用就能顶一天。
如果说哪里不够满意的话那应该就是充电线了，磁吸式的不好买啊！虽说充电确实方便又快吧，但真是怕丢，就送我这一条，万一丢了买一条还得再花好几十。
也不知道跟客服反映一下能不能解决这个困扰，现在就只能珍惜着用了。
另外这短时间各种场合都试了一下，测了一下漏音，大概就是这样吧"""
text = text.replace('\n', '')
output_dir = 'tts_outputs/test_text'
ref_wav_path = 'ref_wav/test.wav'
text_to_speech(text, ref_wav_path, output_dir, max_iter=600)

# chunk_to_speech接口示例
chunk_json_path = 'chunks_outputs/天下第一掌柜/chapter_100/chunk_0.json'
output_dir = 'tts_outputs/test_chunk'
ref_wav_path = 'ref_wav/test.wav'
chunk_to_speech(chunk_json_path, ref_wav_path, output_dir, max_iter=600)
