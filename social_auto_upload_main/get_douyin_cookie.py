import asyncio
from pathlib import Path

from conf import BASE_DIR
from douyin_uploader.main import douyin_setup
import os
# os.environ['EDR_BLOCK_PATH'] = "D:\playwright_browser\chromium-1112\chrome-win\chrome.exe"

if __name__ == '__main__':
    account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
    cookie_setup = asyncio.run(douyin_setup(str(account_file), handle=True))
