from GPT_SoVITS.inference_webui import generate_tts_wav
from scipy.io.wavfile import write
import os
import time
import json
import shutil

def tts(text, output_wav_file_path, ref_wav_path):
    # prompt_text = '今天的天气真不错啊，我想出去玩儿'
    prompt_text = ''
    prompt_language = '中英混合'
    # text = '使用无参考文本模式时建议使用微调的GPT，听不清参考音频说的啥(不晓得写啥)可以开，开启后无视填写的参考文本。'
    text_language = '中英混合'
    sampling_rate, audio_np = generate_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language)
    write(output_wav_file_path, sampling_rate, audio_np)

def text_to_speech(text, ref_wav_path, save_dir, max_time_per_word_limit=1, max_retry=2):
    os.makedirs(save_dir, exist_ok=True)
    time_per_word = max_time_per_word_limit + 1
    retry = 0
    while time_per_word > max_time_per_word_limit: 
        if retry > 0:
            print(f"bad_generate, retry_{retry}...:")
            time.sleep(20)
        start_time = time.time()
        # text to speech
        tts(text, os.path.join(save_dir, f"speech.wav"), ref_wav_path = ref_wav_path)
        end_time = time.time()
        # record the time for each word
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
        # print(speech_meta_json)
        # save the json meta
        with open(os.path.join(save_dir, f"speech_meta.json"), 'w') as f:
            json.dump(speech_meta_json, f, ensure_ascii=False, indent=4)

        if retry >= max_retry:
            break
        retry += 1

def chunk_to_speech(chunk_json_path, ref_wav_path, save_dir, max_time_per_word_limit=1, max_retry=2):
    chunk_json = json.load(open(chunk_json_path, 'r'))
    text = chunk_json["chunk_text"]
    text_to_speech(text, ref_wav_path, save_dir, max_time_per_word_limit, max_retry)
    # copy the json file to the output dir
    shutil.copy(chunk_json_path, save_dir)

if __name__ == '__main__':
    text = """基本上在健身房一泡就是一整天，明显感觉这次续航改善了不少，之前音量高的话耗电会比较快，但现在正常用就能顶一天。
如果说哪里不够满意的话那应该就是充电线了，磁吸式的不好买啊！虽说充电确实方便又快吧，但真是怕丢，就送我这一条，万一丢了买一条还得再花好几十。
也不知道跟客服反映一下能不能解决这个困扰，现在就只能珍惜着用了。
另外这短时间各种场合都试了一下，测了一下漏音，大概就是这样吧"""
    text = text.replace('\n', '\t')
    print(text)

    output_dir = '../tts_outputs/test_text'
    ref_wav_path = '../ref_wav/zzy.wav'
    text_to_speech(text, ref_wav_path, output_dir)
    
    
    chunk_json_path = '../chunks_outputs/天下第一掌柜/chapter_100/chunk_1.json'
    output_dir = '../tts_outputs/test_chunk'
    ref_wav_path = '../ref_wav/zzy.wav'
    chunk_to_speech(chunk_json_path, ref_wav_path, output_dir)

