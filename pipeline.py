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
    os.path.join(project_abs_path, 'GPT_SoVITS_main/'),
    os.path.join(project_abs_path, 'GPT_SoVITS_main/GPT_SoVITS'),
    os.path.join(project_abs_path, 'social_auto_upload_main'),
    os.path.join(project_abs_path, 'social_auto_upload_main/douyin_uploader')
]
for env_path in env_path_list:
    sys.path.append(env_path)
os.chdir(os.path.join(project_abs_path, 'GPT_SoVITS_main'))
from GPT_SoVITS_main.chunk_to_speech import chunk_to_speech
os.chdir(os.path.join(project_abs_path, 'funclip_main'))
from funclip_main.funclip.videoclipper import main as funclip_main
os.chdir(project_abs_path)

from optimus_tools.log_utils import get_logger
from pathlib import Path
from optimus_tools.ffmpeg_utils import merge_video_audio_subtitle, make_cover
import subprocess
import re



produce_offset_file = 'D:\PyProj\optimus\produce_offset.json'
consume_offset_file = 'D:\PyProj\optimus\consume_offset.json'
ref_wav_path = 'D:/PyProj/optimus/GPT_SoVITS_main/ref_wav/我和竹马醉酒后疯狂一夜，我本以为我十年的喜欢终于有了结果，谁知醒后，竹马只是淡淡递给我一粒药。.wav'
jieya_video_path="D:/temp_medias/jieya_video/chongyaji.mp4"
cover_path="D:/temp_medias/binglinchengxia/cover.jpg"

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
def produce_chunk_to_speech(chunk_path, ref_wav_path):
    directory_path = os.path.dirname(chunk_path)
    file_name_with_extension = os.path.basename(chunk_path)
    # 使用os.path.splitext去除文件扩展名，留下 'chunk_1'
    file_name = os.path.splitext(file_name_with_extension)[0]
    output_path = os.path.join(directory_path, file_name)
    if os.path.exists(output_path+"/speech.wav"):
        print("speech.wav already exists.")
        return output_path
    chunk_to_speech(chunk_path, ref_wav_path, output_path, max_iter=600)
    return output_path
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
def save_progress(progress):
    with open(offset_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=4)

def load_progress(offset_file):
    with open(offset_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def producer(queue, progress):
    logger = get_logger("Producer")
    path = Path(progress['novel_split_path'])
    novel_name= path.name
    total_chapters, chunks_per_chapter = count_chapters_and_chunks(path)
    start_chapter = progress['produced']['curr_chapter']
    start_chunk = progress['produced']['curr_chunk']
    for chapter in range(start_chapter, total_chapters):
        total_chunks_this_chapter = chunks_per_chapter["chapter_" + str(chapter)]
        for chunk in range(start_chunk, total_chunks_this_chapter):
            chunk_path = path/f"chapter_{chapter}/chunk_{chunk}.json"
            logger.info(f"producing chunk: {chunk_path}")
            curr_work_dir = produce_chunk_to_speech(chunk_path, ref_wav_path)
            speech2subtitle(curr_work_dir)
            merge_video_audio_subtitle(jieya_video_path, curr_work_dir+"/speech.wav", curr_work_dir +"/total.srt", curr_work_dir+"/video.mp4")
            gen_video_pub_txt(curr_work_dir, novel_name=novel_name, chapter=chapter, chunk=chunk)
            make_cover(cover_path, novel_name, chapter, chunk, curr_work_dir+"/cover.jpg")
            queue.put(curr_work_dir)
            logging.info(f'Produced {curr_work_dir}')
            progress['produced']['curr_chapter'] = chapter
            progress['produced']['curr_chunk'] = chunk
            save_progress(progress)

def consumer(queue, progress):
    logger = get_logger("Consumer:")
    while True:
        try:
            curr_work_dir = queue.get()
            logger.info(f'Consuming got:{curr_work_dir}')
            chapter_match = re.search(r'chapter_(\d+)', curr_work_dir)
            chunk_match = re.search(r'chunk_(\d+)', curr_work_dir)
            chapter = int(chapter_match.group(1))
            chunk = int(chunk_match.group(1))
            subprocess.run( ['python', 'D:/PyProj/optimus/social_auto_upload_main/upload_video_to_douyin.py', '--video-dir', curr_work_dir],check=True)
            logging.info(f'Consumed {curr_work_dir}')
            progress['consumed']['curr_chapter'] = chapter
            progress['consumed']['curr_chunk'] = chunk
            save_progress(progress)
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
if __name__ == '__main__':

    # 加载进度
    produce_progress = load_progress(produce_offset_file)
    consume_progress = load_progress(consume_offset_file)

    q = Queue()

    # debug_work_dir='D:\\temp_medias\\binglinchengxia\\兵临城下\\chapter_0\\chunk_0'

    producer_process = Process(target=producer, args=(q,produce_progress))
    consumer_process = Process(target=consumer, args=(q,consume_progress))

    producer_process.start()
    consumer_process.start()

    producer_process.join()
    q.put(None)  # 使用 None 来通知消费者结束
    consumer_process.join()
