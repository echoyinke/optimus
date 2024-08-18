# -*- coding: utf-8 -*-

import requests
import json
import uuid
import os

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

    response = requests.request("POST", url, headers=headers, data=payload)

    
    # 将应答保存到base_dir中
    with open(basedir + "/" + "orig_coze_response.json", "w",encoding='utf-8') as f:
        f.write(response.text)
    
    # 尝试使用 json.dump 解析应答中的内容，如果无法解析则返回None
    try:
        response_json = json.loads(response.text)
    except json.JSONDecodeError:
        print('Response is not JSON')
        print(response.text)
        return None


    for message in response_json["messages"]:
        if message["role"] == "assistant" and message["type"] == "answer":
            try:
                answer = json.loads(message["content"])
            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON from content {message['content']}")
                raise e
    # 如果answer为空，则返回None
    if not answer:
        print("invalid response")
        return None
    
    output = download_image(answer, basedir)

    # 保存新的应答到base_dir中
    with open(basedir + "/" + "shot_info.json", "w",encoding='utf-8') as f:
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
    

if __name__ == "__main__":
    text = "叶芷白,让车给创死了。\n被神明变成了银发紫瞳的冰山美少女,超有钱的小富婆。\n上辈子穷困潦倒,为晚饭吃几根葱发愁的叶芷白,人生突然好起来了!\n——除了变成女生这一点!\n但万幸...有一张难以接近的冰山面容，想必她们也不敢...\n“嘿嘿...芷白，你笑起来真好看～”\n“小白，昨天说好的亲亲，还没兑现呐。”\n“姐姐，请和她们保持一定距离！"
    basedir = "../debug"
    response_json = text2images_by_coze(text, basedir)
    print(response_json)

    # with open(basedir + "/" + "orig.json", "r") as f:
    #     response_json = json.loads(f.read())
    # response_json =  download_image(response_json, basedir)
    # print(json.dumps(response_json, ensure_ascii=False))