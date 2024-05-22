import random
import subprocess
import platform
import os
from log_utils import get_logger
logger = get_logger(__name__)
import ffmpeg
import random


def win_dir_cvt(dir):
    return dir.replace("\\", '/')
def get_media_duration(file_path):
    """使用 ffmpeg-python 获取多媒体文件的时长，返回秒为单位的浮点数。"""
    try:
        # 使用 ffprobe 获取文件信息
        probe = ffmpeg.probe(file_path)
        # 从视频文件的第一个流中提取时长
        duration = next((stream['duration'] for stream in probe['streams'] if 'duration' in stream), None)
        return float(duration) if duration is not None else None
    except ffmpeg.Error as e:
        print("Failed to retrieve media duration:", e)
        return None
def merge_video_audio_subtitle(video_path, audio_path, subtitle_path, output_path):
    if os.path.exists(output_path):
        logger.info("video.mp4 already exists.")
        return
    duration=get_media_duration(audio_path)
    if platform.system() == 'Windows':
        subtitle_path=subtitle_path.replace("\\", "/")
        subtitle_path=subtitle_path.replace(":", "\\:")
        print(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    command = [
        'ffmpeg',
        '-y', # 覆盖
        '-i', video_path,
        '-i', audio_path,  # 添加音频输入
        '-filter_complex',
        f"[0:v]split=2[v0][v1];[v0][v1]concat=n=2:v=1:a=0,trim=duration={duration}[trimed];[trimed]subtitles=\'{subtitle_path}\':force_style='FontName=Microsoft YaHei,FontSize=24'[video]",
        '-map', '[video]',  # 映射处理后的视频流
        '-map', '1:a',  # 映射处理后的视频流
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-crf', '23',
        '-preset', 'fast',
        output_path
    ]

    try:
        print(f"Running FFmpeg command: {command}")
        subprocess.run(command, check=True)
        print("Video processing completed successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to process video:", e)

def make_cover(cover_path, novel_name, chapter, chunk, output_path):
    # if platform.system() == 'Windows':
    #     picture_path=picture_path.replace(":", "\\:")
    #     print(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    command = [
        'ffmpeg',
        '-y', # 覆盖
        '-i', cover_path,
        '-vf',
        f"drawtext=text='{novel_name}\n 第{chapter}章\n  ({chunk})':fontfile='C\\:/Windows/Fonts/msyh.ttc':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=128:fontcolor=white",
        output_path
    ]

    try:
        print("Running FFmpeg command...")
        subprocess.run(command, check=True)
        print("Video processing completed successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to process video:", e)
def add_cover(cover_path, video_path, output_path):
    command = [
        'ffmpeg',
        '-y',
        '-i', video_path,  # 视频文件路径
        '-i', cover_path,  # 封面图片路径
        '-map', '0:v', '-map', '1:v',  # 映射视频流和音频流，以及封面图像
        '-c:a', 'copy',  # 音频流复制
        '-disposition:1', 'attached_pic',  # 设置封面图片流的表现形式为附加图片
        output_path  # 输出文件路径

    ]
    print(command)
    # ffmpeg - i
    # D: / temp_medias / jieya_video / chongyaji.mp4 - i
    # D: / temp_medias / binglinchengxia / cover2.jpg - filter_complex
    # "[1:v]scale=iw:ih[in];[0:v][in]overlay=0:0:enable='between(t,0,0.1)'" - shortest - y
    # output.mp4

    try:
        print("Running FFmpeg command...")
        subprocess.run(command, check=True)
        print("Video processing completed successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to process video:", e)
