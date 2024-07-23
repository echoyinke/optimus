import random
import subprocess
import platform
import os
from optimus_tools.log_utils import get_logger
import json
logger = get_logger(__name__)
import ffmpeg
import random


def win_dir_cvt(dir):
    return dir.replace("\\", '/')


def get_media_duration(file_path):
    """使用 ffmpeg-python 获取多媒体文件的时长，返回秒为单位的浮点数。"""
        # 使用 ffprobe 获取文件信息
    probe = ffmpeg.probe(file_path)
    # 从视频文件的第一个流中提取时长
    duration = next((stream['duration'] for stream in probe['streams'] if 'duration' in stream), None)
    return float(duration)


def change_video_speed(input_file, output_file, speed_factor):
    """
    调整视频播放速度并同步音频。

    :param input_file: 输入视频文件路径
    :param output_file: 输出视频文件路径
    :param speed_factor: 速度因子，大于1表示加速，小于1表示减速
    """
    video_filter = f"setpts={1 / speed_factor}*PTS"
    audio_filter = f"atempo={speed_factor}"

    if speed_factor < 0.5 or speed_factor > 2.0:
        raise ValueError("音频过滤器atempo的值必须在0.5到2.0之间。")

    command = [
        'ffmpeg',
        '-i', input_file,
        '-filter_complex', f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
        '-map', "[v]",
        '-map', "[a]",
        output_file
    ]

    subprocess.run(command, check=True)
    print(f"输出文件已保存到: {output_file}")

def change_video_speed(input_file, output_file, speed_factor):
    """
    Adjust the playback speed of a video using ffmpeg.

    Args:
        input_file (str): Path to the input video file.
        output_file (str): Path to save the output video file.
        speed_factor (float): Speed factor. >1 for fast, <1 for slow.
    """
    if speed_factor > 2.0 or speed_factor < 0.5:
        raise ValueError("Speed factor should be between 0.5 and 2.0 for audio processing.")

    video_speed = 1 / speed_factor
    audio_speed = speed_factor

    command = [
        'ffmpeg',
        '-i', input_file,
        '-filter:v', f'setpts={video_speed}*PTS',
        '-filter:a', f'atempo={audio_speed}',
        output_file
    ]
    subprocess.run(command, check=True)
    print(f"Video speed change {speed_factor} and saved as {output_file}")

def merge_video_audio_subtitle(video_path, audio_path, subtitle_path, output_path):
    if os.path.exists(output_path):
        logger.info("video.mp4 already exists.")
        return
    duration = get_media_duration(audio_path)
    if platform.system() == 'Windows':
        subtitle_path = subtitle_path.replace("\\", "/")
        subtitle_path = subtitle_path.replace(":", "\\:")
        print(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    command = [
        'ffmpeg',
        '-y',  # 覆盖
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

    print(f"Running FFmpeg command: {command}")
    subprocess.run(command, check=True)
    print("Video processing completed successfully!")
    os.remove(video_path)


def make_cover(cover_path, novel_name, chapter, chunk, output_path):
    # if platform.system() == 'Windows':
    #     picture_path=picture_path.replace(":", "\\:")
    #     print(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    command = [
        'ffmpeg',
        '-y',  # 覆盖
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


def concat_images_to_video(images_with_duration_list, work_dir):
    """
    将images_with_duration_list中的每一个image和duration生成视频，并将所有视频合并成一个视频
    :param images_with_duration_list:
      [{"image_path" : "./images/1.jpg", "duration" : 5400},
       {"image_path" : "/Users/AI图片素材/images/2.jpg", "duration" : 210},
       {"image_path" : "./images/3.jpg", "duration" : 4200}]
    - image_path是图片路径（可以是相对路径，也可以是绝对路径）
    - duration是图片显示时间
    
    :param output_path: 合并后的视频路径
    :param special_effect: 特效，目前支持"zoompan left_up"和"zoompan center"
    """
    if os.path.exists(f'{work_dir}/concat.mp4'):
        logger.info(f"{work_dir}/concat.mp4 already exists.")
        return
    # 根据每一个image和duration生成视频
    tmp_output_video_path_list = []
    for image_with_duration in images_with_duration_list:
        image_path = image_with_duration["image_path"]
        duration = image_with_duration["duration"]
        duration = float(duration)/1000
        tmp_output_video_path = image_path.replace(".png", ".mp4")

        fps = 100
        # zoom_factor代表每秒放大的比例
        zoom_factor = 0.015
        special_effect = {
            # 缩放, z代表每一帧的缩放比例, s代表输出视频的宽高, fps代表每秒帧数, d代表总共的帧数
            "zoompan_left_up": f"zoompan=z='zoom+{zoom_factor / fps}':s=1000x600:fps={fps}:d={fps}*{duration}",
            "zoompan_left_down": f"zoompan=x='0':y='ih*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s=1000x600",
            "zoompan_right_up": f"zoompan=x='iw*(1-1/zoom)':y='0':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s=1000x600",
            "zoompan_right_down": f"zoompan=x='iw*(1-1/zoom)':y='ih*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s=1000x600",
            "zoompan_center": f"zoompan=x='iw/2*(1-1/zoom)':y='ih/2*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s=1000x600",
        }
        # 原始不缩放
        # random select a value from special_effect

        special_effect = random.choice(list(special_effect.values()))
        command = [
                'ffmpeg',
                '-y',
                '-i', image_path,  # 输入图片路径
                '-filter_complex',  # 滤镜复合
                special_effect,
                tmp_output_video_path  # 输出视频路径
            ]
        if not os.path.exists(tmp_output_video_path):
            print(f"Running FFmpeg command: {command}")
            subprocess.run(command, check=True)
            print("Video processing completed successfully!")
        else:
            logger.info(f"{tmp_output_video_path} already exists.")

        tmp_output_video_path_list.append(tmp_output_video_path)

    # 合并视频， 必须要先将所有需要合并的视频路径写入到一个txt文件中，再合并
    with open(f"{work_dir}/contact_videos.txt", "w", encoding='utf-8') as f:
        for tmp_output_video_path in tmp_output_video_path_list:
            f.write(f"file '{tmp_output_video_path}'\n")

    concat_command = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0', # 允许文件名中有特殊字符
        '-i', f'{work_dir}/contact_videos.txt', # 输入的合并文件
        '-c', 'copy',
        f'{work_dir}/concat.mp4'
    ]

    print(f"Running FFmpeg command: {concat_command}")
    subprocess.run(concat_command, check=True)
    print("Video concatenation completed successfully!")
    for tmp_output_video_path in tmp_output_video_path_list:
        os.remove(tmp_output_video_path)

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
    shots_path = "/Users/yinke/PycharmProjects/optimus/optimus_tools/outputs/video_shots_info.json"
    with open(shots_path, 'r', encoding='utf-8') as f:
        # 使用 json.load() 从文件中加载数据
        data = json.load(f)
