
from optimus_tools.log_utils import get_logger

from optimus_tools.ffmpeg_utils import merge_video_audio, add_subtile, make_cover, change_video_speed
from optimus_tools.text2image_utils import subtitle2video, calculate_image_duration, concat_images_to_video
from functools import reduce

logger = get_logger(__name__)
from optimus_tools.asure_cognition import gen_subtile, text2speech_with_timestamp

def img2vid_from_coze_outputs(curr_work_dir):
    text2speech_with_timestamp(curr_work_dir)
    gen_subtile(curr_work_dir)
    concat_images_to_video(curr_work_dir)

    merge_video_audio(curr_work_dir)
    add_subtile(curr_work_dir)
    change_video_speed(curr_work_dir)

if __name__ == '__main__':
    img2vid_from_coze_outputs("/Users/yinke/PycharmProjects/optimus/debug")