def concat_images_to_video(images_with_duration_list, output_path, special_effect=None):
    """
    将images_with_duration_list中的每一个image和duration生成视频，并将所有视频合并成一个视频
    :param images_with_duration_list:
      [{"image_path" : "./images/1.jpg", "duration" : 5.4}, 
       {"image_path" : "/Users/AI图片素材/images/2.jpg", "duration" : 2.1},
       {"image_path" : "./images/3.jpg", "duration" : 4.2}]
    - image_path是图片路径（可以是相对路径，也可以是绝对路径）
    - duration是图片显示时间
    
    :param output_path: 合并后的视频路径
    :param special_effect: 特效，目前支持"zoompan left_up"和"zoompan center"
    """
    # 根据每一个image和duration生成视频
    tmp_output_video_path_list = []
    for image_with_duration in images_with_duration_list:
        image_path = image_with_duration["image_path"]
        duration = image_with_duration["duration"]
        tmp_output_video_path = image_path.replace(".jpg", ".mp4")

        fps = 25
        # 原始不缩放
        items = ["zoompan left_up", "zoompan center", None]

        special_effect = random.choice(items)
        if special_effect is None:
            command = [
                'ffmpeg',
                '-r', f'{1/duration}', # 每秒帧数, 1/duration, 这样可以控制每张图片的显示时间
                '-f', 'image2', # 输入格式
                '-i', image_path, # 输入图片路径
                '-vf', 'scale=w=800:h=600', # 图片的宽高
                tmp_output_video_path # 输出视频路径
            ]
        # 动态缩放
        # 聚焦放大到左上角
        elif special_effect == "zoompan left_up":
            command = [
                'ffmpeg',
                '-i', image_path, # 输入图片路径
                '-filter_complex', # 滤镜复合
                f"zoompan=z='zoom+{0.2/(fps*duration)}':s=1000x600:fps={fps}:d={fps}*{duration}", # 缩放, z代表每一帧的缩放比例（这里代表总共放缩到原来的1.2倍）, s代表输出视频的宽高, fps代表每秒帧数, d代表总共的帧数
                tmp_output_video_path # 输出视频路径
            ]
        # 聚焦放大到中心
        elif special_effect == "zoompan center":
            command = [
                'ffmpeg',
                '-i', image_path, # 输入图片路径
                '-filter_complex', # 滤镜复合
                f"zoompan=x='iw/2*(1-1/zoom)':y='ih/2*(1-1/zoom)':z='zoom+{0.2/(fps*duration)}':fps={fps}:d={fps}*{duration}:s=1000x600", # x和y代表缩放的中心点，x='iw/2'和y='ih/2'代表画面的中心
                tmp_output_video_path # 输出视频路径
            ]
        else:
            raise ValueError("special_effect参数不支持")

        try:
            print(f"Running FFmpeg command: {command}")
            subprocess.run(command, check=True)
            print("Video processing completed successfully!")
        except subprocess.CalledProcessError as e:
            print("Failed to process video:", e)
        tmp_output_video_path_list.append(tmp_output_video_path)

    # 合并视频， 必须要先将所有需要合并的视频路径写入到一个txt文件中，再合并
    with open("contact_videos.txt", "w") as f:
        for tmp_output_video_path in tmp_output_video_path_list:
            f.write(f"file '{tmp_output_video_path}'\n")

    concat_command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0', # 允许文件名中有特殊字符
        '-i', 'contact_videos.txt', # 输入的合并文件
        '-c', 'copy',
        '-y', output_path
    ]

    try:
        print(f"Running FFmpeg command: {concat_command}")
        subprocess.run(concat_command, check=True)
        print("Video concatenation completed successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to concat videos:", e)
    
    # 删除临时视频
    for tmp_output_video_path in tmp_output_video_path_list:
        os.remove(tmp_output_video_path)
    os.remove("contact_videos.txt")

if __name__ == '__main__':
    # video_path =  'D:/temp_medias/jieya_video/chongyaji.mp4'
    # audio_path = 'D:/temp_medias/dev/speech.wav'
    # subtitle_path = 'D:/temp_medias/dev/total.srt'
    # output_path = 'D:/temp_medias/output.mp4'
    # input_cover = 'D:/temp_medias/binglinchengxia/cover.jpg'
    # cover_path= 'D:/temp_medias/binglinchengxia/cover2.jpg'
    # #merge_video_audio_subtitle(video_path,audio_path ,output_cover, subtitle_path,output_path)
    # # make_cover(input_cover,1, 0, output_cover)
    # add_cover(video_path, cover_path, output_path)
    shots_path = "/Users/yinke/PycharmProjects/optimus/optimus_tools/outputs/aug_split_shots.json"
    with open(shots_path, 'r', encoding='utf-8') as f:
        # 使用 json.load() 从文件中加载数据
        data = json.load(f)