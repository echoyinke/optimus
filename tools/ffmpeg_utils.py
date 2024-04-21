import subprocess
import platform



import ffmpeg

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

if __name__ == '__main__':
    video_path =  'D:/temp_medias/jieya.mp4'
    audio_path = 'D:/temp_medias/speech.wav'
    subtitle_path = 'D:/temp_medias/subtitles/total.srt'
    output_path = 'D:/temp_medias/output.mp4'
    merge_video_audio_subtitle(video_path,audio_path , subtitle_path,output_path)
