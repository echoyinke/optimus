# 添加系统系统路径
import sys
sys.path.append("E:/小说推文项目/GPT-SoVITS/GPT_SoVITS")

from GPT_SoVITS.inference_webui import generate_tts_wavz
from scipy.io.wavfile import write
import os
import time
import json

def tts(text, output_wav_file_path, ref_wav_path):
    # print("ref_wav_path: ", ref_wav_path)
    # prompt_text = '今天的天气真不错啊，我想出去玩儿'
    prompt_text = ''
    prompt_language = '中英混合'
    # text = '使用无参考文本模式时建议使用微调的GPT，听不清参考音频说的啥(不晓得写啥)可以开，开启后无视填写的参考文本。'
    text_language = '中英混合'
    sampling_rate, audio_np = generate_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language)
    write(output_wav_file_path, sampling_rate, audio_np)

# file_name = './小说/盗墓笔记 (1).txt'
def split_book_into_chapter(file_name):
    with open(file_name, 'r') as f:
        file_lines = f.readlines()
    # 清除每一行前后的"\n"以及空格
    cleaned_lines = []
    filter_list = ['分界线', 
                '声明：',
                '本章完',
                '用户上传',
                '写在前面：']
    for line in file_lines:
        line = line.strip("- \n\t")
        for filter_str in filter_list:
            if filter_str in line:
                line = ''
        if len(line) >= 2 and line[0] == '（' and line[-1] == '）':
            line = ''
        if line:
            cleaned_lines.append(line)

    # 小说内容
    content = []
    for line in cleaned_lines:
        if '第' in line and '章' in line and '。'not in line:
            content.append([])
        if content:
            content[-1].append(line)
    return content
    
        
# content = [content[-1]]
def book_to_speech(content, book_dir, ref_wav_path, max_time_per_word_limit=1, max_retry=2):
    for i, chapter in enumerate(content):
        chapter_meta = chapter[0]
        chapter_content = chapter[1:]
        chapter_dir = os.path.join(book_dir, f"chapter_{i}")
        os.makedirs(chapter_dir, exist_ok=True)
        with open(os.path.join(chapter_dir, f"chapter_meta.txt"), 'w') as f:
            f.write(chapter_meta)    
        for j, text in enumerate(chapter_content):
            time_per_word = max_time_per_word_limit + 1
            retry = 0
            while time_per_word > max_time_per_word_limit: 
                if retry > 0:
                    print(f"bad_generate, retry_{retry}...:")
                    time.sleep(20)
                line_dir = os.path.join(chapter_dir, f'line_{j}')
                os.makedirs(line_dir, exist_ok=True)
                start_time = time.time()
                # 生成语音并保存
                tts(text, os.path.join(line_dir, f"speech.wav"), ref_wav_path = ref_wav_path)
                # 保存文本
                end_time = time.time()
                # 记录每个字生产的速度
                time_per_word = (end_time - start_time) / len(text)
                speech_meta_json = {}
                speech_meta_json["text"] = text
                speech_meta_json["text_length"] = len(text)
                speech_meta_json["time_per_text"] = end_time - start_time
                speech_meta_json["time_per_word"] = time_per_word
                if time_per_word <= 1: 
                    speech_meta_json["final_generate_status"] = "good"   
                else:
                    speech_meta_json["final_generate_status"] = "bad"
                speech_meta_json["retry"] = retry   
                print(speech_meta_json)
                # 保存json文件
                with open(os.path.join(line_dir, f"speech_meta.json"), 'w') as f:
                    json.dump(speech_meta_json, f, ensure_ascii=False, indent=4)

                if retry >= max_retry:
                    break
                retry += 1

# 读取txt中的每一行文件
if __name__ == '__main__':
    
    file_dir = '../novel_material/'
    output_dir = '../tts_outputs'
    ref_wav_path = './ref_wav/zzy.wav'
    print("ref_wav_path: ", ref_wav_path)
    
    # 用于限制每字生成的时间，如果超过这个时间，则认为生成时间过长，很可能出现badcase，需要重试
    max_time_per_word_limit = 1
    max_retry = 2
    # 读取file_dir下的所有文件
    file_name_list = os.listdir(file_dir)
    for file_name in file_name_list:
        file_path = os.path.join(file_dir, file_name)
        try:
            with open(file_path, 'r') as f:
                file_lines = f.readlines()
            book_dir = os.path.join(output_dir, file_name.replace('.txt', ''))
            os.makedirs(book_dir, exist_ok=True)
            content = split_book_into_chapter(file_path)
            # print(content)
            book_to_speech(content, book_dir, ref_wav_path, max_time_per_word_limit, max_retry)
        except:
            pass
    
