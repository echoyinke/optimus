import argparse
import json
import os
import logging
import time

import requests
import yaml
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