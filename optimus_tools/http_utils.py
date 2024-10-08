import argparse
import json
import os
import logging
import time

import requests
import requests
import json
deepseek_url = "https://api.deepseek.com/chat/completions"
from http import HTTPStatus
import requests
import dashscope
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
def send_dingtalk(content):
    url="https://oapi.dingtalk.com/robot/send?access_token=65d7e980139b424e9c83e21a0bd9bbd7a48cfa75815eda0749d71e13521cd2e1"
    content = "Optimus" + content
    payload = json.dumps({"msgtype": "text","text": {"content": content}})
    headers = {
        'Content-Type': 'application/json'
    }
    res = requests.request("POST", url, headers=headers, data=payload)

def deepseekv2(shot, chunk):

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"请根据我下面给你的小说段落,针对其中抽取的一部分，生成1张漫画镜头描述，记住，请尽量根据抽取的这一部分生成描述，这个描述请尽量细致，你可以适当的丰富它，以使的画面更加吸引人。抽取的部分是：{shot}, 我是从这段里面抽取的：{chunk}"
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-9e3c34cb9cc248b7a700aec20c2ef6a3',
        'Cookie': 'HWWAFSESID=a9bfb1e1d8b31ddd03b; HWWAFSESTIME=1716101437115'
    }

    response = requests.request("POST", deepseek_url, headers=headers, data=payload)

    return response.text

def polish_content(content):

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"""# 角色
你是一位擅长优化小说的高手，能够在保持原有故事线的基础上，将给定的小说片段改写成更吸引眼球且通俗易懂的内容。

## 技能
### 技能 1: 提取吸引人的片段
1. 仔细阅读给定的小说，筛选出情节紧张、冲突强烈或具有戏剧性的片段。
2. 确保所选片段能够独立成章，且具有吸引读者的潜力。

### 技能 2: 改写片段
1. 使用简单直白的语言，避免复杂的修饰和高深的词汇。
2. 运用夸张手法，增强情节的紧张刺激感。
3. 着重打造精彩的开头，使其瞬间抓住读者的注意力。
4. 精心设计结尾，留下悬念，引发读者对后续情节的强烈渴望。

## 限制:
- 严格遵循原小说的故事线，不得随意更改主要情节。
- 语言务必简练通俗，避免使用复杂的修辞手法和华丽的文笔。
- 保证开头和结尾的吸引力和悬念感。
- 请直接输出小说内容，不要有多余的内容

以下是需要优化的小说内容:
{content}"""}
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-4912501ddff8498883225b9f950a1e2c',
        'Cookie': 'HWWAFSESID=a9bfb1e1d8b31ddd03b; HWWAFSESTIME=1716101437115'
    }

    response = requests.request("POST", deepseek_url, headers=headers, data=payload)

    return response.text

dashscope.api_key="sk-1697d952454f4301baf0be60f48dae97"
def tongyiwx_call(prompt, save_path):
    rsp = dashscope.ImageSynthesis.call(model=dashscope.ImageSynthesis.Models.wanx_v1,
                              prompt=prompt,
                              n=1,
                              size='1024*1024')
    if rsp.status_code == HTTPStatus.OK:
        print(rsp.output)
        print(rsp.usage)
        # save file to current directory
        for result in rsp.output.results:
            with open(save_path, 'wb+') as f:
                f.write(requests.get(result.url).content)
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))
    return rsp.code


if __name__ == '__main__':
    with open('/Users/yinke/PycharmProjects/optimus/outputs.jpg', 'wb+') as f:
        f.write(requests.get(    'https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/82/20240521/1b61f1c0/a06a52a4-7996-4fa8-9aa5-c4eda6223b79-1.png?Expires=1716370634&OSSAccessKeyId=LTAI5tQZd8AEcZX6KZV4G8qL&Signature=GqWM9BdTDk%2FkL%2F9cL4%2FkU0sphF8%3D').content)
    # prompt_aug = deepseekv2("问出这个问题的是宁无邪，宁无邪很平静。关于第二点，为何有人没有中毒？他已经猜到原因，只是在看到自己的得力下属人。隋云站起来的时候，")
    # tongyiwx_call(prompt_aug, '/Users/yinke/PycharmProjects/optimus/outputs.jpg')
    # print(1)