import os
import time
import json
import shutil
import uuid
import math
import wave
import contextlib


def text_to_speech(tts_fun, text, save_dir, **kwargs):
    os.makedirs(save_dir, exist_ok=True)
    start_time = time.time()
    # text to speech
    output_wav_file_path = os.path.join(save_dir, f"speech.wav")
    tts_fun(text=text, output_wav_file_path=output_wav_file_path, **kwargs)
    with contextlib.closing(wave.open(output_wav_file_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        speech_duration = frames / float(rate)    
    end_time = time.time()
    # 获取wav的总时长
    # record the time for each word
    speech_meta_json = {
        "speech_id" : str(uuid.uuid4()),
        "speech_duration" : math.ceil(speech_duration),
        "text" : text,
        "text_length" : len(text),
        "inference_time" : end_time - start_time,
        "create_time" : time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    # save the json meta
    with open(os.path.join(save_dir, f"speech_meta.json"), 'w') as f:
        json.dump(speech_meta_json, f, ensure_ascii=False, indent=4)

def chunk_to_speech(chunk_json_path, tts_fun, text, save_dir, **kwargs):
    chunk_json = json.load(open(chunk_json_path, 'r', encoding='utf-8'))
    text = chunk_json["chunk_text"]
    text_to_speech(tts_fun, text, save_dir, **kwargs)
    # copy the json file to the output dir
    shutil.copy(chunk_json_path, save_dir)

if __name__ == '__main__':
    # 选择一个TTS引擎或API
    from microsoft_azure_api import AzureTextToSpeech
    subscription_key = "dc00d3aa5b204db4a4ffbba9b96560d3"
    azure_tts = AzureTextToSpeech(subscription_key)

    text = """基本上在健身房一泡就是一整天，明显感觉这次续航改善了不少，之前音量高的话耗电会比较快，但现在正常用就能顶一天。
    如果说哪里不够满意的话那应该就是充电线了，磁吸式的不好买啊！虽说充电确实方便又快吧，但真是怕丢，就送我这一条，万一丢了买一条还得再花好几十。
    也不知道跟客服反映一下能不能解决这个困扰，现在就只能珍惜着用了。
    另外这短时间各种场合都试了一下，测了一下漏音，大概就是这样吧"""
    text = text.replace('\n', '\t')
    print(text)

    output_dir = '../tts_outputs/test_text'
    text_to_speech(azure_tts.tts, text, output_dir)
    # 通过ShortName指定生成的音频的音色
    # text_to_speech(azure_tts.tts, text, output_dir, ShortName='zh-CN-YunyeNeural')
    
    chunk_json_path = '../chunks_outputs/天下第一掌柜/chapter_100/chunk_1.json'
    output_dir = '../tts_outputs/test_chunk'
    chunk_to_speech(chunk_json_path, azure_tts.tts, text, output_dir)

