import subprocess
import platform



import ffmpeg

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
        print("Running FFmpeg command...")
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

if __name__ == '__main__':
    video_path =  'D:/temp_medias/jieya_video/chongyaji.mp4'
    audio_path = 'D:/temp_medias/dev/speech.wav'
    subtitle_path = 'D:/temp_medias/dev/total.srt'
    output_path = 'D:/temp_medias/output.mp4'
    input_cover = 'D:/temp_medias/binglinchengxia/cover.jpg'
    cover_path= 'D:/temp_medias/binglinchengxia/cover2.jpg'
    #merge_video_audio_subtitle(video_path,audio_path ,output_cover, subtitle_path,output_path)
    # make_cover(input_cover,1, 0, output_cover)
    add_cover(video_path, cover_path, output_path)