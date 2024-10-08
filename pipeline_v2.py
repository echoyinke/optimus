import os.path

from optimus_tools.log_utils import get_logger

from optimus_tools.ffmpeg_utils import merge_video_audio, add_subtile, change_video_speed, add_bgm
from optimus_tools.text2image_utils import concat_images_to_video

logger = get_logger(__name__)
from optimus_tools.asure_cognition import gen_subtile, text2speech_with_timestamp


def img2vid_from_coze_outputs(curr_work_dir):
    text2speech_with_timestamp(curr_work_dir)
    concat_images_to_video(curr_work_dir)
    merge_video_audio(curr_work_dir)
    # gen_subtile(curr_work_dir)
    # add_subtile(curr_work_dir)
    add_bgm(curr_work_dir, video_path = curr_work_dir + "/video.mp4", music_path = "./bgm/suspend/1.mp3")
    change_video_speed(curr_work_dir)


if __name__ == '__main__':
    abs_path=os.path.abspath("./debug")
    img2vid_from_coze_outputs(abs_path)
