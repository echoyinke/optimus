import asyncio
from pathlib import Path

from conf import BASE_DIR
from douyin_uploader.main import douyin_setup

def douyin_cookie_setup():
    account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
    cookie_setup = asyncio.run(douyin_setup(str(account_file), handle=True))


if __name__ == '__main__':
    douyin_cookie_setup()
