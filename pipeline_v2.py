from optimus_tools.log_utils import get_logger

from optimus_tools.ffmpeg_utils import merge_video_audio
from optimus_tools.text2image_utils import concat_images_to_video
from optimus_tools.coze_api import preview_shot_info

logger = get_logger(__name__)
from optimus_tools.asure_cognition import gen_subtile, text2speech_with_timestamp


def img2vid_from_coze_outputs(curr_work_dir):
    preview_shot_info(curr_work_dir)
    input("please preview the preview.html... 按任意键继续....")
    text2speech_with_timestamp(curr_work_dir)
    concat_images_to_video(curr_work_dir)
    merge_video_audio(curr_work_dir)
    # gen_subtile(curr_work_dir)
    # add_subtile(curr_work_dir)
    # change_video_speed(curr_work_dir)


if __name__ == '__main__':
    img2vid_from_coze_outputs("your/workdir")
