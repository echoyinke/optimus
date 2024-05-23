import json
import os.path

from optimus_tools.ffmpeg_utils import  concat_images_to_video
from optimus_tools.http_utils import deepseekv2, tongyiwx_call


def subtile_to_video_shots(sentence_path, video_shots_num, save_dir):
    """
    把字幕文件（sentences）拆分成镜头,方便后面文生图
    """
    if os.path.exists(f"{save_dir}/video_shots_info.json"):
        return
    with open(sentence_path, 'r') as file:
        file_content = file.read()
    file_content = file_content.replace("'", '"')
    data = json.loads(file_content)
    total_duration = data[-1]['end'] - data[0]['start']
    segment_duration = total_duration // video_shots_num
    merged_data = []
    current_segment = {'text': '', 'start': 0, 'end': None, 'duration': 0}
    for i, item in enumerate(data):
        duration = item['end'] - current_segment['start']
        current_segment['text'] += item['text']
        current_segment['end'] = item['end']
        current_segment["duration"] = duration
        if item['end'] - current_segment['start'] >= segment_duration:
            merged_data.append(current_segment)
            current_segment = {'text': '', 'start': item["end"], 'end': None, 'duration': 0}
    # 检查最后一个段落的长度, 如果太短就合并
    if current_segment['duration'] > 0 and current_segment['duration'] < segment_duration // 1.5 and merged_data:
        # 合并到倒数个segment中
        merged_data[-2]['text'] += current_segment['text']
        merged_data[-1]['end'] = current_segment['end']
        merged_data[-1]['duration'] = current_segment['end'] - merged_data[-1]['start']
    else:
        merged_data.append(current_segment)
    with open(f"{save_dir}/video_shots_info.json", 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

def subtitle2video(work_dir, video_shots_num):
    sentence_path = f"{work_dir}/sentences"
    subtile_to_video_shots(sentence_path, video_shots_num, work_dir)
    video_shot_info_path = f"{work_dir}/video_shots_info.json"
    video_shots_info=llm_augment_and_gen_image(video_shot_info_path, work_dir)
    concat_images_to_video(images_with_duration_list=video_shots_info, work_dir=work_dir)

def llm_augment_and_gen_image(video_shots_info_path, work_dir):
    with open(video_shots_info_path, 'r', encoding='utf-8') as f:
        # 使用 json.load() 从文件中加载数据
        data = json.load(f)
    chunk_text = ''
    for d in data:
        chunk_text+=d['text']
    for i, d in enumerate(data):
        if "image_path" in d:
            continue
        aug_prompt = deepseekv2(d['text'], chunk_text)
        prompt = json.loads(aug_prompt)['choices'][0]['message']['content']
        d['aug_prompt'] = prompt
        image_path= f"{work_dir}/{i}.jpg"
        code = tongyiwx_call(prompt, image_path)
        #
        if code == "DataInspectionFailed":
            aug_prompt = deepseekv2(d['text']+"。另外，请注意使用合规的描述！避免色情暴力偏见及政治错误", chunk_text)
            prompt = json.loads(aug_prompt)['choices'][0]['message']['content']
            d['aug_prompt'] = prompt
            code = tongyiwx_call(prompt, image_path)

        d['image_path'] = image_path
    with open(video_shots_info_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data


if __name__ == '__main__':

    sentence_path = "D:/temp_medias/binglinchengxia\兵临城下\chapter_0\chunk_57/sentences"
    shots_path = "/Users/yinke/PycharmProjects/optimus/optimus_tools/outputs/split_shots.json"
    aug_shots = "/Users/yinke/PycharmProjects/optimus/optimus_tools/outputs/aug_split_shots.json"
    # subtile_to_video_shots(sentence_path, 5,  "D:/temp_medias/binglinchengxia\兵临城下\chapter_0")
    info_path = "D:/temp_medias/binglinchengxia\兵临城下\chapter_0\chunk_58/video_shots_info.json"
    with open(info_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    concat_images_to_video(images_with_duration_list=data, work_dir="D:/temp_medias/binglinchengxia\兵临城下\chapter_0\chunk_58/")

