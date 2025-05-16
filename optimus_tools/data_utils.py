import platform
import matplotlib.font_manager as fm
from matplotlib import rcParams
import logging
import requests
from time import sleep
import json
import jsonlines
import os
import random
from tqdm import tqdm
from typing import Union, List, Any, Dict
import codecs
from typing import Generator

# 设置模块级 logger
logger = logging.getLogger(__name__)


# 设置全局字体

try:
    if platform.system() == "Darwin":  # macOS 系统
        font_path = "/System/Library/Fonts/Supplemental/Songti.ttc"
    elif platform.system() == "Linux":  # Linux 系统
        font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    zh_font = fm.FontProperties(fname=font_path)
    rcParams['font.sans-serif'] = [zh_font.get_name()]
    rcParams['axes.unicode_minus'] = False
except Exception as e:
    logger.warning("Font path is not set for this operating system.")


########################################
#                磁盘I/O               #
########################################


def read_data(input_paths: Union[str, List[str]]) -> List[Any]:
    """
    通用的读取数据函数，支持 JSON 和 JSONL 文件，单个文件或文件夹路径。

    参数:
        input_paths (Union[str, List[str]]): 文件路径或文件夹路径，可以是单个字符串或列表。

    返回:
        List[Any]: 所有文件中合并的数据。
    """
    if isinstance(input_paths, str):
        input_paths = [input_paths]

    file_list = []
    for path in input_paths:
        # 将路径转换为绝对路径
        abs_path = os.path.abspath(path)
        # 判断路径是否存在
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path does not exist: {abs_path}")
        if os.path.isfile(abs_path):
            file_list.append(abs_path)
        elif os.path.isdir(abs_path):
            for root, _, files in os.walk(abs_path):
                for file_name in files:
                    file_list.append(os.path.join(root, file_name))

    all_data = []
    for file_path in file_list:
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data if isinstance(data, list) else [data])
                logger.info(f"Loaded {len(data)} items from {file_path}.")
        elif file_path.endswith('.jsonl'):
            logger.info(f"Begin to load items from {file_path}.")
            with jsonlines.open(file_path, mode='r') as reader:
                lenth_before = len(all_data)
                all_data.extend(reader)
            logger.info(
                f"Loaded {len(all_data)-lenth_before} items from {file_path}.")
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    if not all_data:
        logger.error(f"No data found in the provided paths: {input_paths}")
    if len(file_list) > 1:
        logger.info(f"Totally Loaded {len(all_data)} items.")
    return all_data

def process_streaming_response(response: requests.Response, delimiter: str = "\n\n") -> Generator[dict, None, None]:
    """
    处理流式响应，逐块解析 JSON 数据，并返回生成器
    """
    # 检查 response.raw 是否可用
    if not response.raw:
        raise RuntimeError("Raw stream is not available. The response might have been closed.")
    
    chunk_index = 0
    message_id, usage, finish_reason = None, None, None
    full_assistant_content = ""

    # 处理 delimiter 的 Unicode 转义
    delimiter = codecs.decode(delimiter, "unicode_escape")
    
    try:
        for chunk in response.iter_lines(decode_unicode=True, delimiter=delimiter):
            chunk = chunk.strip()
            if not chunk or chunk.startswith(":"):  # 跳过空行和 SSE 注释
                continue

            decoded_chunk = chunk.lstrip("data: ").strip()
            if decoded_chunk == "[DONE]":  # 处理 API 结束标记
                break

            try:
                chunk_json = json.loads(decoded_chunk)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON encountered: {decoded_chunk}")
                yield {
                    "id": message_id,
                    "chunk_index": chunk_index + 1,
                    "message": "",
                    "finish_reason": "Non-JSON encountered.",
                    "usage": usage,
                }
                break

            if "usage" in chunk_json:
                usage = chunk_json["usage"]

            if not chunk_json.get("choices"):
                continue

            choice = chunk_json["choices"][0]
            finish_reason = choice.get("finish_reason")
            message_id = chunk_json.get("id")
            chunk_index += 1

            content_piece = ""
            if "delta" in choice and "content" in choice["delta"]:
                content_piece = choice["delta"]["content"]
            elif "text" in choice:
                content_piece = choice["text"]

            if content_piece:
                full_assistant_content += content_piece

            yield {
                "id": message_id,
                "chunk_index": chunk_index,
                "content": content_piece,
                "full_message": full_assistant_content,
                "finish_reason": finish_reason,
                "usage": usage,
            }
    except Exception as e:
        logger.error(f"Exception while processing stream: {e}")
        raise

def write_json(data: Any, file_path: str) -> None:
    """
    通用的写 JSON 文件函数。

    参数:
        data (Any): 要写入的数据。
        file_path (str): 输出文件路径。
    """
    if not data:
        raise ValueError(f"数据为空，无法写入文件：{file_path}")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info(f"数据已成功写入到 {file_path}")


def remove_exists(input_data: List[dict], output_file: str) -> List[dict]:
    """
    从输入数据中过滤掉已经存在于输出文件中的条目。

    参数:
        input_data (List[dict]): 输入的数据列表。
        output_file (str): 输出文件路径。

    返回:
        List[dict]: 过滤后的数据列表。
    """
    try:
        output_data = read_data(output_file)
        existing_keys = {item["dedup_key"] for item in output_data}
        return [item for item in input_data if item.get("dedup_key") not in existing_keys]
    except Exception as e:
        logger.error(f"Failed to filter existing data: {e}")
        return input_data


########################################
#                网络I/O               #
########################################

class MaxRetriesExceeded(Exception):
    """Custom exception for exceeding maximum retry attempts."""
    pass


def send_post_request(url: str, headers: Dict[str, str], payload: dict, stream=False, timeout=(30, 360), retries: int = 3) -> dict:
    # 这里只封装retry异常，其他都透传
    # 在 requests 库中，timeout 参数的默认值是 None。这意味着，如果没有显式指定 timeout 参数，客户端将不会设置超时时间，直到服务器响应或连接被关闭。
    for attempt in range(retries):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=timeout, stream=stream)
            response.raise_for_status()
            return response if stream else response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"[Timeout]: {e} on attempt {attempt + 1}, retrying...")
            sleep(random.randint(5, 10) * (2 ** attempt))
        except requests.exceptions.HTTPError as e:
            if response.status_code == 504:
                logger.warning(f"[504]: {e} on attempt {attempt + 1}, retrying...")
                sleep(random.randint(5, 10) * (2 ** attempt))
            else:
                raise e  # 其他 HTTP 错误，直接抛出
    raise MaxRetriesExceeded(
        f"Max retries({retries}) reached for timeout reason. timeout setting is ({timeout}).")

# 示例：如何使用该函数
if __name__ == "__main__":

    url = "http://1411998742277274.cn-wulanchabu.pai-eas.aliyuncs.com/api/predict/qwq_32b/v1/chat/completions"
    headers = {
        "Authorization": "Bearer OWI3YTNlNTk0ZmQ3ODI5NTVjZWJmYTI3Yjc3NGNmYzcwZTlhMzNlNQ=="}

    payload = {
        "model": "QwQ-32B",
        "messages":   [
            {
                "content": "你好",
                "role": "user"
            }
        ],
        "temperature": 0.6,
        "top_k": 20,
        "top_p": 0.95,
        "stream":True
    }

    response = send_post_request(url, headers=headers, payload=payload, stream=True)

    full_message = list(process_streaming_response(response))[-1]['full_message']

    print("\n=== Final Message ===")
    print(full_message)