import random
import subprocess
import platform
import os
import time

from optimus_tools.log_utils import get_logger
import json

logger = get_logger(__name__)
import ffmpeg
import random
import requests
from .coze_utils import load_shot_info, download_images


def win_dir_cvt(dir):
    return dir.replace("\\", '/')


def get_media_duration(file_path):
    """使用 ffmpeg-python 获取多媒体文件的时长，返回秒为单位的浮点数。"""
    # 使用 ffprobe 获取文件信息
    probe = ffmpeg.probe(file_path)
    # 从视频文件的第一个流中提取时长
    duration = next((stream['duration'] for stream in probe['streams'] if 'duration' in stream), None)
    return float(duration)


def change_video_speed(workdir, speed_factor=1.25):
    """
    Adjust the playback speed of a video using ffmpeg.

    Args:
        input_file (str): Path to the input video file.
        output_file (str): Path to save the output video file.
        speed_factor (float): Speed factor. >1 for fast, <1 for slow.
    """
    input_file = workdir + "/video.mp4"
    output_file = workdir + "/video_1.25x.mp4"
    if speed_factor > 2.0 or speed_factor < 0.5:
        raise ValueError("Speed factor should be between 0.5 and 2.0 for audio processing.")

    video_speed = 1 / speed_factor
    audio_speed = speed_factor

    change_speed_command = [
        'ffmpeg',
        '-loglevel', 'error',  # 只输出错误信息
        '-y',
        '-i', input_file,
        '-filter:v', f'setpts={video_speed}*PTS',
        '-filter:a', f'atempo={audio_speed}',
        output_file
    ]
    logger.info(f"Running command:change_speed_command")
    subprocess.run(change_speed_command, check=True)
    logger.info(f"Video speed change {speed_factor}")
    os.remove(input_file)
    os.rename(output_file, input_file)


