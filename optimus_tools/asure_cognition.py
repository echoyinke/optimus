import azure.cognitiveservices.speech as speechsdk
import json
import re
from .log_utils import get_logger
import os
import datetime
from .coze_utils import load_shot_info

log=get_logger("asure_cognition")



def text2speech_with_timestamp(workdir):
    '''

    Args:
        workdir: 工作目录，确保里面包含shot_info.json

    Returns:

    '''
    # 正则化sentences
    curr_work_dir = os.path.abspath(workdir)
    if os.path.exists(f"{curr_work_dir}/output.wav"):
        raise ValueError("output.wav already exists.")
    shot_info=load_shot_info(curr_work_dir)

    def normalize_text(text):

        # 去除不可见的零宽字符和空格
        text = re.sub(r'\s+', ' ', text)  # 将多个空格替换为一个空格

        # 保留的标点符号（中英文的句号、逗号、问号、感叹号、括号、冒号、分号、破折号、省略号等）
        pattern = r'[^a-zA-Z0-9\u4e00-\u9fa5，。？！：；（）——…,.?!()\-]'
        text = re.sub(pattern, '', text)

        return text.strip()
    sentences = [normalize_text(s['original_text']) for s in shot_info]

    # Initialize the speech configuration
    speech_config = speechsdk.SpeechConfig(subscription="dc00d3aa5b204db4a4ffbba9b96560d3", region="eastasia")
    speech_config.speech_synthesis_voice_name = "zh-CN-YunxiNeural"  # Example: Female voice named Jenny

    # Configure the output audio format
    output_wav_file=f"{workdir}/output.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_wav_file)

    # Create the synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    sentence_timestamps = []
    current_sentence_index = 0
    sentence_start_time = None
    sentence_buffer = ""
    def word_boundary_event_handler(evt):
        nonlocal shot_info, sentence_start_time, current_sentence_index, sentence_buffer
        # evt类如下
        # SpeechSynthesisWordBoundaryEventArgs(audio_offset=2875000, duration=0:00:00.300000, text_offset=2, word_length=2)
        # audio_offset 单位：100纳秒， ticks, 2875000=287 500 000ns= 287.5 毫秒
        # duration 是一个 timedelta 对象，以秒为单位的 0:00:00.300000 表示该单词的发音持续了0.3 秒
        word = evt.text
        curr_word_audio_offset_ms = evt.audio_offset / 10000  # Convert to milliseconds
        # Start time of the current sentence
        if sentence_start_time is None:
            sentence_start_time = 0

        # Append the current word to the buffer
        sentence_buffer += word

        # Debug print statements to track the buffer and matching process

        # Check if the buffered sentence matches the current sentence
        expected_sentence = sentences[current_sentence_index].strip()
        info = shot_info[current_sentence_index]
        if sentence_buffer.strip() == expected_sentence.strip():
            # evt.duration.total_seconds() 将 timedelta 转换为秒
            end_time = curr_word_audio_offset_ms + int(evt.duration.total_seconds() * 1000)  # End time of the sentence
            duration = end_time - sentence_start_time
            info.update({
                "sentence": sentence_buffer.strip(),
                "start_time_ms": sentence_start_time,
                "end_time_ms": end_time,
                "duration_ms": duration
            })
            # 将当前句子的结束时间作为下一个句子的开始时间
            sentence_start_time = end_time
            sentence_buffer = ""  # Clear the buffer
            current_sentence_index += 1
        if len(sentence_buffer.strip()) > len(expected_sentence.strip()):
            log.info(f"evt is:{evt}, word:{word}")
            log.info(f"sentence_buffer  : {sentence_buffer.strip()}")
            log.info(f"expected_sentence: {expected_sentence.strip()}")

    # Connect the event handler
    synthesizer.synthesis_word_boundary.connect(word_boundary_event_handler)

    # Synthesize the sentences as a single text block
    full_text = "\n".join(sentences)
    result = synthesizer.speak_text_async(full_text).get()

    # Check if synthesis completed successfully
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        log.info(f"Audio content written to file '{output_wav_file}'")
        with open(curr_work_dir+"/shot_info.json", 'w') as f:
            json.dump(shot_info, f, ensure_ascii=False, indent=4)
        log.info(f"tts info updated to shot_info.json.")

    else:
        log.info(f"Speech synthesis failed with reason: {result.reason}")
        if result.error_details:
            log.info(f"Error details: {result.error_details}")
def gen_subtile(workdir):
    curr_work_dir = os.path.abspath(workdir)
    if os.path.exists(f"{curr_work_dir}/output.srt"):
        log.info("output.srt already exists.")
        return
    def format_srt_timestamp(ms):
        """将毫秒格式化为 SRT 时间戳格式"""
        td = datetime.timedelta(milliseconds=ms)
        # 确保输出格式为 hh:mm:ss,ms
        total_seconds = int(td.total_seconds())
        milliseconds = int(ms % 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    def create_srt(sentences_with_timestamps, output_file):
        """根据句子的时间戳信息生成 SRT 文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, item in enumerate(sentences_with_timestamps, start=1):
                start_time = format_srt_timestamp(item['start_time_ms'])
                end_time = format_srt_timestamp(item['end_time_ms'])
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{item['sentence']}\n\n")
    # 生成字幕文件
    abs_workdir = os.path.abspath(workdir)
    with open(abs_workdir+"/shot_info.json", 'r', encoding='utf-8') as file:
        shot_info = json.load(file)
    output_srt_file = f"{workdir}/output.srt"
    create_srt(shot_info, output_srt_file)
    log.info(f"Subtitle content written to file '{output_srt_file}'")
    return shot_info

if __name__ == '__main__':
    # shot_info=text2speech_and_subtile("/Users/yinke/PycharmProjects/optimus/debug")
    # print(shot_info)

    gen_subtile("./debug")