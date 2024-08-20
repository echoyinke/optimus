# -*- coding: utf-8 -*-

import requests
import json
import uuid
import os
from .log_utils import get_logger

logger = get_logger("coze_api")


def text2images_by_coze(text, basedir):
    """
    向聊天机器人发送查询并处理其响应。

    :param text: 用户的查询文本。
    :param basedir: 用于存储响应数据的目录路径。
    :return: 处理后的聊天机器人响应。
    """

    url = "https://api.coze.cn/open_api/v2/chat"

    payload = json.dumps({
        "conversation_id": str(uuid.uuid4()),
        "bot_id": "7392129560491933708",
        "user": "29032212312301862555",
        "query": text,
        "stream": False
    })
    headers = {
        'Authorization': 'Bearer pat_jyJ4WxOjAehpLveRq3FIXvALE0SaawdvuiQLLomwVQpooOfrsVWG6jLAbIAAREtp',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'api.coze.cn',
        'Connection': 'keep-alive'
    }
    logger.info("Sending request to coze...")
    response = requests.request("POST", url, headers=headers, data=payload)

    # 将应答保存到base_dir中
    with open(basedir + "/" + "orig_coze_response.json", "w", encoding='utf-8') as f:
        f.write(response.text)

    # 尝试使用 json.dump 解析应答中的内容，如果无法解析则返回None
    response_json = json.loads(response.text)
    logger.info(f"Got response from coze: {response.text}")

    for message in response_json["messages"]:
        if message["role"] == "assistant" and message["type"] == "answer":
            try:
                answer = json.loads(message["content"])
            except json.decoder.JSONDecodeError as e:
                logger.info(f"Error decoding JSON from content {message['content']}")
                raise e
    # 如果answer为空，则返回None
    if not answer:
        logger.info("invalid response")
        return None

    output = download_image(answer, basedir)

    # 保存新的应答到base_dir中
    with open(basedir + "/" + "shot_info.json", "w", encoding='utf-8') as f:
        f.write(json.dumps(output, ensure_ascii=False))

    # 返回应答
    return json.dumps(output, ensure_ascii=False)


def download_image(answer, basedir):
    basedir = os.path.abspath(basedir)
    for shot in answer["output"]:
        image_url = shot["image_url"]
        shot_num = shot['shot_num']
        image_path = f"{basedir}/shot_{shot_num}.png"
        response = requests.get(image_url)
        # 下载图片并将图片保存到 image_path 的文件中
        with open(image_path, "wb") as f:
            f.write(response.content)

        # 将image_path添加到原来应答的json中
        shot["image_path"] = image_path

    return answer["output"]


def workflow_api():
    import requests
    import json
    import time

    url = "https://api.coze.cn/v1/workflow/run"

    payload = json.dumps({
        "workflow_id": "7404102654546182180",
        "parameters": {
            "input_text": '''
    一个老旧的钨丝灯被黑色的电线悬在屋子中央，闪烁着昏暗的光芒。
    　　静谧的气氛犹如墨汁滴入清水，正在房间内晕染蔓延。
    　　房间的正中央放着一张大圆桌，看起来已经斑驳不堪，桌子中央立着一尊小小的座钟，花纹十分繁复，此刻正滴答作响。
        '''
        }
    })
    headers = {
        'Authorization': 'Bearer pat_0JPHtVxikQDKBuV7TI8iXKP8cXgJ1CnILSokm8kb8WL88B09SJyH6r7TytL9HGSY',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'api.coze.cn',
        'Connection': 'keep-alive'
    }
    start_time = time.time()

    response = requests.request("POST", url, headers=headers, data=payload)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Method executed in {execution_time:.4f} seconds")

    print(response.text)


def generate_html_from_json(json_data, output_html_file):
    # 读取JSON文件
    data = json_data
    # 开始生成HTML内容
    # 开始生成HTML内容
    html_content = """
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>图片预览</title>
          <style>
              body {
                  font-family: Arial, sans-serif;
              }
              .container {
                  display: flex;
                  flex-wrap: wrap;
                  justify-content: space-around;
              }
              .item {
                  margin: 10px;
                  border: 1px solid #ddd;
                  padding: 10px;
                  width: 300px;
                  box-sizing: border-box;
              }
              .item img {
                  max-width: 100%;
                  height: auto;
                  display: block;
                  margin-bottom: 10px;
              }
              .item p {
                  margin: 0;
                  font-size: 14px;
                  word-break: break-word;
              }
              .shot-num {
                  font-weight: bold;
                  margin-bottom: 10px;
                  font-size: 16px;
              }
              hr {
                  margin: 10px 0;
                  border: none;
                  border-top: 1px solid #ddd;
              }
          </style>
      </head>
      <body>
          <h1>图片预览</h1>
          <div class="container">
      """

    # 动态生成图片及对应的文本信息
    for idx, item in enumerate(data):
        shot_num = item.get('shot_num', 'N/A')
        image_url = item.get('image_url', '')
        original_text = item.get('original_text', '无描述')
        prompt = item.get('prompt', '无提示')

        html_content += f"""
          <div class="item">
              <div class="shot-num">Shot Number: {shot_num}</div>
              <img src="{image_url}" alt="Image {idx + 1}">
              <p><strong>Original Text:</strong> {original_text}</p>
              <hr>
              <p><strong>Prompt:</strong> {prompt}</p>
          </div>
          """

    # 结束HTML内容
    html_content += """
          </div>
      </body>
      </html>
      """
    # 将HTML内容写入文件
    with open(output_html_file, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"HTML file '{output_html_file}' has been generated successfully.")


def preview_shot_info(workdir):
    with open(workdir + "/shot_info.json", 'r', encoding='utf-8') as file:
        shot_info = json.load(file)
    if "output" in shot_info:
        shot_info = shot_info['output']
    shot_info = sorted(shot_info, key=lambda x: int(x['shot_num']))
    generate_html_from_json(shot_info, workdir + "/preview.html")
    with open(workdir + "/shot_info.json", 'w') as f:
        json.dump(shot_info, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # text = "叶芷白,让车给创死了。\n被神明变成了银发紫瞳的冰山美少女,超有钱的小富婆。\n上辈子穷困潦倒,为晚饭吃几根葱发愁的叶芷白,人生突然好起来了!\n——除了变成女生这一点!\n但万幸...有一张难以接近的冰山面容，想必她们也不敢...\n“嘿嘿...芷白，你笑起来真好看～”\n“小白，昨天说好的亲亲，还没兑现呐。”\n“姐姐，请和她们保持一定距离！"
    # basedir = "../debug"
    # response_json = text2images_by_coze(text, basedir)
    # logger.info(response_json)
    preview_shot_info("/Users/yinke/PycharmProjects/optimus/debug")

    # with open(basedir + "/" + "orig.json", "r") as f:
    #     response_json = json.loads(f.read())
    # response_json =  download_image(response_json, basedir)
    # logger.info(json.dumps(response_json, ensure_ascii=False))