def merge_video_audio_subtitle(concat_video, audio_path, subtitle_path, output_path):
    if os.path.exists(output_path):
        logger.info("video.mp4 already exists.")
        return
    duration = get_media_duration(audio_path)
    if platform.system() == 'Windows':
        subtitle_path = subtitle_path.replace("\\", "/")
        subtitle_path = subtitle_path.replace(":", "\\:")
        logger.info(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    # 直接合并视频/音频/字幕太费内存，容易崩
    command_merge_video_audio_subtile = [
        'ffmpeg',
        '-loglevel', 'error',  # 只输出错误信息
        '-y',  # 覆盖
        '-i', concat_video,
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

    logger.info(f"Running FFmpeg command: command_merge_video_audio_subtile ...")
    subprocess.run(command_merge_video_audio_subtile, check=True)
    # logger.info(f"Running FFmpeg command: step2_add_subtitle")
    # subprocess.run(step2_add_subtitles, check=True)
    # logger.info("Video processing completed successfully!")


def merge_video_audio(workdir):
    concat_video = f"{workdir}/concat.mp4"
    audio_path = f"{workdir}/output.wav"
    output_path = f"{workdir}/video.mp4"
    if os.path.exists(output_path):
        raise ValueError("video.mp4 already exists.")
    command_merge_video_audio = [
        'ffmpeg',
        '-loglevel', 'info',  # 只输出错误信息
        '-y',  # 覆盖
        '-i', concat_video,  # 视频输入
        '-i', audio_path,  # 音频输入
        '-c:v', 'libx264',  # 编码视频
        '-c:a', 'aac',  # 编码音频
        '-crf', '23',  # 压缩质量
        '-preset', 'fast',  # 编码速度
        output_path  # 中间输出文件路径
    ]

    logger.info(f"Running FFmpeg command: command_merge_video_audio ...")
    subprocess.run(command_merge_video_audio, check=True)
    logger.info(f"Finish FFmpeg command: command_merge_video_audio")


def add_subtile(workdir):
    input_path = workdir + "/video.mp4"
    subtitle_path = workdir + "/output.srt"
    output_path = workdir + "/video_srt.mp4"
    if platform.system() == 'Windows':
        subtitle_path = subtitle_path.replace("\\", "/")
        subtitle_path = subtitle_path.replace(":", "\\:")
        logger.info(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")

    command_add_subtitles = [
        'ffmpeg',
        '-loglevel', 'error',  # 只输出错误信息
        '-y',  # 覆盖
        '-i', input_path,  # 合并后的中间文件
        '-vf', f"subtitles=\'{subtitle_path}\':force_style='FontName=Microsoft YaHei,FontSize=24'",  # 添加字幕
        '-c:v', 'libx264',  # 编码视频
        '-crf', '23',  # 压缩质量
        '-preset', 'fast',  # 编码速度
        output_path  # 最终输出文件路径
    ]

    logger.info(f"Running FFmpeg command: command_add_subtitles ...")
    subprocess.run(command_add_subtitles, check=True)
    logger.info(f"Finish FFmpeg command: command_add_subtitles")
    os.remove(input_path)
    os.rename(output_path, input_path)


def make_cover(cover_path, novel_name, chapter, chunk, output_path):
    # if platform.system() == 'Windows':
    #     picture_path=picture_path.replace(":", "\\:")
    #     logger.info(f"This is a Windows system. play a path trick ...modify path as : {subtitle_path}")
    command = [
        'ffmpeg',
        '-y',  # 覆盖
        '-i', cover_path,
        '-vf',
        f"drawtext=text='{novel_name}\n 第{chapter}章\n  ({chunk})':fontfile='C\\:/Windows/Fonts/msyh.ttc':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=128:fontcolor=white",
        output_path
    ]

    try:
        logger.info("Running FFmpeg command make_cover...")
        subprocess.run(command, check=True)
        logger.info("Video processing completed successfully!")
    except subprocess.CalledProcessError as e:
        logger.info("Failed to process video:", e)


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
    logger.info(command)
    # ffmpeg - i
    # D: / temp_medias / jieya_video / chongyaji.mp4 - i
    # D: / temp_medias / binglinchengxia / cover2.jpg - filter_complex
    # "[1:v]scale=iw:ih[in];[0:v][in]overlay=0:0:enable='between(t,0,0.1)'" - shortest - y
    # output.mp4

    try:
        logger.info("Running FFmpeg command add cover ...")
        subprocess.run(command, check=True)
        logger.info("Video processing completed successfully!")
    except subprocess.CalledProcessError as e:
        logger.info("Failed to process video:", e)


def maybe_download_images(shot_info, work_dir):
    os.makedirs(f"{os.path.abspath(work_dir)}/media/images/", exist_ok=True)
    do_download = False
    for shot in shot_info:
        if 'image_url' in shot and 'image_path' not in shot:
            image_url = shot["image_url"]
            shot_num = shot['shot_num']
            image_path = f"{os.path.abspath(work_dir)}/media/images/shot_{shot_num}.png"
            if os.path.exists(image_path):
                logger.info(f"{image_path} already exists.")
                shot['image_path'] = image_path
                continue
            logger.info(f"starting download {image_path}")
            try:
                response = requests.get(image_url)
                time.sleep(2)
            except Exception as e:
                print(e)
                time.sleep(2)

            # 下载图片并将图片保存到 image_path 的文件中
            with open(image_path, "wb") as f:
                f.write(response.content)

            # 将image_path添加到原来应答的json中
            shot["image_path"] = image_path
            do_download = True
    if do_download:
        with open(work_dir + "/shot_info.json", 'w') as f:
            json.dump(shot_info, f, ensure_ascii=False, indent=4)
    return shot_info


def direct_concat_videos(work_dir, video_path_list):
    # 合并视频， 必须要先将所有需要合并的视频路径写入到一个txt文件中，再合并
    with open(f"{work_dir}/contact_videos.txt", "w", encoding='utf-8') as f:
        for video in video_path_list:
            f.write(f"file '{video}'\n")

    concat_command = [
        'ffmpeg',
        '-loglevel', 'error',  # 只输出错误信息
        '-y',
        '-f', 'concat',
        '-safe', '0',  # 允许文件名中有特殊字符
        '-i', f'{work_dir}/contact_videos.txt',  # 输入的合并文件
        '-c', 'copy',
        f'{work_dir}/concat.mp4'
    ]

    logger.info(f"Running FFmpeg command: concat_command ...")
    subprocess.run(concat_command, check=True)
    logger.info("Video concatenation completed successfully!")


def concat_videos_with_fade_transitions(work_dir, videos_path_list_with_time, transition_duration=1):
    concat_command = ['ffmpeg',
                      '-loglevel', 'error',  # 只输出错误信息
                      '-y']

    # 添加输入文件和滤波器复杂度选项
    filter_complex = []
    for idx, (video_path, start_time_ms, duration_time_ms) in enumerate(videos_path_list_with_time):
        concat_command.extend(['-i', video_path])

        duration_time_s = duration_time_ms / 1000
        start_time_pts = f"PTS-STARTPTS+{start_time_ms / 1000:.3f}/TB"

        # 第一个视频不需要淡入效果
        if idx == 0:
            filter_str = (
                f'[{idx}:v]format=pix_fmts=yuva420p,fade=t=out:st={duration_time_s}:d={transition_duration}:alpha=1,setpts=PTS-STARTPTS[va{idx}];'
            )
        # 最后一个视频不需要淡出效果
        elif idx == len(videos_path_list_with_time) - 1:
            filter_str = (
                f'[{idx}:v]format=pix_fmts=yuva420p,fade=t=in:st=0:d={transition_duration}:alpha=1,setpts={start_time_pts}[va{idx}];'
            )
        else:
            # 构建滤波器复杂度字符串
            filter_str = (
                f'[{idx}:v]format=pix_fmts=yuva420p,fade=t=in:st=0:d={transition_duration}:alpha=1,fade=t=out:st={duration_time_s}:d={transition_duration}:alpha=1,setpts={start_time_pts}[va{idx}];'
            )
        filter_complex.append(filter_str)

    # 拼接overlay操作
    overlay_commands = []
    for i in range(len(videos_path_list_with_time) - 1):
        if i == 0:
            overlay_str = f'[va{i}][va{i + 1}]overlay=format=yuv420[ov{i + 1}];'
        elif i == len(videos_path_list_with_time) - 2:
            overlay_str = f'[ov{i}][va{i + 1}]overlay=format=yuv420[outv]'
        else:
            overlay_str = f'[ov{i}][va{i + 1}]overlay=format=yuv420[ov{i + 1}];'
        overlay_commands.append(overlay_str)

    filter_complex.extend(overlay_commands)

    # 添加其余参数
    concat_command.extend([
        '-filter_complex', "".join(filter_complex),
        '-map', '[outv]',
        f'{work_dir}/concat.mp4'
    ])

    logger.info(f"Running FFmpeg command: concat_command ...")
    subprocess.run(concat_command, check=True)
    logger.info("Video concatenation completed successfully!")


def concat_images_to_video(work_dir, shot_info=None, video_ratio="16:9"):
    """
    将shot_info中的每一个image和duration生成视频，并将所有视频合并成一个视频
    :param shot_info需要包含:
      [{"image_path" : "./images/1.jpg", "duration" : 5400},
       {"image_path" : "/Users/AI图片素材/images/2.jpg", "duration" : 210},
       {"image_path" : "./images/3.jpg", "duration" : 4200}]
    - image_path是图片路径（可以是相对路径，也可以是绝对路径）
    - duration是图片显示时间，单位毫秒

    :param output_path: 合并后的视频路径
    :param special_effect: 特效，目前支持"zoompan left_up"和"zoompan center"
    """
    if video_ratio == "16:9":
        video_size = "1920x1080"
    elif video_ratio == "9:16":
        video_size = "1080x1920"
    else:
        raise ValueError("Unsupported video ratio. Supported ratios are '16:9' and '9:16'.")

    if os.path.exists(f'{work_dir}/concat.mp4'):
        logger.info(f"concat.mp4 already exists.")
        return
    if shot_info is None:
        shot_info = load_shot_info(work_dir)

    shot_info = maybe_download_images(shot_info, work_dir)

    # 根据每一个image和duration生成视频
    tmp_output_video_path_list = []
    tmp_output_video_path_list_with_time = []
    for image_with_duration in shot_info:
        image_path = image_with_duration["image_path"]
        duration = image_with_duration["duration_ms"]
        duration = float(duration) / 1000
        tmp_output_video_path = image_path.replace(".png", ".mp4")

        fps = 100
        # zoom_factor代表每秒放大的比例
        zoom_factor = 0.015
        special_effect = {
            # 缩放, z代表每一帧的缩放比例, s代表输出视频的宽高, fps代表每秒帧数, d代表总共的帧数
            "zoompan_left_up": f"zoompan=z='zoom+{zoom_factor / fps}':s={video_size}:fps={fps}:d={fps}*{duration}",
            "zoompan_left_down": f"zoompan=x='0':y='ih*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_right_up": f"zoompan=x='iw*(1-1/zoom)':y='0':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_right_down": f"zoompan=x='iw*(1-1/zoom)':y='ih*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_center": f"zoompan=x='iw/2*(1-1/zoom)':y='ih/2*(1-1/zoom)':z='zoom+{zoom_factor / fps}':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_left_to_right": f"zoompan='1.2':x='if(lte(on,-1),(iw-iw/zoom)/2,x+0.1)':y='if(lte(on,1),(ih-ih/zoom)/2,y)':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_right_to_left": f"zoompan='1.2':x='if(lte(on,1),(iw/zoom)/2,x-0.1)':y='if(lte(on,1),(ih-ih/zoom)/2,y)':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_up_to_down": f"zoompan='1.2':x='if(lte(on,1),(iw-iw/zoom)/2,x)':y='if(lte(on,-1),(ih-ih/zoom)/2,y+0.05)':fps={fps}:d={fps}*{duration}:s={video_size}",
            "zoompan_down_to_up": f"zoompan='1.2':x='if(lte(on,1),(iw-iw/zoom)/2,x)':y='if(lte(on,1),(ih/zoom)/2,y-0.05)':fps={fps}:d={fps}*{duration}:s={video_size}",
        }
        # 原始不缩放
        # random select a value from special_effect

        special_effect = random.choice(list(special_effect.values()))
        single_image2vid_command = [
            'ffmpeg',
            '-loglevel', 'error',  # 只输出错误信息
            '-y',
            '-i', image_path,  # 输入图片路径
            '-filter_complex',  # 滤镜复合
            special_effect,
            tmp_output_video_path  # 输出视频路径
        ]
        if not os.path.exists(tmp_output_video_path):
            logger.info(f"Running FFmpeg command: single_image2vid_command for {image_path} ...")
            subprocess.run(single_image2vid_command, check=True)
        else:
            logger.info(f"{tmp_output_video_path} already exists.")

        tmp_output_video_path_list.append(tmp_output_video_path)
        tmp_output_video_path_list_with_time.append(
            (tmp_output_video_path, image_with_duration["start_time_ms"], image_with_duration["duration_ms"]))

    # 合并所有视频
    concat_videos_with_fade_transitions(work_dir, tmp_output_video_path_list_with_time)

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
