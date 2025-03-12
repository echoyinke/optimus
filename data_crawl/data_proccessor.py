import logging
import copy
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import jsonlines
import os
import re
from datetime import datetime
import callers
from utils import read_data, write_json, send_post_request
import traceback


# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 主脚本 logger
logger = logging.getLogger(__name__)


# 业务逻辑函数
def register_callers():
    """
    自动注册当前模块中所有以 _caller 结尾的函数
    """
    caller_dict = {}
    for name in dir(callers):
        obj = getattr(callers, name)
        if callable(obj) and name.endswith('_caller'):
            caller_dict[name] = obj

    return caller_dict


def process_jsonl_file(data, output_file, caller, response_key, num_workers, already_proccessed_num):
    """
    处理 .jsonl 文件的逻辑，进行并发请求并写入处理结果。
    """
    logger.info(f"Processing {len(data)} items with {caller.__name__}...")
    need_proccess_data = data[already_proccessed_num:]
    logger.info(
        f"Skipping {already_proccessed_num} items, processing remaining {len(need_proccess_data)} items...")
    processed_results = []  # 存储处理后的结果
    consecutive_failure_count = 0  # 用于记录连续失败的次数
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with jsonlines.open(output_file, mode='a') as writer:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(
                    caller, item, response_key): item for item in need_proccess_data}
                for future in tqdm(as_completed(futures), total=len(data), desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Processed", unit="item", initial=already_proccessed_num + 1):
                    try:
                        future.result()  # 这里去拿结果，会阻塞线程，如果有异常会抛出，跳到异常处理
                        consecutive_failure_count = 0  # 成功则重置连续失败计数器
                    except Exception as e:
                        consecutive_failure_count += 1  # 失败则增加连续失败计数器
                        item = futures[future]
                        item['error'] = str(e)  # 异常的话添加异常信息
                        error_traceback = traceback.format_exc()  # 获取完整的异常堆栈信息
                        logger.error(
                            f"Error processing item with dedup_key {item.get('dedup_key', 'UNKNOWN')}:\n{error_traceback}"
                        )
                    item = futures[future]  # 获取处理后的 item
                    processed_results.append(item)  # 将处理后的 item 添加到结果列表
                    writer.write(item)  # 写入文件

                    # 如果连续失败次数超过阈值，直接中止处理
                    if consecutive_failure_count >= num_workers:
                        # 先把作业都cancel
                        for future_to_cancel in futures:
                            future_to_cancel.cancel()
                        # 抛出异常
                        raise RuntimeError(
                            f"Consecutive failure threshold ({num_workers}) exceeded...\nExiting process...")

    finally:
        total_count = len(processed_results)
        success_count = sum(
            1 for item in processed_results if "error" not in item)
        failure_count = total_count - success_count  # 失败的数量是总数减去成功的数量
        logger.info(
            f"\n\n######################  Proccess Summary  ######################")
        logger.info(f"Skip {already_proccessed_num} items.")
        logger.info(f"Total {total_count} items processed.")
        logger.info(f"Failed to process {failure_count} items.")
        logger.info(f"Successfully processed {success_count} items.")
        logger.info(f"Processed results written to {output_file}...")
        logger.info(
            f"\n##################################################################\n\n")


def process_json_file(data, output_file, caller, response_key, num_workers):
    """
    处理 .json 文件的逻辑，进行并发请求并写入处理结果。
    """
    processed_results = []  # 存储处理后的结果

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(
            caller, item, response_key): item for item in data}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing items", unit="item"):
            future.result()
            item = futures[future]  # 获取处理后的 item
            processed_results.append(item)  # 将处理后的 item 添加到结果列表

    write_json(processed_results, output_file)

    # 统计成功和失败的数量
    total_count = len(processed_results)
    success_count = sum(1 for item in processed_results if "error" not in item)
    failure_count = total_count - success_count  # 失败的数量是总数减去成功的数量
    logger.info(f"Total {total_count} items processed.")
    logger.info(f"Successfully processed {success_count} items.")
    logger.warning(f"Failed to process {failure_count} items.")
    logger.info(f"Processed results written to {output_file}")


def proccess_items(data, caller, output_file, response_key, num_workers, already_proccessed_num):
    """
    主处理函数，判断文件类型并调用对应的处理函数。
    """
    file_extension = output_file.split(".")[-1]

    if file_extension == 'jsonl':  # 如果是 .jsonl 文件
        process_jsonl_file(data, output_file, caller,
                           response_key, num_workers, already_proccessed_num)
    elif file_extension == 'json':  # 如果是 .json 文件
        if already_proccessed_num > 0:
            raise ValueError(
                "Resume mode is only supported for '.jsonl' files. To continue processing, use a '.jsonl' file or remove the existing output file.")
        process_json_file(data, output_file, caller, response_key, num_workers)
    else:
        raise ValueError(
            "Unsupported file format. Only '.json' and '.jsonl' are supported.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Process items and call services.")
    parser.add_argument('--caller', type=str, default='qwen2_caller',
                        help="The caller function to use.")
    parser.add_argument('--response_key', type=str,
                        default='response', help="The key to update in each item.")
    parser.add_argument('--input_paths', type=str, nargs='+',
                        required=True, help="The input data file paths.")
    parser.add_argument('--output_file', type=str,
                        required=True, help="The output file path.")
    parser.add_argument('--num_workers', type=int, default=4,
                        help="Number of worker threads for concurrent processing.")  # 新增参数
    parser.add_argument(
        '--debug', action='store_true', help="Enable debug mode to get more detailed logs."
    )
    return parser.parse_args()


# 主程序入口
if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    logger.info("Starting the process...")

    # 自动注册所有以 '_caller' 结尾的函数
    caller_dict = register_callers()
    logger.info(f"Available callers: {list(caller_dict.keys())}")

    caller = caller_dict[args.caller]
    if not caller:
        logger.error(f"Caller function {args.caller} not found.")
        exit(1)
    need_proccess_data = read_data(args.input_paths)
    # need_proccess_data=need_proccess_data[:2]
    if os.path.exists(args.output_file):
        already_proccessed_data = read_data(args.output_file)
    else:
        already_proccessed_data = []

    proccess_items(need_proccess_data, caller, args.output_file, args.response_key,
                      num_workers=args.num_workers, already_proccessed_num=len(already_proccessed_data))



 # python core/data_proccess.py --caller qwq_32b_caller  --response_key qwq_res --input_paths /mnt/workspace/yinke/summary/data_proccess/inputs/r1_online/eval_300.json --output_file /mnt/workspace/yinke/summary/data_proccess/outputs/r1_online/qwq_0308_eval.jsonl --num_workers 4