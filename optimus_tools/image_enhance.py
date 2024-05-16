import re
from playwright.sync_api import Playwright, sync_playwright, expect
import os

def enhance_image_resolution_by_online_waifu2x(playwright: Playwright, image_path) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    page = context.new_page()
    page.goto("https://unlimited.waifu2x.net/")
    # page.locator("#file").click()
    page.locator("#file").set_input_files(image_path)
    page.locator("select[name=\"scale\"]").select_option("4")
    page.locator("select[name=\"tile_size\"]").select_option("256")
    page.get_by_role("button", name="Start").click()
    # 等待图片处理完成
    page.wait_for_selector("text=Download", timeout=200000)
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Download").click()
    download = download_info.value

    # 将下载后的文件名改为image_path中的原文件名
    file_name = re.findall(r'\/([^\/]+)\.jpg', image_path)[0]
    processed_file_path = os.path.join(os.path.dirname(image_path), file_name + '_waifu2x.jpg')
    os.rename(download.path(), processed_file_path)
    print('new_file_name:', processed_file_path)

    # ---------------------
    context.close()
    browser.close()
    return processed_file_path


def enhance_image_resolution(image_path):
    with sync_playwright() as playwright:
        enhance_image_resolution_by_online_waifu2x(playwright, image_path)


if __name__ == '__main__':
    image_path = '/Users/zzy/Documents/AI图片素材/images/3.jpg'
    processed_file_path = enhance_image_resolution(image_path)
    print(processed_file_path)
