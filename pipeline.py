from multiprocessing import Process, Queue, TimeoutError
import time
import logging
import json
import os
import sys
project_abs_path = os.getcwd()
env_path_list = [
    os.path.join(project_abs_path, 'funclip_main'),
    os.path.join(project_abs_path, 'funclip_main/funclip/'),
    # os.path.join(project_abs_path, 'GPT_SoVITS_main/'),
    # os.path.join(project_abs_path, 'GPT_SoVITS_main/GPT_SoVITS'),
    os.path.join(project_abs_path, 'social_auto_upload_main'),
    os.path.join(project_abs_path, 'social_auto_upload_main/douyin_uploader')
]
for env_path in env_path_list:
    sys.path.append(env_path)
# os.chdir(os.path.join(project_abs_path, 'GPT_SoVITS_main'))
# from GPT_SoVITS_main.chunk_to_speech import chunk_to_speech
os.chdir(os.path.join(project_abs_path, 'funclip_main'))
from funclip_main.funclip.videoclipper import main as funclip_main
os.chdir(project_abs_path)

from optimus_tools.log_utils import get_logger
from pathlib import Path
from optimus_tools.ffmpeg_utils import merge_video_audio_subtitle, make_cover, change_video_speed
from optimus_tools.text2image_utils import subtitle2video
from optimus_tools.chunk_to_speech import chunk_to_speech as asure_chunk_to_speech, text_to_speech as asure_text2speech
import subprocess
from optimus_tools.text_utils import split_text
import re
import random
logger = get_logger(__name__)



produce_offset_file = 'D:\PyProj\optimus\produce_offset.json'
consume_offset_file = 'D:\PyProj\optimus\consume_offset.json'
ref_wav_path = 'D:/PyProj/optimus/GPT_SoVITS_main/ref_wav/我和竹马醉酒后疯狂一夜，我本以为我十年的喜欢终于有了结果，谁知醒后，竹马只是淡淡递给我一粒药。.wav'
jieya_video_folder="D:/temp_medias/jieya_video/"
cover_path="D:/temp_medias/binglinchengxia/cover.jpg"

