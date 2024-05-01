import threading
import queue
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
from optimus_tools.log_utils import get_logger
from pathlib import Path
from producer import *
from optimus_tools.ffmpeg_utils import merge_video_audio_subtitle, make_cover

logger = get_logger(__name__)

data_queue = queue.Queue()
offset_file = 'D:\PyProj\optimus\offset.json'
ref_wav_path = 'D:/PyProj/optimus/GPT_SoVITS_main/ref_wav/我和竹马醉酒后疯狂一夜，我本以为我十年的喜欢终于有了结果，谁知醒后，竹马只是淡淡递给我一粒药。.wav'
jieya_video_path="D:/temp_medias/jieya_video/chongyaji.mp4"
cover_path="D:/temp_medias/binglinchengxia/cover.jpg"


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
    with open(offset_file, 'w') as f:
        json.dump(progress, f)

def load_progress(offset_file):
    with open(offset_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def producer(progress):
    path = Path(progress['split_path'])
    novel_name= path.name
    total_chapters, chunks_per_chapter = count_chapters_and_chunks(path)
    start_chapter = progress['produced']['curr_chapter']
    start_chunk = progress['produced']['curr_chunk']
    for chapter in range(start_chapter, total_chapters):
        total_chunks_this_chapter = chunks_per_chapter["chapter_" + str(chapter)]
        for chunk in range(start_chunk, total_chunks_this_chapter):
            chunk_path = path/f"chapter_{chapter}/chunk_{chunk}.json"
            curr_work_dir = produce_chunk_to_speech(chunk_path, ref_wav_path)
            speech2subtitle(curr_work_dir)
            merge_video_audio_subtitle(jieya_video_path, curr_work_dir+"/speech.wav", curr_work_dir +"/total.srt", curr_work_dir+"/video.mp4")
            gen_video_pub_txt(curr_work_dir, novel_name=novel_name, chapter=chapter, chunk=chunk)
            make_cover(cover_path, novel_name, chapter, chunk, curr_work_dir+"/cover.jpg")
            data_queue.put(curr_work_dir)
            logging.info(f'Produced {curr_work_dir}')
            progress['produced']['curr_chapter'] = chapter
            progress['produced']['curr_chunk'] = chunk
            save_progress(progress)

def consumer(progress):
    while True:
        item = data_queue.get()
        logging.info(f'Consumed {item}')
        data_queue.task_done()
        progress['consumed'] += 1
        save_progress(progress)
        time.sleep(1.5)

if __name__ == '__main__':


    # 加载进度
    progress = load_progress(offset_file)

    producer(progress)

    # 创建生产者和消费者线程
    # producer_thread = threading.Thread(target=producer, args=(progress,))
    # consumer_thread = threading.Thread(target=consumer, args=(progress,))
    #
    # # 启动线程
    # producer_thread.start()
    # consumer_thread.start()
    #
    # # 等待所有项目被处理完毕
    # producer_thread.join()
    # data_queue.join()  # 确保队列中的所有项都被处理

    logging.info('All data has been produced and consumed.')