def get_jieya_video(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid directory")
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        raise ValueError(f"No files found in {folder_path}")
    random_file = random.choice(files)
    return os.path.join(folder_path, random_file)
def speech2subtitle(curr_work_dir):
    speech_wav_path = Path(curr_work_dir)/"speech.wav"
    if os.path.exists(curr_work_dir + "/total.srt"):
        print("total.srt already exists.")
        return curr_work_dir
    funclip_main(['--stage', '1', '--file', str(speech_wav_path), "--output_dir", curr_work_dir])
    return curr_work_dir
def gen_video_pub_txt(curr_work_dir, novel_name, chapter, chunk):
    with open(Path(curr_work_dir)/"video.txt", 'w', encoding='utf-8') as f:
        f.write(f'第 {chapter} 章 {chunk} \n#小说 #{novel_name}\n')
def count_chapters_and_chunks(directory):
    chapters = os.listdir(directory)
    total_chapter = len(chapters)
    chunks_per_chapter = {}

    for chapter in chapters:
        chapter_path = os.path.join(directory, chapter)
        if os.path.isdir(chapter_path):  # 确保是目录
            chunks = os.listdir(chapter_path)
            chunks_per_chapter[chapter] = len(chunks)

    return total_chapter, chunks_per_chapter
def save_progress(progress, offset_file):
    with open(offset_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=4)

def load_progress(offset_file):
    with open(offset_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def text2video(text, curr_work_dir):
    if os.path.exists(f"{curr_work_dir}/video.mp4"):
        logger.info("video.mp4 already exists.")
        return
    asure_text2speech(text, curr_work_dir)
    speech2subtitle(curr_work_dir)
    subtitle2video(work_dir=curr_work_dir, video_shots_num=10)
    merge_video_audio_subtitle(f"{curr_work_dir}/concat.mp4", curr_work_dir + "/speech.wav",
                               curr_work_dir + "/total.srt", curr_work_dir + "/video.mp4")
    change_video_speed(f"{curr_work_dir}/video.mp4", f"{curr_work_dir}/video_1.25x.mp4", 1.25)

def producer(queue, offset_path):
    logger = get_logger("Producer")
    progress = load_progress(offset_path)
    path = Path(progress['novel_split_path'])
    novel_name= path.name
    total_chapters, chunks_per_chapter = count_chapters_and_chunks(path)
    start_chapter = progress['produced']['curr_chapter']
    start_chunk = progress['produced']['curr_chunk']
    for chapter in range(start_chapter, total_chapters):
        total_chunks_this_chapter = chunks_per_chapter["chapter_" + str(chapter)]
        for chunk in range(start_chunk, total_chunks_this_chapter):
            chunk_path = path/f"chapter_{chapter}/chunk_{chunk}.json"
            curr_work_dir = str(path / f"chapter_{chapter}/chunk_{chunk}")
            logger.info(f"producing chunk: {chunk_path}")
            asure_chunk_to_speech(chunk_path, curr_work_dir)
            speech2subtitle(curr_work_dir)
            subtitle2video(work_dir=curr_work_dir, video_shots_num=5)
            merge_video_audio_subtitle(f"{curr_work_dir}/concat.mp4", curr_work_dir+"/speech.wav", curr_work_dir +"/total.srt", curr_work_dir+"/video.mp4")
            gen_video_pub_txt(curr_work_dir, novel_name=novel_name, chapter=chapter, chunk=chunk)
            make_cover(f"{curr_work_dir}/0.jpg", novel_name, chapter, chunk, curr_work_dir+"/cover.jpg")
            queue.put(curr_work_dir)
            logging.info(f'Produced {curr_work_dir}')
            progress['produced']['curr_chapter'] = chapter
            progress['produced']['curr_chunk'] = chunk
            save_progress(progress, offset_path)

def consumer(queue, offset_path):
    logger = get_logger("Consumer:")
    while True:
        try:
            curr_work_dir = queue.get()
            progress = load_progress(offset_path)
            logger.info(f'Consuming got:{curr_work_dir}')
            chapter_match = re.search(r'chapter_(\d+)', curr_work_dir)
            chunk_match = re.search(r'chunk_(\d+)', curr_work_dir)
            chapter = int(chapter_match.group(1))
            chunk = int(chunk_match.group(1))
            subprocess.run( ['python', 'D:/PyProj/optimus/social_auto_upload_main/upload_video_to_douyin.py', '--video-dir', curr_work_dir],check=True)
            logging.info(f'Consumed {curr_work_dir}')
            progress['consumed']['curr_chapter'] = chapter
            progress['consumed']['curr_chunk'] = chunk
            save_progress(progress, offset_path)
        except Exception as e:
            logger.error(f'Consume exception...\n{e}')
def debug_consume(curr_work_dir):
    chapter_match = re.search(r'chapter_(\d+)', curr_work_dir)
    chunk_match = re.search(r'chunk_(\d+)', curr_work_dir)
    chapter = int(chapter_match.group(1))
    chunk = int(chunk_match.group(1))
    subprocess.run( ['python', 'D:/PyProj/optimus/social_auto_upload_main/upload_video_to_douyin.py', '--video-dir', curr_work_dir],check=True)
    logging.info(f'Consumed {curr_work_dir}')
    # data_queue.task_done()
def run_pipeline():
    q = Queue()

    # debug_work_dir='D:\\temp_medias\\binglinchengxia\\兵临城下\\chapter_0\\chunk_0'

    producer_process = Process(target=producer, args=(q, produce_offset_file))
    consumer_process = Process(target=consumer, args=(q, consume_offset_file))

    producer_process.start()
    consumer_process.start()

    producer_process.join()
    q.put(None)  # 使用 None 来通知消费者结束
    consumer_process.join()



if __name__ == '__main__':
    file_path="D:/temp_medias/shirizhongyan/srzy2.txt"
    work_dir = file_path.split(".")[0]
    with open(file_path, "r" , encoding="utf-8") as f:
        text = f.read()
    split_texts = split_text(text, 800)

    for idx, text in enumerate(split_texts):
        work_dir = f"{file_path.split('.')[0]}/{idx}"
        os.makedirs(work_dir, exist_ok=True)
        text2video(text, curr_work_dir=work_dir)

